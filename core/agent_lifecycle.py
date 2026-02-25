"""
Agent 生命周期管理

生命周期：CREATE → ONBOARD → EXECUTE

核心原则：
- Agent 不"自己发明工作"
- 所有 Task 来自入职文件或上级指派
- 没有 prompt 让 Agent"自由发挥"
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol
from datetime import datetime
import uuid

from .task_state import Task, Step, TaskGraph, Signal
from .orchestration import OrchestrationSkill, SkillRegistry
from .atomic_skill import AtomicSkill


class AgentState(Enum):
    """Agent 生命周期状态"""
    CREATING = "creating"     # 创建中
    ONBOARDING = "onboarding" # 入职中
    READY = "ready"           # 就绪，可执行
    EXECUTING = "executing"   # 执行中
    BLOCKED = "blocked"       # 被阻塞
    IDLE = "idle"             # 空闲（任务完成）
    OFFBOARDING = "offboarding"  # 离职中
    TERMINATED = "terminated"    # 已终止


class AgentRole(Enum):
    """
    Agent 角色定义
    
    角色差异 = Orchestration 复杂度 + Atomic Skill 范围
    """
    MANAGER = "manager"   # 多任务、多 Agent、依赖多，几乎不做具体执行
    EXPERT = "expert"     # 单大任务、强阶段性，系统级分析
    SENIOR = "senior"     # 单模块、弱生命周期，模块级分析
    JUNIOR = "junior"     # 无 Orchestration，极原子、强约束


@dataclass
class RoleDescription:
    """
    角色职责说明
    
    这是 ONBOARD 阶段的输入之一
    """
    role: AgentRole
    name: str
    description: str
    
    # Orchestration 特点
    max_concurrent_tasks: int       # 最大并发任务数
    supports_task_decomposition: bool  # 是否支持任务分解
    requires_explicit_steps: bool      # 是否需要显式步骤
    
    # Atomic Skill 特点
    allowed_skills: List[str]           # 允许使用的技能
    restricted_skills: List[str]        # 限制使用的技能
    
    # 约束
    max_context_steps: int              # 最大上下文步骤数
    requires_approval_for: List[str]    # 需要审批的操作


@dataclass
class OnboardingSpec:
    """
    入职规范
    
    这是 ONBOARD 阶段的核心输入
    """
    role_description: RoleDescription
    
    # SOP（标准操作程序）
    sop_steps: List[Dict[str, Any]]  # 标准步骤定义
    
    # Orchestration Spec
    task_templates: List[Dict[str, Any]]  # 任务模板
    step_templates: List[Dict[str, Any]]  # 步骤模板
    
    # 初始任务（如有）
    initial_tasks: List[Dict[str, Any]]


@dataclass
class AgentConfig:
    """Agent 配置"""
    agent_id: str = field(default_factory=lambda: f"agent_{uuid.uuid4().hex[:8]}")
    role: AgentRole = AgentRole.JUNIOR
    name: Optional[str] = None
    workspace: str = "./workspace"
    
    # LLM 配置
    llm_model: str = "anthropic/claude-sonnet-4-5-20250929"
    llm_api_key: Optional[str] = None
    
    # 技能注册表
    skill_registry: Optional[SkillRegistry] = None


class AgentLifecycleManager:
    """
    Agent 生命周期管理器
    
    负责：
    - CREATE: 创建 Agent 实例
    - ONBOARD: 执行入职流程，构建任务状态图
    - EXECUTE: 管理执行循环
    - OFFBOARD: 清理和终止
    """
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.agent_id = config.agent_id
        self.role = config.role
        
        self.state = AgentState.CREATING
        self.created_at = datetime.now()
        
        # 核心组件
        self.task_graph: Optional[TaskGraph] = None
        self.orchestration: Optional[OrchestrationSkill] = None
        self.skill_registry: SkillRegistry = config.skill_registry or SkillRegistry()
        
        # 元数据
        self.current_task_id: Optional[str] = None
        self.completed_tasks: int = 0
        self.failed_tasks: int = 0
        
        # 角色描述（ONBOARD 时设置）
        self.role_description: Optional[RoleDescription] = None
    
    # ========== CREATE 阶段 ==========
    
    @classmethod
    def create(cls, config: AgentConfig) -> "AgentLifecycleManager":
        """
        创建新 Agent
        
        分配 Agent ID、Role，装载可用 Skill 清单
        """
        manager = cls(config)
        manager.state = AgentState.CREATING
        
        # 初始化任务图
        manager.task_graph = TaskGraph(agent_id=config.agent_id)
        
        # 初始化编排技能
        manager.orchestration = OrchestrationSkill(manager.skill_registry)
        manager.orchestration.bind_task_graph(manager.task_graph)
        
        # 根据角色配置可用技能
        manager._setup_role_skills()
        
        return manager
    
    def _setup_role_skills(self) -> None:
        """根据角色配置可用技能"""
        # 默认注册所有内置技能
        from .atomic_skill import create_default_registry
        
        if not self.skill_registry.list_skills():
            registry = create_default_registry()
            for skill_name in registry.list_skills():
                skill = registry.get_skill(skill_name)
                self.skill_registry.register(skill)
        
        # 根据角色限制技能
        if self.role_description:
            for restricted in self.role_description.restricted_skills:
                # 移除限制技能（这里只是标记，实际执行时检查）
                pass
    
    # ========== ONBOARD 阶段 ==========
    
    def onboard(self, spec: OnboardingSpec) -> bool:
        """
        执行入职流程
        
        输入：
        - 入职职责说明（Role Description）
        - 入职文件（SOP / Orchestration Spec）
        
        输出：
        - Agent 专属 Task State Graph
        """
        if self.state != AgentState.CREATING:
            return False
        
        self.state = AgentState.ONBOARDING
        self.role_description = spec.role_description
        
        # 1. 构建显式任务状态机
        self._build_task_state_machine(spec)
        
        # 2. 初始化 Task / Step 列表
        self._initialize_tasks(spec)
        
        # 3. 标注每个 Step 的完成条件与信号
        self._annotate_completion_conditions(spec)
        
        self.state = AgentState.READY
        return True
    
    def _build_task_state_machine(self, spec: OnboardingSpec) -> None:
        """构建任务状态机"""
        # 根据角色设置任务状态机特点
        if self.role == AgentRole.MANAGER:
            # Manager: 多任务、多依赖
            self.task_graph = TaskGraph(agent_id=self.agent_id)
            self.orchestration.bind_task_graph(self.task_graph)
        
        elif self.role == AgentRole.EXPERT:
            # Expert: 单大任务、强阶段性
            pass
        
        elif self.role == AgentRole.SENIOR:
            # Senior: 单模块、弱生命周期
            pass
        
        elif self.role == AgentRole.JUNIOR:
            # Junior: 无 Orchestration，直接执行
            pass
    
    def _initialize_tasks(self, spec: OnboardingSpec) -> None:
        """初始化任务列表"""
        # 从模板创建任务
        for task_template in spec.task_templates:
            self._create_task_from_template(task_template)
        
        # 添加初始任务
        for initial_task in spec.initial_tasks:
            self._create_task_from_template(initial_task)
    
    def _create_task_from_template(self, template: Dict[str, Any]) -> Task:
        """从模板创建任务"""
        from .task_state import CompletionCondition
        
        # 解析模板
        name = template.get("name", "Unnamed Task")
        description = template.get("description", "")
        
        # 完成条件
        completion_type = template.get("completion_condition", "all_steps")
        if completion_type == "all_steps":
            completion = CompletionCondition.ALL_STEPS
        elif completion_type == "specific_step":
            completion = CompletionCondition.SPECIFIC_STEP
        elif completion_type == "signal":
            completion = CompletionCondition.SIGNAL_RECEIVED
        else:
            completion = CompletionCondition.ALL_STEPS
        
        # 创建任务
        task = self.orchestration.create_task(
            name=name,
            description=description,
            completion_condition=completion,
            completion_condition_params=template.get("completion_params", {}),
        )
        
        # 添加步骤
        for step_template in template.get("steps", []):
            step = self._create_step_from_template(step_template)
            task.add_step(step)
        
        return task
    
    def _create_step_from_template(self, template: Dict[str, Any]) -> Step:
        """从模板创建步骤"""
        return Step(
            step_id=template.get("step_id", f"step_{uuid.uuid4().hex[:8]}"),
            name=template.get("name", "Unnamed Step"),
            description=template.get("description", ""),
            skill_name=template.get("skill", "UnknownSkill"),
            inputs=template.get("inputs", {}),
            dependencies=set(template.get("dependencies", [])),
        )
    
    def _annotate_completion_conditions(self, spec: OnboardingSpec) -> None:
        """标注完成条件"""
        # 为每个 Step 标注完成条件
        for task in self.task_graph.tasks.values():
            for step in task.steps:
                # 从模板或默认值获取完成条件
                step.completion_condition = f"result is not empty and not error"
    
    # ========== EXECUTE 阶段 ==========
    
    def start_execution(self) -> bool:
        """开始执行"""
        if self.state not in (AgentState.READY, AgentState.IDLE):
            return False
        
        self.state = AgentState.EXECUTING
        return True
    
    def execute_step(self) -> Optional[str]:
        """
        执行单步
        
        这是执行循环的核心：
        1. 获取下一个可执行的 Step
        2. 执行对应的 Atomic Skill
        3. 更新状态
        4. 返回结果
        
        返回：
            str: 执行结果，或 None（无可用步骤）
        """
        if self.state != AgentState.EXECUTING:
            return None
        
        # 获取下一个可执行的步骤
        next_item = self.orchestration.advance()
        if not next_item:
            # 没有可执行的步骤，进入空闲状态
            self.state = AgentState.IDLE
            return None
        
        task_id, step = next_item
        self.current_task_id = task_id
        
        # 检查技能是否在允许列表中
        if self.role_description:
            allowed = self.role_description.allowed_skills
            if allowed and step.skill_name not in allowed:
                return f"错误：技能 '{step.skill_name}' 不在角色允许列表中"
        
        # 执行原子技能
        try:
            result = self.skill_registry.execute_skill(
                name=step.skill_name,
                **step.inputs,
            )
            
            # 更新步骤状态
            self.orchestration.complete_step(task_id, step.step_id, result)
            
            # 检查任务是否完成
            task = self.task_graph.get_task(task_id)
            if task and task.state.value == "completed":
                self.completed_tasks += 1
            
            return result
            
        except Exception as e:
            self.orchestration.fail_step(task_id, step.step_id, str(e))
            self.failed_tasks += 1
            raise
    
    def run_loop(self, max_steps: Optional[int] = None) -> List[str]:
        """
        运行执行循环
        
        持续执行直到：
        - 没有可执行的步骤
        - 达到最大步数
        - 被外部中断
        
        返回：
            执行结果列表
        """
        if not self.start_execution():
            return []
        
        results = []
        steps_executed = 0
        
        while self.state == AgentState.EXECUTING:
            if max_steps and steps_executed >= max_steps:
                break
            
            try:
                result = self.execute_step()
                if result:
                    results.append(result)
                    steps_executed += 1
                else:
                    break  # 没有可执行的步骤
                    
            except Exception as e:
                results.append(f"错误：{str(e)}")
                # 继续执行其他步骤
        
        return results
    
    def send_signal(self, signal: Signal) -> bool:
        """
        发送信号到 Agent
        
        信号可以：
        - 唤醒被阻塞的任务
        - 触发新的任务
        - 通知外部事件
        """
        # 查找阻塞中的任务
        for task in self.task_graph.tasks.values():
            for blocking_signal in task.blocking_signals:
                if blocking_signal.name == signal.name:
                    task.send_signal(signal)
                    
                    # 如果 Agent 是空闲状态，恢复执行
                    if self.state == AgentState.IDLE:
                        self.state = AgentState.EXECUTING
                    
                    return True
        
        return False
    
    # ========== 状态查询 ==========
    
    def get_status(self) -> Dict[str, Any]:
        """获取 Agent 状态"""
        return {
            "agent_id": self.agent_id,
            "name": self.config.name or self.agent_id,
            "role": self.role.value,
            "state": self.state.value,
            "current_task": self.current_task_id,
            "completed_tasks": self.completed_tasks,
            "failed_tasks": self.failed_tasks,
            "task_graph": self.task_graph.to_dict() if self.task_graph else None,
        }
    
    def get_current_context(self) -> Optional[str]:
        """
        获取当前执行上下文
        
        这是传递给 LLM 的有限上下文：
        - 仅包含当前任务/步骤信息
        - 不累积历史
        """
        if not self.current_task_id:
            return None
        
        ctx = self.orchestration.get_orchestration_context(self.current_task_id)
        if ctx:
            return ctx.to_prompt()
        
        return None
    
    # ========== OFFBOARD 阶段 ==========
    
    def offboard(self) -> Dict[str, Any]:
        """
        离职流程
        
        返回：
            交接数据（任务状态、进度等）
        """
        self.state = AgentState.OFFBOARDING
        
        # 收集交接数据
        handoff_data = {
            "agent_id": self.agent_id,
            "offboarded_at": datetime.now().isoformat(),
            "task_graph": self.task_graph.to_dict() if self.task_graph else None,
            "completed_tasks": self.completed_tasks,
            "failed_tasks": self.failed_tasks,
            "pending_signals": [
                {"task_id": tid, "signal": s.name}
                for tid, task in (self.task_graph.tasks.items() if self.task_graph else {})
                for s in task.blocking_signals
            ],
        }
        
        self.state = AgentState.TERMINATED
        return handoff_data
    
    def terminate(self) -> None:
        """终止 Agent"""
        self.state = AgentState.TERMINATED
        self.task_graph = None
        self.orchestration = None


# ========== 便捷函数 ==========

def create_agent(
    role: AgentRole = AgentRole.JUNIOR,
    name: Optional[str] = None,
    workspace: str = "./workspace",
    llm_api_key: Optional[str] = None,
) -> AgentLifecycleManager:
    """
    创建 Agent 的便捷函数
    
    示例：
        agent = create_agent(role=AgentRole.SENIOR, name="代码审查员")
    """
    config = AgentConfig(
        role=role,
        name=name,
        workspace=workspace,
        llm_api_key=llm_api_key,
    )
    
    return AgentLifecycleManager.create(config)
