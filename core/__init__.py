"""
Core 包：显式任务状态机 + 任务清单驱动 + 原子执行技能
"""
from .task_state import (
    TaskState,
    StepState,
    CompletionCondition,
    Signal,
    Step,
    Task,
    TaskGraph,
)

from .orchestration import (
    OrchestrationSkill,
    OrchestrationContext,
)

from .atomic_skill import (
    AtomicSkill,
    SkillRegistry,
    SkillSpec,
    ReadFileSkill,
    WriteFileSkill,
    ListFilesSkill,
    SearchTextSkill,
    ExecuteCommandSkill,
    AnalyzeCodeSkill,
    create_default_registry,
)

from .agent_lifecycle import (
    AgentState,
    AgentRole,
    AgentConfig,
    AgentLifecycleManager,
    create_agent,
)

from .roles import (
    get_manager_role,
    get_expert_role,
    get_senior_role,
    get_junior_role,
    create_onboarding_spec,
)

__all__ = [
    # Task State
    "TaskState",
    "StepState",
    "CompletionCondition",
    "Signal",
    "Step",
    "Task",
    "TaskGraph",
    
    # Orchestration
    "OrchestrationSkill",
    "OrchestrationContext",
    
    # Atomic Skill
    "AtomicSkill",
    "SkillRegistry",
    "SkillSpec",
    "ReadFileSkill",
    "WriteFileSkill",
    "ListFilesSkill",
    "SearchTextSkill",
    "ExecuteCommandSkill",
    "AnalyzeCodeSkill",
    "create_default_registry",
    
    # Agent Lifecycle
    "AgentState",
    "AgentRole",
    "AgentConfig",
    "AgentLifecycleManager",
    "create_agent",
    
    # Roles
    "get_manager_role",
    "get_expert_role",
    "get_senior_role",
    "get_junior_role",
    "create_onboarding_spec",
]
