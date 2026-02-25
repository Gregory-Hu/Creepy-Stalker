"""
任务状态机核心模块

显式任务状态机是整个架构的核心：
- Task: 顶层任务，有明确的生命周期
- Step: 任务内的步骤，按顺序或依赖关系执行
- 状态全部显式存储，不依赖 LLM 上下文记忆
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from datetime import datetime
import uuid


class TaskState(Enum):
    """任务生命周期状态"""
    PENDING = "pending"       # 等待开始
    RUNNING = "running"       # 执行中
    BLOCKED = "blocked"       # 被阻塞（等待信号）
    COMPLETED = "completed"   # 已完成
    FAILED = "failed"         # 失败
    CANCELLED = "cancelled"   # 已取消


class StepState(Enum):
    """步骤状态"""
    PENDING = "pending"       # 等待执行
    READY = "ready"           # 前置条件满足，可执行
    RUNNING = "running"       # 执行中
    COMPLETED = "completed"   # 已完成
    FAILED = "failed"         # 失败
    SKIPPED = "skipped"       # 已跳过


class CompletionCondition(Enum):
    """完成条件类型"""
    ALL_STEPS = "all_steps"           # 所有步骤完成
    SPECIFIC_STEP = "specific_step"   # 特定步骤完成
    SIGNAL_RECEIVED = "signal"        # 收到特定信号
    CUSTOM = "custom"                 # 自定义条件


@dataclass
class Signal:
    """
    信号：用于跨任务/跨 Agent 通信
    
    信号驱动持续化的核心：
    - 任务可以被信号阻塞
    - 收到信号后继续执行
    - 信号可以被审计、追踪
    """
    name: str
    source: str              # 信号来源（Agent ID 或系统）
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    signal_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    
    def __str__(self) -> str:
        return f"Signal({self.name}, from={self.source})"


@dataclass
class Step:
    """
    原子执行单元
    
    一个 Step 必须满足：
    - 输入明确
    - 输出明确
    - 无长期上下文
    - 无跨 step 状态
    """
    step_id: str
    name: str
    description: str
    skill_name: str              # 使用的 Atomic Skill
    inputs: Dict[str, Any] = field(default_factory=dict)
    outputs: Dict[str, Any] = field(default_factory=dict)
    
    state: StepState = StepState.PENDING
    dependencies: Set[str] = field(default_factory=set)  # 依赖的 step_id
    
    # 完成条件
    completion_condition: Optional[str] = None  # 可选，覆盖默认条件
    
    # 执行结果
    result: Optional[str] = None
    error: Optional[str] = None
    
    # 元数据
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    def mark_ready(self) -> None:
        """标记为可执行（前置依赖已满足）"""
        if self.state == StepState.PENDING:
            self.state = StepState.READY
    
    def mark_running(self) -> None:
        """标记为执行中"""
        if self.state in (StepState.READY, StepState.PENDING):
            self.state = StepState.RUNNING
            self.started_at = datetime.now()
    
    def mark_completed(self, result: str) -> None:
        """标记为已完成"""
        self.state = StepState.COMPLETED
        self.result = result
        self.completed_at = datetime.now()
    
    def mark_failed(self, error: str) -> None:
        """标记为失败"""
        self.state = StepState.FAILED
        self.error = error
        self.completed_at = datetime.now()
    
    def can_execute(self) -> bool:
        """检查是否可以执行（所有依赖已完成）"""
        if self.state not in (StepState.PENDING, StepState.READY):
            return False
        return self.state == StepState.READY
    
    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典（用于审计/持久化）"""
        return {
            "step_id": self.step_id,
            "name": self.name,
            "state": self.state.value,
            "skill_name": self.skill_name,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "dependencies": list(self.dependencies),
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


@dataclass
class Task:
    """
    顶层任务：包含多个 Step
    
    Task 是 Orchestration 的基本单位：
    - 有明确的生命周期
    - 有完成条件
    - 可以被信号阻塞
    """
    task_id: str
    name: str
    description: str
    
    state: TaskState = TaskState.PENDING
    steps: List[Step] = field(default_factory=list)
    
    # 完成条件
    completion_condition: CompletionCondition = CompletionCondition.ALL_STEPS
    completion_condition_params: Dict[str, Any] = field(default_factory=dict)
    
    # 信号相关
    blocking_signals: List[Signal] = field(default_factory=list)  # 阻塞中的信号
    received_signals: List[Signal] = field(default_factory=list)  # 已收到的信号
    
    # 元数据
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # 父任务（用于任务分解）
    parent_task_id: Optional[str] = None
    sub_tasks: List[str] = field(default_factory=list)  # 子任务 ID
    
    def add_step(self, step: Step) -> None:
        """添加步骤"""
        self.steps.append(step)
        self._update_step_readiness()
    
    def add_steps(self, steps: List[Step]) -> None:
        """批量添加步骤"""
        for step in steps:
            self.steps.append(step)
        self._update_step_readiness()
    
    def get_step(self, step_id: str) -> Optional[Step]:
        """获取步骤"""
        for step in self.steps:
            if step.step_id == step_id:
                return step
        return None
    
    def get_next_ready_step(self) -> Optional[Step]:
        """获取下一个可执行的步骤"""
        for step in self.steps:
            if step.state == StepState.READY:
                return step
        return None
    
    def get_pending_steps(self) -> List[Step]:
        """获取所有待执行的步骤"""
        return [s for s in self.steps if s.state in (StepState.PENDING, StepState.READY)]
    
    def get_completed_steps(self) -> List[Step]:
        """获取已完成的步骤"""
        return [s for s in self.steps if s.state == StepState.COMPLETED]
    
    def _update_step_readiness(self) -> None:
        """更新所有步骤的就绪状态"""
        completed_step_ids = {
            s.step_id for s in self.steps if s.state == StepState.COMPLETED
        }
        
        for step in self.steps:
            if step.state == StepState.PENDING:
                # 检查所有依赖是否已完成
                if step.dependencies.issubset(completed_step_ids):
                    step.mark_ready()
    
    def check_completion(self) -> bool:
        """检查任务是否完成"""
        if self.state == TaskState.COMPLETED:
            return True
        
        if self.completion_condition == CompletionCondition.ALL_STEPS:
            all_completed = all(
                s.state in (StepState.COMPLETED, StepState.SKIPPED)
                for s in self.steps
            )
            if all_completed:
                self.state = TaskState.COMPLETED
                self.completed_at = datetime.now()
                return True
        
        elif self.completion_condition == CompletionCondition.SPECIFIC_STEP:
            target_step_id = self.completion_condition_params.get("step_id")
            if target_step_id:
                step = self.get_step(target_step_id)
                if step and step.state == StepState.COMPLETED:
                    self.state = TaskState.COMPLETED
                    self.completed_at = datetime.now()
                    return True
        
        elif self.completion_condition == CompletionCondition.SIGNAL_RECEIVED:
            expected_signal = self.completion_condition_params.get("signal_name")
            if expected_signal:
                for signal in self.received_signals:
                    if signal.name == expected_signal:
                        self.state = TaskState.COMPLETED
                        self.completed_at = datetime.now()
                        return True
        
        return False
    
    def send_signal(self, signal: Signal) -> None:
        """发送信号到任务"""
        self.received_signals.append(signal)
        self._update_step_readiness()
        
        # 检查是否因信号而完成
        if self.state == TaskState.BLOCKED:
            self.check_completion()
    
    def mark_running(self) -> None:
        """标记任务为执行中"""
        if self.state == TaskState.PENDING:
            self.state = TaskState.RUNNING
            self.started_at = datetime.now()
    
    def mark_blocked(self, signal_name: str) -> None:
        """标记任务为阻塞状态，等待信号"""
        self.state = TaskState.BLOCKED
        signal = Signal(name=signal_name, source=self.task_id)
        self.blocking_signals.append(signal)
    
    def mark_completed(self) -> None:
        """标记任务为已完成"""
        self.state = TaskState.COMPLETED
        self.completed_at = datetime.now()
    
    def mark_failed(self, error: str) -> None:
        """标记任务为失败"""
        self.state = TaskState.FAILED
        self.error = error
        self.completed_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典（用于审计/持久化）"""
        return {
            "task_id": self.task_id,
            "name": self.name,
            "state": self.state.value,
            "steps": [s.to_dict() for s in self.steps],
            "completion_condition": self.completion_condition.value,
            "completion_condition_params": self.completion_condition_params,
            "received_signals": [
                {"name": s.name, "source": s.source, "timestamp": s.timestamp.isoformat()}
                for s in self.received_signals
            ],
            "blocking_signals": [
                {"name": s.name, "source": s.source}
                for s in self.blocking_signals
            ],
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


@dataclass
class TaskGraph:
    """
    任务状态图：Agent 的完整任务视图
    
    这是 ONBOARD 阶段的输出：
    - 包含所有任务
    - 包含任务间依赖
    - 可被审计、被打断、被替换
    """
    agent_id: str
    tasks: Dict[str, Task] = field(default_factory=dict)
    
    # 任务依赖（跨任务）
    task_dependencies: Dict[str, Set[str]] = field(default_factory=dict)
    
    def add_task(self, task: Task) -> None:
        """添加任务"""
        self.tasks[task.task_id] = task
        if task.task_id not in self.task_dependencies:
            self.task_dependencies[task.task_id] = set()
    
    def add_dependency(self, task_id: str, depends_on: str) -> None:
        """添加任务依赖"""
        if task_id not in self.task_dependencies:
            self.task_dependencies[task_id] = set()
        self.task_dependencies[task_id].add(depends_on)
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """获取任务"""
        return self.tasks.get(task_id)
    
    def get_ready_tasks(self) -> List[Task]:
        """获取可执行的任务（依赖已满足）"""
        ready = []
        for task in self.tasks.values():
            if task.state != TaskState.PENDING:
                continue
            
            deps = self.task_dependencies.get(task.task_id, set())
            deps_satisfied = all(
                self.tasks.get(tid) and self.tasks[tid].state == TaskState.COMPLETED
                for tid in deps
            )
            if deps_satisfied:
                ready.append(task)
        
        return ready
    
    def get_next_step(self) -> Optional[tuple[Task, Step]]:
        """获取下一个可执行的 (任务，步骤) 对"""
        for task in self.get_ready_tasks():
            step = task.get_next_ready_step()
            if step:
                return (task, step)
        
        # 尝试从运行中的任务找
        for task in self.tasks.values():
            if task.state == TaskState.RUNNING:
                step = task.get_next_ready_step()
                if step:
                    return (task, step)
        
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典"""
        return {
            "agent_id": self.agent_id,
            "tasks": {tid: t.to_dict() for tid, t in self.tasks.items()},
            "task_dependencies": {
                tid: list(deps) for tid, deps in self.task_dependencies.items()
            },
        }
