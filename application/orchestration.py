"""
应用层：Orchestration（编排协调）

职责：
- 管理智能体的生命周期（创建、销毁、状态监控）
- 负责任务的分解、分发与进度跟踪
- 协调多个智能体的工作流
- 通过消息网络向执行层下发任务，监听执行结果
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime
import uuid
import asyncio
import yaml

from infra import (
    Message, MessageType, MessagePriority,
    get_message_network, get_module_registry,
    ModuleType, ModuleStatus, ModuleInfo,
)
from memory import MemoryService, MemoryType, get_memory_service
from services import ExecutionAgent, create_agent, get_available_agent_types


@dataclass
class TaskPlan:
    """
    任务计划
    
    任务分解后的执行计划
    """
    plan_id: str
    task_id: str
    task_name: str
    task_description: str
    
    # 子任务分解
    sub_tasks: List[Dict[str, Any]] = field(default_factory=list)
    
    # 执行状态
    status: str = "pending"  # pending, running, completed, failed
    current_step: int = 0
    
    # 结果
    results: List[Dict[str, Any]] = field(default_factory=list)
    
    # 元数据
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "task_id": self.task_id,
            "task_name": self.task_name,
            "status": self.status,
            "sub_tasks": self.sub_tasks,
            "current_step": self.current_step,
            "results": self.results,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


@dataclass
class SOP:
    """
    标准操作程序（SOP）
    
    从 Markdown 文件加载
    """
    sop_id: str
    name: str
    description: str
    
    # 步骤定义
    steps: List[Dict[str, Any]] = field(default_factory=list)
    
    # 条件分支
    conditions: List[Dict[str, Any]] = field(default_factory=list)
    
    # 元数据
    version: str = "1.0"
    tags: List[str] = field(default_factory=list)
    
    @classmethod
    def from_markdown(cls, markdown_path: str) -> "SOP":
        """从 Markdown 文件加载 SOP"""
        with open(markdown_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # 解析 YAML frontmatter
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                yaml_content = parts[1]
                data = yaml.safe_load(yaml_content) or {}
                
                return cls(
                    sop_id=data.get("sop_id", str(uuid.uuid4())[:8]),
                    name=data.get("name", "Unnamed SOP"),
                    description=data.get("description", ""),
                    steps=data.get("steps", []),
                    conditions=data.get("conditions", []),
                    version=data.get("version", "1.0"),
                    tags=data.get("tags", []),
                )
        
        return cls(
            sop_id=str(uuid.uuid4())[:8],
            name="Unnamed SOP",
            description="No description",
        )


class OrchestrationService:
    """
    编排协调服务
    
    核心职责：
    1. 任务分解与规划
    2. 智能体调度
    3. 进度跟踪
    4. 异常处理
    """
    
    def __init__(
        self,
        orchestrator_id: Optional[str] = None,
        memory_service: Optional[MemoryService] = None,
    ):
        self.orchestrator_id = orchestrator_id or f"orchestrator_{uuid.uuid4().hex[:8]}"
        self.memory = memory_service or get_memory_service()
        self.network = get_message_network()
        
        # 管理的智能体
        self.managed_agents: Dict[str, ExecutionAgent] = {}
        
        # 任务计划
        self.task_plans: Dict[str, TaskPlan] = {}
        
        # 加载的 SOP
        self.sops: Dict[str, SOP] = {}
        
        # 运行状态
        self._running = False
        self._task_queue: asyncio.Queue = asyncio.Queue()
        
        # 注册到模块注册表
        self._register_self()
        
        # 注册消息处理器
        self._register_message_handlers()
    
    def _register_self(self) -> None:
        """注册自己到模块注册表"""
        registry = get_module_registry()
        
        module_info = ModuleInfo(
            module_id=self.orchestrator_id,
            module_type=ModuleType.ORCHESTRATION,
            name="Orchestration Service",
            description="Task orchestration and agent coordination",
            status=ModuleStatus.READY,
            capabilities=["task_decomposition", "agent_scheduling", "progress_tracking"],
        )
        
        registry.register(module_info)
    
    def _register_message_handlers(self) -> None:
        """注册消息处理器"""
        self.network.register_handler(
            MessageType.MCP_START_TASK,
            self._handle_start_task,
        )
        
        self.network.register_handler(
            MessageType.MCP_STOP_TASK,
            self._handle_stop_task,
        )
        
        self.network.register_handler(
            MessageType.EVENT_TASK_COMPLETED,
            self._handle_task_completed,
        )
    
    # ========== 智能体管理 ==========
    
    def create_agent(self, agent_type: str, agent_id: Optional[str] = None) -> ExecutionAgent:
        """创建并注册执行智能体"""
        agent = create_agent(agent_type, agent_id)
        agent.register()
        self.managed_agents[agent.agent_id] = agent
        return agent
    
    def destroy_agent(self, agent_id: str) -> bool:
        """销毁执行智能体"""
        agent = self.managed_agents.pop(agent_id, None)
        if agent:
            agent.unregister()
            return True
        return False
    
    def get_agent(self, agent_id: str) -> Optional[ExecutionAgent]:
        """获取智能体"""
        return self.managed_agents.get(agent_id)
    
    def list_agents(self) -> List[Dict[str, Any]]:
        """列出所有管理的智能体"""
        return [agent.get_status() for agent in self.managed_agents.values()]
    
    # ========== SOP 管理 ==========
    
    def load_sop(self, sop_path: str) -> SOP:
        """加载 SOP 文件"""
        sop = SOP.from_markdown(sop_path)
        self.sops[sop.sop_id] = sop
        return sop
    
    def get_sop(self, sop_id: str) -> Optional[SOP]:
        """获取 SOP"""
        return self.sops.get(sop_id)
    
    # ========== 任务编排 ==========
    
    async def submit_task(self, task: Dict[str, Any]) -> str:
        """
        提交任务
        
        返回任务 ID
        """
        task_id = task.get("task_id", str(uuid.uuid4())[:8])
        
        # 创建任务计划
        plan = await self._decompose_task(task)
        self.task_plans[task_id] = plan
        
        # 放入任务队列
        await self._task_queue.put(plan)
        
        # 存储到记忆
        self.memory.store_task_state(
            task_id=task_id,
            state=plan.to_dict(),
            created_by=self.orchestrator_id,
        )
        
        return task_id
    
    async def _decompose_task(self, task: Dict[str, Any]) -> TaskPlan:
        """
        任务分解
        
        将高层任务分解为可执行的子任务
        """
        task_id = task.get("task_id", str(uuid.uuid4())[:8])
        
        plan = TaskPlan(
            plan_id=str(uuid.uuid4())[:8],
            task_id=task_id,
            task_name=task.get("name", "Unnamed Task"),
            task_description=task.get("description", ""),
        )
        
        # 检查是否指定了 SOP
        sop_id = task.get("sop_id")
        if sop_id and sop_id in self.sops:
            sop = self.sops[sop_id]
            plan.sub_tasks = sop.steps
        else:
            # 默认分解：单步骤任务
            plan.sub_tasks = [
                {
                    "step_id": "step_1",
                    "name": task.get("name", "Task"),
                    "action": task.get("action", "execute"),
                    "params": task.get("params", {}),
                    "agent_type": task.get("agent_type", "file_operation"),
                }
            ]
        
        return plan
    
    async def execute_plan(self, plan: TaskPlan) -> Dict[str, Any]:
        """
        执行任务计划
        
        按步骤执行子任务
        """
        plan.status = "running"
        plan.started_at = datetime.now()
        
        results = []
        
        for i, sub_task in enumerate(plan.sub_tasks):
            plan.current_step = i
            
            # 选择智能体
            agent_type = sub_task.get("agent_type", "file_operation")
            agent = self._select_agent(agent_type)
            
            if not agent:
                results.append({
                    "step_id": sub_task.get("step_id"),
                    "status": "failed",
                    "error": f"No available agent for type: {agent_type}",
                })
                continue
            
            # 发送任务请求
            message = Message.task_request(
                source=self.orchestrator_id,
                target=agent.agent_id,
                task=sub_task,
            )
            
            try:
                # 等待响应（带超时）
                response = await self.network.send_and_wait(message, timeout=60.0)
                
                if response:
                    result = response.payload.get("result", {})
                    results.append({
                        "step_id": sub_task.get("step_id"),
                        "status": result.get("status", "unknown"),
                        "data": result.get("data", {}),
                    })
                else:
                    results.append({
                        "step_id": sub_task.get("step_id"),
                        "status": "failed",
                        "error": "Timeout waiting for response",
                    })
                    
            except Exception as e:
                results.append({
                    "step_id": sub_task.get("step_id"),
                    "status": "failed",
                    "error": str(e),
                })
        
        plan.results = results
        plan.completed_at = datetime.now()
        
        # 判断整体状态
        failed_count = sum(1 for r in results if r.get("status") == "failed")
        plan.status = "failed" if failed_count > 0 else "completed"
        
        # 更新记忆
        self.memory.store_task_state(
            task_id=plan.task_id,
            state=plan.to_dict(),
            created_by=self.orchestrator_id,
        )
        
        # 发布完成事件
        event = Message.event_task_completed(
            source=self.orchestrator_id,
            task_id=plan.task_id,
            result={"status": plan.status, "results": results},
        )
        await self.network.publish(event)
        
        return plan.to_dict()
    
    def _select_agent(self, agent_type: str) -> Optional[ExecutionAgent]:
        """选择合适的智能体"""
        # 优先从管理的智能体中选择
        for agent in self.managed_agents.values():
            if agent.agent_type == agent_type and agent.status == ModuleStatus.READY:
                return agent
        
        # 如果没有，创建一个新的
        try:
            return self.create_agent(agent_type)
        except Exception:
            return None
    
    # ========== 消息处理 ==========
    
    async def _handle_start_task(self, message: Message) -> None:
        """处理启动任务消息"""
        task = message.payload.get("task", {})
        task_id = await self.submit_task(task)
        
        # 响应
        response = Message(
            message_type=MessageType.MCP_STATUS_RESPONSE,
            source=self.orchestrator_id,
            target=message.source,
            payload={"task_id": task_id, "status": "submitted"},
            correlation_id=message.message_id,
        )
        await self.network.respond(message, response)
    
    async def _handle_stop_task(self, message: Message) -> None:
        """处理停止任务消息"""
        task_id = message.payload.get("task_id")
        
        if task_id and task_id in self.task_plans:
            plan = self.task_plans[task_id]
            plan.status = "cancelled"
            plan.completed_at = datetime.now()
        
        response = Message(
            message_type=MessageType.MCP_STATUS_RESPONSE,
            source=self.orchestrator_id,
            target=message.source,
            payload={"task_id": task_id, "status": "stopped"},
            correlation_id=message.message_id,
        )
        await self.network.respond(message, response)
    
    async def _handle_task_completed(self, message: Message) -> None:
        """处理任务完成事件"""
        # 可以用于触发后续任务或报告生成
        pass
    
    # ========== 运行循环 ==========
    
    async def start(self) -> None:
        """启动编排服务"""
        self._running = True
        
        while self._running:
            try:
                # 获取任务计划
                try:
                    plan = await asyncio.wait_for(self._task_queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    continue
                
                # 执行计划
                await self.execute_plan(plan)
                
            except Exception as e:
                print(f"Orchestration error: {e}")
    
    def stop(self) -> None:
        """停止编排服务"""
        self._running = False
    
    # ========== 状态查询 ==========
    
    def get_status(self) -> Dict[str, Any]:
        """获取编排服务状态"""
        return {
            "orchestrator_id": self.orchestrator_id,
            "managed_agents": len(self.managed_agents),
            "active_plans": len([p for p in self.task_plans.values() if p.status == "running"]),
            "completed_plans": len([p for p in self.task_plans.values() if p.status == "completed"]),
            "sops_loaded": len(self.sops),
        }
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务状态"""
        plan = self.task_plans.get(task_id)
        if plan:
            return plan.to_dict()
        
        # 从记忆中获取
        return self.memory.get_task_state(task_id)
