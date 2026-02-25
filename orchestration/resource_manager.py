"""
Resource 管理模块

管理 Agent 工作所需的资源：
- 代码路径
- 文档路径
- 配置文件
- 工具访问权限
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime
import os
import yaml


@dataclass
class Resource:
    """
    资源定义
    
    Agent 工作需要的各类资源
    """
    resource_id: str
    name: str
    resource_type: str  # code, document, config, tool, api
    
    # 资源位置
    path: Optional[str] = None
    url: Optional[str] = None
    
    # 访问权限
    read_only: bool = True
    required: bool = True
    
    # 元数据
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "resource_id": self.resource_id,
            "name": self.name,
            "resource_type": self.resource_type,
            "path": self.path,
            "url": self.url,
            "read_only": self.read_only,
            "required": self.required,
            "description": self.description,
            "metadata": self.metadata,
        }


@dataclass
class ResourceBundle:
    """
    资源包
    
    一组相关的资源集合，分配给 Agent 使用
    """
    bundle_id: str
    name: str
    description: str
    
    # 资源列表
    resources: List[Resource] = field(default_factory=list)
    
    # 工作空间
    workspace: str = "./workspace"
    
    # 元数据
    created_at: datetime = field(default_factory=datetime.now)
    created_by: str = ""
    
    def add_resource(self, resource: Resource) -> None:
        """添加资源"""
        self.resources.append(resource)
    
    def get_resources_by_type(self, resource_type: str) -> List[Resource]:
        """按类型获取资源"""
        return [r for r in self.resources if r.resource_type == resource_type]
    
    def get_required_resources(self) -> List[Resource]:
        """获取必需资源"""
        return [r for r in self.resources if r.required]
    
    def validate(self) -> List[str]:
        """
        验证资源可用性
        
        返回：
            错误列表，空列表表示所有资源可用
        """
        errors = []
        
        for resource in self.resources:
            if resource.path:
                # 检查路径是否存在
                if not os.path.exists(resource.path):
                    if resource.required:
                        errors.append(f"必需资源不存在：{resource.path}")
            
            if resource.url:
                # URL 资源暂时不验证
                pass
        
        return errors
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "bundle_id": self.bundle_id,
            "name": self.name,
            "description": self.description,
            "workspace": self.workspace,
            "resources": [r.to_dict() for r in self.resources],
            "created_at": self.created_at.isoformat(),
            "created_by": self.created_by,
        }


class ResourceManager:
    """
    资源管理器
    
    管理所有资源的注册、分配和验证
    """
    
    def __init__(self):
        self._bundles: Dict[str, ResourceBundle] = {}
        self._resources: Dict[str, Resource] = {}
    
    def register_resource(self, resource: Resource) -> None:
        """注册资源"""
        self._resources[resource.resource_id] = resource
    
    def create_bundle(
        self,
        bundle_id: str,
        name: str,
        description: str,
        workspace: str = "./workspace",
    ) -> ResourceBundle:
        """创建资源包"""
        bundle = ResourceBundle(
            bundle_id=bundle_id,
            name=name,
            description=description,
            workspace=workspace,
        )
        self._bundles[bundle_id] = bundle
        return bundle
    
    def get_bundle(self, bundle_id: str) -> Optional[ResourceBundle]:
        """获取资源包"""
        return self._bundles.get(bundle_id)
    
    def get_resource(self, resource_id: str) -> Optional[Resource]:
        """获取资源"""
        return self._resources.get(resource_id)
    
    # ========== 从 YAML 加载资源包 ==========
    
    @classmethod
    def load_from_yaml(cls, yaml_path: str) -> ResourceBundle:
        """从 YAML 文件加载资源包"""
        with open(yaml_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        
        bundle = ResourceBundle(
            bundle_id=data.get("bundle_id", "default"),
            name=data.get("name", "Resource Bundle"),
            description=data.get("description", ""),
            workspace=data.get("workspace", "./workspace"),
        )
        
        # 加载资源
        for res_data in data.get("resources", []):
            resource = Resource(
                resource_id=res_data.get("resource_id", ""),
                name=res_data.get("name", ""),
                resource_type=res_data.get("type", "file"),
                path=res_data.get("path"),
                url=res_data.get("url"),
                read_only=res_data.get("read_only", True),
                required=res_data.get("required", True),
                description=res_data.get("description", ""),
                metadata=res_data.get("metadata", {}),
            )
            bundle.add_resource(resource)
        
        return bundle


# ========== 预定义资源包 ==========

def create_python_dev_resources(workspace: str = "./workspace") -> ResourceBundle:
    """创建 Python 开发资源包"""
    bundle = ResourceBundle(
        bundle_id="python_dev_resources",
        name="Python 开发资源",
        description="Python 开发工程师所需的资源",
        workspace=workspace,
    )
    
    # 代码资源
    bundle.add_resource(Resource(
        resource_id="src_code",
        name="源代码目录",
        resource_type="code",
        path=os.path.join(workspace, "src"),
        read_only=False,
        required=True,
        description="项目源代码目录",
    ))
    
    # 测试资源
    bundle.add_resource(Resource(
        resource_id="test_code",
        name="测试代码目录",
        resource_type="code",
        path=os.path.join(workspace, "tests"),
        read_only=False,
        required=True,
        description="测试代码目录",
    ))
    
    # 文档资源
    bundle.add_resource(Resource(
        resource_id="docs",
        name="文档目录",
        resource_type="document",
        path=os.path.join(workspace, "docs"),
        read_only=True,
        required=True,
        description="项目文档目录",
    ))
    
    # 配置资源
    bundle.add_resource(Resource(
        resource_id="config",
        name="配置文件",
        resource_type="config",
        path=os.path.join(workspace, "config"),
        read_only=True,
        required=False,
        description="项目配置文件目录",
    ))
    
    return bundle


def create_code_review_resources(workspace: str = "./workspace") -> ResourceBundle:
    """创建代码审查资源包"""
    bundle = ResourceBundle(
        bundle_id="code_review_resources",
        name="代码审查资源",
        description="代码审查所需的资源",
        workspace=workspace,
    )
    
    # 待审查代码
    bundle.add_resource(Resource(
        resource_id="pr_code",
        name="PR 代码",
        resource_type="code",
        path=os.path.join(workspace, "pr"),
        read_only=True,
        required=True,
        description="待审查的 Pull Request 代码",
    ))
    
    # 审查规范
    bundle.add_resource(Resource(
        resource_id="review_guide",
        name="审查规范",
        resource_type="document",
        path=os.path.join(workspace, "docs", "review_guide.md"),
        read_only=True,
        required=True,
        description="代码审查规范和检查清单",
    ))
    
    return bundle
