"""
Orchestration 模块

Agent 创建和编排启动流程
"""
from .jd import (
    JobDescription,
    JDManager,
    get_jd_manager,
)

from .resource_manager import (
    Resource,
    ResourceBundle,
    ResourceManager,
)

from .agent_lifecycle import (
    AgentSpec,
    AgentOnboardingResult,
    DutySkillManager,
    OrchestrationSkillManager,
    AgentCreator,
    get_agent_creator,
)

__all__ = [
    # JD
    "JobDescription",
    "JDManager",
    "get_jd_manager",
    
    # Resource
    "Resource",
    "ResourceBundle",
    "ResourceManager",
    
    # Agent Lifecycle
    "AgentSpec",
    "AgentOnboardingResult",
    "DutySkillManager",
    "OrchestrationSkillManager",
    "AgentCreator",
    "get_agent_creator",
]
