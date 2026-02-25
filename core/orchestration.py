"""
编排技能（Orchestration Skill）

职责：
- 维护 Task / Step 状态
- 判断 Step 是否满足完成条件
- 决定是否推进到下一个 Step
- 注册 / 等待信号
- 记录进度

核心原则：
- 不执行具体工作，只管理状态
- 上下文仅限于状态数据，不累积
- 可被审计、被打断、被替换
"""
from typing import Any, Dict, List, Optional, Protocol
from dataclasses import dataclass
from datetime import datetime

from .task_state import (
    Task, Step, TaskGraph, TaskState, StepState,
    Signal, CompletionCondition
)


class SkillRegistry(Protocol):
    """技能注册表接口"""
    def get_skill(self, name: str): ...
    def execute_skill(self, name: str, **inputs) -> str: ...


@dataclass
class OrchestrationContext:
    """
    编排上下文：仅包含状态数据，不累积
    
    这是传递给 LLM 的有限上下文：
    - 当前任务状态
    - 当前步骤信息
    - 不历史累积
    """
    task_id: str
    task_name: str
    task_state: str
    
    current_step_id: Optional[str]
    current_step_name: Optional[str]
    current_step_inputs: Dict[str, Any]
    
    # 仅包含必要信息，不累积历史
    pending_step_count: int
    completed_step_count: int
    
    # 阻塞信号（如有）
    blocking_signal: Optional[str] = None
    
    def to_prompt(self) -> str:
        """转换为提示词"""
        lines = [
            f"Task: {self.task_name} (ID: {self.task_id})",
            f"State: {self.task_state}",
            f"Progress: {self.completed_step_count}/{self.completed_step_count + self.pending_step_count} steps",
        ]
        
        if self.current_step_id:
            lines.extend([
                f"\nCurrent Step: {self.current_step_name} (ID: {self.current_step_id})",
                f"Inputs: {self.current_step_inputs}",
            ])
        
        if self.blocking_signal:
            lines.append(f"\n⏸ Blocked: Waiting for signal '{self.blocking_signal}'")
        
        return "\n".join(lines)


class OrchestrationSkill:
    """
    编排技能：管理任务生命周期
    
    这是 Agent 的"自我管理层"核心组件
    """
    
    def __init__(self, skill_registry: Optional[SkillRegistry] = None):
        self.skill_registry = skill_registry
        self._task_graph: Optional[TaskGraph] = None
    
    def bind_task_graph(self, task_graph: TaskGraph) -> None:
        """绑定任务状态图"""
        self._task_graph = task_graph
    
    # ========== 任务生命周期管理 ==========
    
    def create_task(
        self,
        name: str,
        description: str,
        steps: Optional[List[Step]] = None,
        completion_condition: CompletionCondition = CompletionCondition.ALL_STEPS,
        completion_condition_params: Optional[Dict[str, Any]] = None,
        parent_task_id: Optional[str] = None,
    ) -> Task:
        """
        创建新任务
        
        这是 CREATE 阶段的核心操作
        """
        task = Task(
            task_id=f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._task_graph.tasks)}",
            name=name,
            description=description,
            completion_condition=completion_condition,
            completion_condition_params=completion_condition_params or {},
            parent_task_id=parent_task_id,
        )
        
        if steps:
            task.add_steps(steps)
        
        self._task_graph.add_task(task)
        
        # 如果有父任务，建立关联
        if parent_task_id:
            parent = self._task_graph.get_task(parent_task_id)
            if parent:
                parent.sub_tasks.append(task.task_id)
        
        return task
    
    def start_task(self, task_id: str) -> bool:
        """启动任务"""
        task = self._task_graph.get_task(task_id)
        if not task:
            return False
        
        if task.state == TaskState.PENDING:
            task.mark_running()
            return True
        return False
    
    def complete_task(self, task_id: str) -> bool:
        """完成任务"""
        task = self._task_graph.get_task(task_id)
        if not task:
            return False
        
        task.mark_completed()
        return True
    
    def fail_task(self, task_id: str, error: str) -> bool:
        """标记任务失败"""
        task = self._task_graph.get_task(task_id)
        if not task:
            return False
        
        task.mark_failed(error)
        return True
    
    # ========== 步骤管理 ==========
    
    def get_next_step(self, task_id: str) -> Optional[Step]:
        """
        获取下一个可执行的步骤
        
        这是推进任务的核心方法
        """
        task = self._task_graph.get_task(task_id)
        if not task:
            return None
        
        # 更新步骤就绪状态
        task._update_step_readiness()
        
        # 获取下一个就绪的步骤
        return task.get_next_ready_step()
    
    def start_step(self, task_id: str, step_id: str) -> bool:
        """启动步骤"""
        task = self._task_graph.get_task(task_id)
        if not task:
            return False
        
        step = task.get_step(step_id)
        if not step:
            return False
        
        if step.state in (StepState.READY, StepState.PENDING):
            step.mark_running()
            task.mark_running()
            return True
        return False
    
    def complete_step(
        self,
        task_id: str,
        step_id: str,
        result: str,
        outputs: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        完成步骤
        
        这是原子技能执行后的回调
        """
        task = self._task_graph.get_task(task_id)
        if not task:
            return False
        
        step = task.get_step(step_id)
        if not step:
            return False
        
        step.mark_completed(result)
        if outputs:
            step.outputs = outputs
        
        # 更新后续步骤的就绪状态
        task._update_step_readiness()
        
        # 检查任务是否完成
        task.check_completion()
        
        return True
    
    def fail_step(self, task_id: str, step_id: str, error: str) -> bool:
        """标记步骤失败"""
        task = self._task_graph.get_task(task_id)
        if not task:
            return False
        
        step = task.get_step(step_id)
        if not step:
            return False
        
        step.mark_failed(error)
        return True
    
    # ========== 信号管理 ==========
    
    def wait_for_signal(
        self,
        task_id: str,
        signal_name: str,
        as_completion_condition: bool = True,
    ) -> Signal:
        """
        等待信号
        
        任务会被阻塞，直到收到信号
        """
        task = self._task_graph.get_task(task_id)
        if not task:
            raise ValueError(f"Task not found: {task_id}")
        
        # 创建阻塞信号
        signal = Signal(name=signal_name, source=task_id)
        task.blocking_signals.append(signal)
        task.mark_blocked(signal_name)
        
        # 可选：设置为完成条件
        if as_completion_condition:
            task.completion_condition = CompletionCondition.SIGNAL_RECEIVED
            task.completion_condition_params = {"signal_name": signal_name}
        
        return signal
    
    def send_signal(self, task_id: str, signal: Signal) -> bool:
        """
        发送信号到任务
        
        这会唤醒被阻塞的任务
        """
        task = self._task_graph.get_task(task_id)
        if not task:
            return False
        
        task.send_signal(signal)
        return True
    
    # ========== 状态查询 ==========
    
    def get_orchestration_context(self, task_id: str) -> Optional[OrchestrationContext]:
        """
        获取编排上下文
        
        这是传递给 LLM 的有限上下文，不包含历史累积
        """
        task = self._task_graph.get_task(task_id)
        if not task:
            return None
        
        current_step = task.get_next_ready_step()
        
        return OrchestrationContext(
            task_id=task.task_id,
            task_name=task.name,
            task_state=task.state.value,
            current_step_id=current_step.step_id if current_step else None,
            current_step_name=current_step.name if current_step else None,
            current_step_inputs=current_step.inputs if current_step else {},
            pending_step_count=len(task.get_pending_steps()),
            completed_step_count=len(task.get_completed_steps()),
            blocking_signal=(
                task.blocking_signals[0].name
                if task.blocking_signals and task.state == TaskState.BLOCKED
                else None
            ),
        )
    
    def get_task_state_summary(self, task_id: str) -> Dict[str, Any]:
        """获取任务状态摘要（用于审计）"""
        task = self._task_graph.get_task(task_id)
        if not task:
            return {}
        
        return {
            "task_id": task.task_id,
            "name": task.name,
            "state": task.state.value,
            "total_steps": len(task.steps),
            "completed_steps": len(task.get_completed_steps()),
            "pending_steps": len(task.get_pending_steps()),
            "signals_received": len(task.received_signals),
            "blocking_signals": [s.name for s in task.blocking_signals],
        }
    
    def execute_step(self, task_id: str, step_id: str) -> Optional[str]:
        """
        执行步骤
        
        这是编排层与原子技能层的桥梁
        """
        task = self._task_graph.get_task(task_id)
        if not task:
            return None
        
        step = task.get_step(step_id)
        if not step:
            return None
        
        if not self.skill_registry:
            raise RuntimeError("Skill registry not configured")
        
        # 启动步骤
        self.start_step(task_id, step_id)
        
        # 执行原子技能
        try:
            result = self.skill_registry.execute_skill(
                name=step.skill_name,
                **step.inputs,
            )
            
            # 完成步骤
            self.complete_step(task_id, step_id, result)
            
            return result
            
        except Exception as e:
            self.fail_step(task_id, step_id, str(e))
            raise
    
    # ========== 进度推进 ==========
    
    def advance(self) -> Optional[tuple[str, Step]]:
        """
        推进任务
        
        返回 (task_id, step) 表示下一个要执行的步骤
        返回 None 表示没有可执行的步骤
        
        这是主循环调用的方法
        """
        if not self._task_graph:
            return None
        
        result = self._task_graph.get_next_step()
        if result:
            task, step = result
            return (task.task_id, step)
        
        return None
