"""
基础设施层：模块注册表

管理所有模块的注册、发现和生命周期
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Type
from datetime import datetime
import uuid


class ModuleType(Enum):
    """模块类型"""
    ORCHESTRATION = "orchestration"
    MEETING = "meeting"
    REPORTING = "reporting"
    EXECUTION_AGENT = "execution_agent"
    MEMORY = "memory"


class ModuleStatus(Enum):
    """模块状态"""
    REGISTERING = "registering"
    READY = "ready"
    BUSY = "busy"
    OFFLINE = "offline"
    ERROR = "error"


@dataclass
class ModuleInfo:
    """模块信息"""
    module_id: str
    module_type: ModuleType
    name: str
    description: str = ""
    
    status: ModuleStatus = ModuleStatus.REGISTERING
    capabilities: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    registered_at: datetime = field(default_factory=datetime.now)
    last_heartbeat: datetime = field(default_factory=datetime.now)
    
    # 连接信息
    endpoint: Optional[str] = None  # HTTP endpoint 或队列名称
    config: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "module_id": self.module_id,
            "module_type": self.module_type.value,
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "capabilities": self.capabilities,
            "metadata": self.metadata,
            "registered_at": self.registered_at.isoformat(),
            "last_heartbeat": self.last_heartbeat.isoformat(),
            "endpoint": self.endpoint,
            "config": self.config,
        }


class ModuleRegistry:
    """
    模块注册表
    
    管理所有模块的注册、发现和状态跟踪
    """
    
    def __init__(self):
        self._modules: Dict[str, ModuleInfo] = {}
        self._type_index: Dict[ModuleType, List[str]] = {t: [] for t in ModuleType}
        self._capability_index: Dict[str, List[str]] = {}
    
    # ========== 注册管理 ==========
    
    def register(self, module: ModuleInfo) -> None:
        """注册模块"""
        self._modules[module.module_id] = module
        
        # 更新类型索引
        if module.module_id not in self._type_index[module.module_type]:
            self._type_index[module.module_type].append(module.module_id)
        
        # 更新能力索引
        for cap in module.capabilities:
            if cap not in self._capability_index:
                self._capability_index[cap] = []
            if module.module_id not in self._capability_index[cap]:
                self._capability_index[cap].append(module.module_id)
    
    def unregister(self, module_id: str) -> Optional[ModuleInfo]:
        """注销模块"""
        module = self._modules.pop(module_id, None)
        if module:
            # 清理索引
            self._type_index[module.module_type].remove(module_id)
            for cap in module.capabilities:
                if cap in self._capability_index:
                    self._capability_index[cap].remove(module_id)
        return module
    
    # ========== 查询方法 ==========
    
    def get_module(self, module_id: str) -> Optional[ModuleInfo]:
        """获取模块信息"""
        return self._modules.get(module_id)
    
    def get_modules_by_type(self, module_type: ModuleType) -> List[ModuleInfo]:
        """按类型获取模块"""
        ids = self._type_index.get(module_type, [])
        return [self._modules[mid] for mid in ids if mid in self._modules]
    
    def get_modules_by_capability(self, capability: str) -> List[ModuleInfo]:
        """按能力获取模块"""
        ids = self._capability_index.get(capability, [])
        return [self._modules[mid] for mid in ids if mid in self._modules]
    
    def find_module(
        self,
        module_type: Optional[ModuleType] = None,
        capability: Optional[str] = None,
        status: Optional[ModuleStatus] = None,
    ) -> List[ModuleInfo]:
        """查找模块（支持多条件）"""
        results = list(self._modules.values())
        
        if module_type:
            results = [m for m in results if m.module_type == module_type]
        
        if capability:
            results = [m for m in results if capability in m.capabilities]
        
        if status:
            results = [m for m in results if m.status == status]
        
        return results
    
    # ========== 状态管理 ==========
    
    def update_status(self, module_id: str, status: ModuleStatus) -> bool:
        """更新模块状态"""
        module = self.get_module(module_id)
        if not module:
            return False
        
        module.status = status
        module.last_heartbeat = datetime.now()
        return True
    
    def heartbeat(self, module_id: str) -> bool:
        """更新心跳"""
        module = self.get_module(module_id)
        if not module:
            return False
        
        module.last_heartbeat = datetime.now()
        return True
    
    # ========== 健康检查 ==========
    
    def check_health(self, timeout_seconds: int = 60) -> Dict[str, Any]:
        """检查所有模块健康状态"""
        now = datetime.now()
        healthy = []
        unhealthy = []
        
        for module in self._modules.values():
            elapsed = (now - module.last_heartbeat).total_seconds()
            if elapsed > timeout_seconds:
                unhealthy.append({
                    "module_id": module.module_id,
                    "name": module.name,
                    "last_seen": module.last_heartbeat.isoformat(),
                    "elapsed": elapsed,
                })
            else:
                healthy.append(module.module_id)
        
        return {
            "healthy": healthy,
            "unhealthy": unhealthy,
            "total": len(self._modules),
        }
    
    # ========== 统计信息 ==========
    
    def get_stats(self) -> Dict[str, Any]:
        """获取注册表统计"""
        return {
            "total_modules": len(self._modules),
            "by_type": {
                t.value: len(self._type_index[t])
                for t in ModuleType
            },
            "by_status": {},
            "capabilities": list(self._capability_index.keys()),
        }


# ========== 全局注册表实例 ==========

_default_registry: Optional[ModuleRegistry] = None


def get_module_registry() -> ModuleRegistry:
    """获取全局模块注册表实例"""
    global _default_registry
    if _default_registry is None:
        _default_registry = ModuleRegistry()
    return _default_registry
