"""
Job Description 模块

管理 Agent 的 JD 定义和加载
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime
import yaml
import os


@dataclass
class Responsibility:
    """职责定义"""
    id: str
    name: str
    description: str


@dataclass
class Requirement:
    """要求定义"""
    required_skills: List[str] = field(default_factory=list)
    preferred_skills: List[str] = field(default_factory=list)


@dataclass
class Constraint:
    """约束定义"""
    id: str
    description: str
    type: str = "permission"  # permission, process, technical


@dataclass
class SuccessMetric:
    """成功指标"""
    id: str
    name: str
    target: str


@dataclass
class JobDescription:
    """
    工作描述 (JD)
    
    定义 Agent 的角色、职责、要求等
    """
    jd_id: str
    role: str  # senior, junior, expert, manager
    name: str
    description: str
    
    # 核心内容
    responsibilities: List[Responsibility] = field(default_factory=list)
    requirements: Optional[Requirement] = None
    constraints: List[Constraint] = field(default_factory=list)
    success_metrics: List[SuccessMetric] = field(default_factory=list)
    
    # 协作关系
    reporting_to: str = ""
    collaborates_with: List[str] = field(default_factory=list)
    
    # 元数据
    version: str = "1.0"
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "jd_id": self.jd_id,
            "role": self.role,
            "name": self.name,
            "description": self.description,
            "responsibilities": [
                {"id": r.id, "name": r.name, "description": r.description}
                for r in self.responsibilities
            ],
            "requirements": {
                "required_skills": self.requirements.required_skills if self.requirements else [],
                "preferred_skills": self.requirements.preferred_skills if self.requirements else [],
            } if self.requirements else {},
            "constraints": [
                {"id": c.id, "description": c.description, "type": c.type}
                for c in self.constraints
            ],
            "success_metrics": [
                {"id": s.id, "name": s.name, "target": s.target}
                for s in self.success_metrics
            ],
            "reporting_to": self.reporting_to,
            "collaborates_with": self.collaborates_with,
            "version": self.version,
            "created_at": self.created_at.isoformat(),
        }
    
    @classmethod
    def from_markdown(cls, markdown_path: str) -> "JobDescription":
        """从 Markdown 文件加载 JD"""
        with open(markdown_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # 解析 YAML frontmatter
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                yaml_content = parts[1]
                data = yaml.safe_load(yaml_content) or {}
                
                # 解析 responsibilities
                responsibilities = []
                for i, resp in enumerate(data.get("responsibilities", [])):
                    responsibilities.append(Responsibility(
                        id=f"resp_{i+1}",
                        name=resp if isinstance(resp, str) else resp.get("name", ""),
                        description=resp if isinstance(resp, str) else resp.get("description", ""),
                    ))
                
                # 解析 requirements
                requirements = None
                req_data = data.get("requirements", {})
                if req_data:
                    requirements = Requirement(
                        required_skills=req_data.get("required_skills", []),
                        preferred_skills=req_data.get("preferred_skills", []),
                    )
                
                # 解析 constraints
                constraints = []
                for i, const in enumerate(data.get("constraints", [])):
                    constraints.append(Constraint(
                        id=f"constraint_{i+1}",
                        description=const if isinstance(const, str) else const,
                        type="process",
                    ))
                
                # 解析 success metrics
                success_metrics = []
                for i, metric in enumerate(data.get("success_metrics", [])):
                    if isinstance(metric, str):
                        parts = metric.split(">", 1)
                        success_metrics.append(SuccessMetric(
                            id=f"metric_{i+1}",
                            name=parts[0].strip() if len(parts) > 1 else metric,
                            target=parts[1].strip() if len(parts) > 1 else "",
                        ))
                
                return cls(
                    jd_id=data.get("jd_id", os.path.basename(markdown_path).replace(".md", "")),
                    role=data.get("role", "junior"),
                    name=data.get("name", "Unnamed Role"),
                    description=data.get("description", ""),
                    responsibilities=responsibilities,
                    requirements=requirements,
                    constraints=constraints,
                    success_metrics=success_metrics,
                    reporting_to=data.get("reporting_to", ""),
                    collaborates_with=data.get("collaborates_with", []),
                    version=data.get("version", "1.0"),
                )
        
        # 没有 frontmatter，返回基本 JD
        return cls(
            jd_id=os.path.basename(markdown_path).replace(".md", ""),
            role="junior",
            name="Unnamed Role",
            description=content[:200],
        )


class JDManager:
    """
    JD 管理器
    
    管理所有 JD 的加载和查询
    """
    
    def __init__(self, jd_dir: str = "./jd"):
        self.jd_dir = jd_dir
        self._jds: Dict[str, JobDescription] = {}
        
        # 自动加载 JD 目录
        self._load_all()
    
    def _load_all(self) -> None:
        """加载所有 JD 文件"""
        if not os.path.exists(self.jd_dir):
            return
        
        for filename in os.listdir(self.jd_dir):
            if filename.endswith(".md"):
                jd_path = os.path.join(self.jd_dir, filename)
                jd = JobDescription.from_markdown(jd_path)
                self._jds[jd.jd_id] = jd
    
    def get_jd(self, jd_id: str) -> Optional[JobDescription]:
        """获取 JD"""
        return self._jds.get(jd_id)
    
    def get_jd_by_role(self, role: str) -> List[JobDescription]:
        """按角色获取 JD"""
        return [jd for jd in self._jds.values() if jd.role == role]
    
    def list_jds(self) -> List[Dict[str, str]]:
        """列出所有 JD"""
        return [
            {"jd_id": jd.jd_id, "name": jd.name, "role": jd.role}
            for jd in self._jds.values()
        ]
    
    def register_jd(self, jd: JobDescription) -> None:
        """注册 JD"""
        self._jds[jd.jd_id] = jd


# 全局 JD 管理器
_default_jd_manager: Optional[JDManager] = None


def get_jd_manager() -> JDManager:
    """获取全局 JD 管理器"""
    global _default_jd_manager
    if _default_jd_manager is None:
        _default_jd_manager = JDManager()
    return _default_jd_manager
