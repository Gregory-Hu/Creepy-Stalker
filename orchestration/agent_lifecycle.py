"""
Orchestration Phase - Agent 创建和启动流程

核心流程:
1. Agent 创建：JD + Resource + Duty Skills → Agent 实例
2. Orchestration 启动：Orchestration Skills → 任务状态机
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime
import uuid
import os
import yaml

from .jd import JobDescription, JDManager, get_jd_manager
from .resource_manager import ResourceBundle, ResourceManager


@dataclass
class AgentSpec:
    """
    Agent 规格定义
    
    创建 Agent 时的完整输入
    """
    # 基本信息
    agent_id: str = field(default_factory=lambda: f"agent_{uuid.uuid4().hex[:8]}")
    name: str = ""
    
    # JD (Job Description)
    jd_id: str = ""
    jd: Optional[JobDescription] = None
    
    # Resource (资源)
    resource_bundle_id: str = ""
    resource_bundle: Optional[ResourceBundle] = None
    
    # Skills
    duty_skills: List[str] = field(default_factory=list)      # 职责技能
    orchestration_skills: List[str] = field(default_factory=list)  # 编排技能
    
    # 元数据
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "jd_id": self.jd_id,
            "resource_bundle_id": self.resource_bundle_id,
            "duty_skills": self.duty_skills,
            "orchestration_skills": self.orchestration_skills,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class AgentOnboardingResult:
    """
    Agent 入职结果
    
    包含入职后建立的任务状态机等信息
    """
    agent_id: str
    status: str  # success, failed
    
    # 任务状态图
    task_graph: Dict[str, Any] = field(default_factory=dict)
    
    # 初始任务列表
    initial_tasks: List[Dict[str, Any]] = field(default_factory=list)
    
    # 错误信息（如有）
    error: Optional[str] = None
    
    # 元数据
    onboarded_at: datetime = field(default_factory=datetime.now)


class DutySkillManager:
    """
    职责技能管理器
    
    管理按 Role 分类的 Duty Skills
    """
    
    def __init__(self, skills_dir: str = "./duty_skills"):
        self.skills_dir = skills_dir
        self._skills: Dict[str, Dict[str, Any]] = {}  # role -> skills
        
        # 自动加载
        self._load_all()
    
    def _load_all(self) -> None:
        """加载所有 Duty Skills"""
        if not os.path.exists(self.skills_dir):
            return
        
        for filename in os.listdir(self.skills_dir):
            if filename.endswith(".md"):
                role = filename.replace(".md", "")
                skill_path = os.path.join(self.skills_dir, filename)
                self._skills[role] = self._parse_skill_file(skill_path)
    
    def _parse_skill_file(self, path: str) -> Dict[str, Any]:
        """解析技能文件"""
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # 解析 YAML frontmatter
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                yaml_content = parts[1]
                data = yaml.safe_load(yaml_content) or {}
                
                return {
                    "skill_set_id": data.get("skill_set_id", ""),
                    "role": data.get("role", ""),
                    "name": data.get("name", ""),
                    "description": data.get("description", ""),
                    "content": content,
                }
        
        return {"content": content}
    
    def get_skills(self, role: str) -> Optional[Dict[str, Any]]:
        """获取指定 Role 的 Duty Skills"""
        return self._skills.get(role)
    
    def list_roles(self) -> List[str]:
        """列出所有有 Duty Skills 的 Role"""
        return list(self._skills.keys())


class OrchestrationSkillManager:
    """
    编排技能管理器
    
    管理按 Role 分类的 Orchestration Skills
    """
    
    def __init__(self, skills_dir: str = "./orchestration_skills"):
        self.skills_dir = skills_dir
        self._skills: Dict[str, Dict[str, Any]] = {}
        
        # 自动加载
        self._load_all()
    
    def _load_all(self) -> None:
        """加载所有 Orchestration Skills"""
        if not os.path.exists(self.skills_dir):
            return
        
        for filename in os.listdir(self.skills_dir):
            if filename.endswith(".md"):
                role = filename.replace(".md", "")
                skill_path = os.path.join(self.skills_dir, filename)
                self._skills[role] = self._parse_skill_file(skill_path)
    
    def _parse_skill_file(self, path: str) -> Dict[str, Any]:
        """解析技能文件"""
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                yaml_content = parts[1]
                data = yaml.safe_load(yaml_content) or {}
                
                return {
                    "skill_set_id": data.get("skill_set_id", ""),
                    "role": data.get("role", ""),
                    "name": data.get("name", ""),
                    "description": data.get("description", ""),
                    "content": content,
                }
        
        return {"content": content}
    
    def get_skills(self, role: str) -> Optional[Dict[str, Any]]:
        """获取指定 Role 的 Orchestration Skills"""
        return self._skills.get(role)
    
    def list_roles(self) -> List[str]:
        """列出所有有 Orchestration Skills 的 Role"""
        return list(self._skills.keys())


class AgentCreator:
    """
    Agent 创建器
    
    负责 Agent 的创建和入职流程
    """
    
    def __init__(
        self,
        jd_manager: Optional[JDManager] = None,
        resource_manager: Optional[ResourceManager] = None,
    ):
        self.jd_manager = jd_manager or get_jd_manager()
        self.resource_manager = resource_manager or ResourceManager()
        self.duty_skill_manager = DutySkillManager()
        self.orchestration_skill_manager = OrchestrationSkillManager()
        
        # 已创建的 Agent
        self._agents: Dict[str, AgentSpec] = {}
    
    # ========== Phase 1: Agent 创建 ==========
    
    def create_agent(
        self,
        jd_id: str,
        resource_bundle: Optional[ResourceBundle] = None,
        name: Optional[str] = None,
    ) -> AgentSpec:
        """
        创建 Agent
        
        参数:
            jd_id: Job Description ID
            resource_bundle: 资源包（可选，如不提供则使用默认）
            name: Agent 名称（可选）
        
        返回:
            AgentSpec: Agent 规格
        """
        # 1. 加载 JD
        jd = self.jd_manager.get_jd(jd_id)
        if not jd:
            raise ValueError(f"JD not found: {jd_id}")
        
        # 2. 确定 Role
        role = jd.role
        
        # 3. 加载 Duty Skills
        duty_skills = self.duty_skill_manager.get_skills(role)
        if not duty_skills:
            print(f"警告：未找到 Role '{role}' 的 Duty Skills")
        
        # 4. 加载 Orchestration Skills
        orch_skills = self.orchestration_skill_manager.get_skills(role)
        if not orch_skills:
            print(f"警告：未找到 Role '{role}' 的 Orchestration Skills")
        
        # 5. 创建 AgentSpec
        agent = AgentSpec(
            agent_id=f"agent_{uuid.uuid4().hex[:8]}",
            name=name or jd.name,
            jd_id=jd_id,
            jd=jd,
            resource_bundle_id=resource_bundle.bundle_id if resource_bundle else "",
            resource_bundle=resource_bundle,
            duty_skills=[duty_skills.get("skill_set_id", "")] if duty_skills else [],
            orchestration_skills=[orch_skills.get("skill_set_id", "")] if orch_skills else [],
        )
        
        # 6. 注册 Agent
        self._agents[agent.agent_id] = agent
        
        return agent
    
    # ========== Phase 2: JD + Resource 快速浏览 ==========
    
    def quick_browse(
        self,
        agent: AgentSpec,
    ) -> Dict[str, Any]:
        """
        快速浏览 JD 和 Resource
        
        让 Agent 了解自己的职责和可用资源
        """
        result = {
            "agent_id": agent.agent_id,
            "jd_summary": self._summarize_jd(agent.jd),
            "resource_summary": self._summarize_resources(agent.resource_bundle),
            "duty_skills": agent.duty_skills,
            "orchestration_skills": agent.orchestration_skills,
        }
        
        return result
    
    def _summarize_jd(self, jd: Optional[JobDescription]) -> Dict[str, Any]:
        """摘要 JD"""
        if not jd:
            return {}
        
        return {
            "role": jd.role,
            "name": jd.name,
            "responsibilities_count": len(jd.responsibilities),
            "required_skills": jd.requirements.required_skills if jd.requirements else [],
            "constraints_count": len(jd.constraints),
        }
    
    def _summarize_resources(self, bundle: Optional[ResourceBundle]) -> Dict[str, Any]:
        """摘要资源"""
        if not bundle:
            return {}
        
        return {
            "bundle_name": bundle.name,
            "resources_count": len(bundle.resources),
            "workspace": bundle.workspace,
            "by_type": self._count_resources_by_type(bundle),
        }
    
    def _count_resources_by_type(self, bundle: ResourceBundle) -> Dict[str, int]:
        """按类型统计资源"""
        counts = {}
        for resource in bundle.resources:
            t = resource.resource_type
            counts[t] = counts.get(t, 0) + 1
        return counts
    
    # ========== Phase 3: Orchestration 启动 ==========
    
    def start_orchestration(
        self,
        agent: AgentSpec,
        initial_tasks: Optional[List[Dict[str, Any]]] = None,
    ) -> AgentOnboardingResult:
        """
        启动 Orchestration
        
        使用 Orchestration Skills 建立任务状态机
        """
        # 1. 获取 Orchestration Skills
        orch_skills = self.orchestration_skill_manager.get_skills(agent.jd.role if agent.jd else "junior")
        
        if not orch_skills:
            return AgentOnboardingResult(
                agent_id=agent.agent_id,
                status="failed",
                error=f"Orchestration Skills not found for role: {agent.jd.role if agent.jd else 'junior'}",
            )
        
        # 2. 初始化任务状态图
        task_graph = self._initialize_task_graph(agent, initial_tasks)
        
        # 3. 创建初始任务
        initial_tasks_result = self._create_initial_tasks(agent, task_graph)
        
        return AgentOnboardingResult(
            agent_id=agent.agent_id,
            status="success",
            task_graph=task_graph,
            initial_tasks=initial_tasks_result,
        )
    
    def _initialize_task_graph(
        self,
        agent: AgentSpec,
        initial_tasks: Optional[List[Dict[str, Any]]],
    ) -> Dict[str, Any]:
        """初始化任务状态图"""
        return {
            "agent_id": agent.agent_id,
            "jd_id": agent.jd_id,
            "role": agent.jd.role if agent.jd else "junior",
            "tasks": initial_tasks or [],
            "status": "initialized",
            "created_at": datetime.now().isoformat(),
        }
    
    def _create_initial_tasks(
        self,
        agent: AgentSpec,
        task_graph: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """创建初始任务"""
        # 这里根据 JD 的职责创建初始任务
        # 实际实现会根据具体业务逻辑定制
        
        tasks = []
        
        if agent.jd:
            for i, resp in enumerate(agent.jd.responsibilities):
                task = {
                    "task_id": f"task_{i+1}",
                    "name": resp.name,
                    "description": resp.description,
                    "status": "pending",
                    "priority": "normal",
                }
                tasks.append(task)
                task_graph["tasks"].append(task)
        
        task_graph["status"] = "ready"
        
        return tasks
    
    # ========== 状态查询 ==========
    
    def get_agent(self, agent_id: str) -> Optional[AgentSpec]:
        """获取 Agent"""
        return self._agents.get(agent_id)
    
    def list_agents(self) -> List[Dict[str, str]]:
        """列出所有 Agent"""
        return [
            {"agent_id": a.agent_id, "name": a.name, "jd_id": a.jd_id}
            for a in self._agents.values()
        ]


# ========== 全局创建器实例 ==========

_default_creator: Optional[AgentCreator] = None


def get_agent_creator() -> AgentCreator:
    """获取全局 Agent 创建器"""
    global _default_creator
    if _default_creator is None:
        _default_creator = AgentCreator()
    return _default_creator
