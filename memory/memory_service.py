"""
记忆层：统一存储但逻辑分离

Cognitive Memory：长期认知结果存储（知识图谱、推理结论、学习到的模式）
Notebook Memory：短期任务状态记录（便签、工作上下文）

两者共用同一层但逻辑分离，通过消息网络与编排、执行层交互
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from datetime import datetime
import uuid
import json
import os


class MemoryType(Enum):
    """记忆类型"""
    COGNITIVE = "cognitive"  # 长期认知
    NOTEBOOK = "notebook"    # 短期任务


class MemoryVisibility(Enum):
    """记忆可见性"""
    PRIVATE = "private"    # 仅创建者可访问
    SHARED = "shared"      # 同团队可访问
    PUBLIC = "public"      # 所有模块可访问


@dataclass
class MemoryEntry:
    """
    记忆条目
    
    所有记忆的基本单位
    """
    entry_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    memory_type: MemoryType = MemoryType.NOTEBOOK
    
    # 内容
    key: str = ""                    # 键（用于检索）
    value: Any = None                # 值（可以是任意结构）
    content_hash: str = ""           # 内容哈希（用于去重）
    
    # 元数据
    created_by: str = ""             # 创建者 ID
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None  # 过期时间（None 表示永不过期）
    
    # 访问控制
    visibility: MemoryVisibility = MemoryVisibility.SHARED
    tags: List[str] = field(default_factory=list)
    
    # 引用关系
    references: List[str] = field(default_factory=list)  # 引用的其他 entry_id
    
    # 访问统计
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "memory_type": self.memory_type.value,
            "key": self.key,
            "value": self.value,
            "content_hash": self.content_hash,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "visibility": self.visibility.value,
            "tags": self.tags,
            "references": self.references,
            "access_count": self.access_count,
            "last_accessed": self.last_accessed.isoformat() if self.last_accessed else None,
        }
    
    def is_expired(self) -> bool:
        """检查是否过期"""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at
    
    def touch(self) -> None:
        """更新访问时间和计数"""
        self.access_count += 1
        self.last_accessed = datetime.now()


class MemoryStore:
    """
    记忆存储：底层存储抽象
    
    支持多种后端：内存、文件、Redis、向量数据库等
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        self._entries: Dict[str, MemoryEntry] = {}
        self._key_index: Dict[str, str] = {}  # key -> entry_id
        self._tag_index: Dict[str, List[str]] = {}  # tag -> entry_ids
        self._storage_path = storage_path
        
        # 如果指定了存储路径，加载持久化数据
        if storage_path:
            self._load_from_disk()
    
    # ========== 基本操作 ==========
    
    def put(self, entry: MemoryEntry) -> str:
        """存储记忆条目"""
        # 计算内容哈希
        if not entry.content_hash:
            entry.content_hash = self._compute_hash(entry.value)
        
        # 存储
        self._entries[entry.entry_id] = entry
        
        # 更新索引
        if entry.key:
            index_key = f"{entry.memory_type.value}:{entry.key}"
            self._key_index[index_key] = entry.entry_id
        
        for tag in entry.tags:
            if tag not in self._tag_index:
                self._tag_index[tag] = []
            if entry.entry_id not in self._tag_index[tag]:
                self._tag_index[tag].append(entry.entry_id)
        
        # 持久化
        self._save_to_disk()
        
        return entry.entry_id
    
    def get(self, entry_id: str) -> Optional[MemoryEntry]:
        """获取记忆条目"""
        entry = self._entries.get(entry_id)
        if entry and not entry.is_expired():
            entry.touch()
            return entry
        elif entry and entry.is_expired():
            # 过期条目，删除
            self.delete(entry_id)
            return None
        return None
    
    def get_by_key(self, memory_type: MemoryType, key: str) -> Optional[MemoryEntry]:
        """通过键获取记忆"""
        index_key = f"{memory_type.value}:{key}"
        entry_id = self._key_index.get(index_key)
        if entry_id:
            return self.get(entry_id)
        return None
    
    def delete(self, entry_id: str) -> bool:
        """删除记忆条目"""
        entry = self._entries.pop(entry_id, None)
        if not entry:
            return False
        
        # 清理索引
        index_key = f"{entry.memory_type.value}:{entry.key}"
        self._key_index.pop(index_key, None)
        
        for tag in entry.tags:
            if tag in self._tag_index:
                self._tag_index[tag].remove(entry_id)
        
        self._save_to_disk()
        return True
    
    # ========== 查询方法 ==========
    
    def find_by_type(self, memory_type: MemoryType) -> List[MemoryEntry]:
        """按类型查找"""
        return [
            e for e in self._entries.values()
            if e.memory_type == memory_type and not e.is_expired()
        ]
    
    def find_by_tags(self, tags: List[str]) -> List[MemoryEntry]:
        """按标签查找（支持多标签）"""
        result_ids = set()
        for tag in tags:
            ids = set(self._tag_index.get(tag, []))
            if result_ids:
                result_ids &= ids  # 交集
            else:
                result_ids = ids
        
        return [
            self._entries[eid] for eid in result_ids
            if eid in self._entries and not self._entries[eid].is_expired()
        ]
    
    def find_by_key_pattern(self, pattern: str) -> List[MemoryEntry]:
        """按键模式查找（支持通配符）"""
        import fnmatch
        results = []
        for index_key, entry_id in self._key_index.items():
            if fnmatch.fnmatch(index_key, pattern):
                entry = self.get(entry_id)
                if entry:
                    results.append(entry)
        return results
    
    def search(
        self,
        memory_type: Optional[MemoryType] = None,
        tags: Optional[List[str]] = None,
        created_by: Optional[str] = None,
        limit: int = 100,
    ) -> List[MemoryEntry]:
        """高级搜索"""
        results = list(self._entries.values())
        
        # 过滤过期
        results = [e for e in results if not e.is_expired()]
        
        # 按类型过滤
        if memory_type:
            results = [e for e in results if e.memory_type == memory_type]
        
        # 按标签过滤
        if tags:
            results = [e for e in results if any(t in e.tags for t in tags)]
        
        # 按创建者过滤
        if created_by:
            results = [e for e in results if e.created_by == created_by]
        
        return results[:limit]
    
    # ========== 工具方法 ==========
    
    def _compute_hash(self, value: Any) -> str:
        """计算内容哈希"""
        import hashlib
        content = json.dumps(value, sort_keys=True, default=str)
        return hashlib.md5(content.encode()).hexdigest()[:16]
    
    def _save_to_disk(self) -> None:
        """持久化到磁盘"""
        if not self._storage_path:
            return
        
        os.makedirs(self._storage_path, exist_ok=True)
        
        # 保存所有条目
        data = {
            "entries": {eid: e.to_dict() for eid, e in self._entries.items()},
            "key_index": self._key_index,
            "tag_index": self._tag_index,
        }
        
        with open(os.path.join(self._storage_path, "memory_store.json"), "w") as f:
            json.dump(data, f, indent=2)
    
    def _load_from_disk(self) -> None:
        """从磁盘加载"""
        if not self._storage_path:
            return
        
        file_path = os.path.join(self._storage_path, "memory_store.json")
        if not os.path.exists(file_path):
            return
        
        with open(file_path, "r") as f:
            data = json.load(f)
        
        # 恢复条目
        for eid, entry_data in data.get("entries", {}).items():
            entry = MemoryEntry(
                entry_id=entry_data["entry_id"],
                memory_type=MemoryType(entry_data["memory_type"]),
                key=entry_data["key"],
                value=entry_data["value"],
                content_hash=entry_data["content_hash"],
                created_by=entry_data["created_by"],
                created_at=datetime.fromisoformat(entry_data["created_at"]),
                updated_at=datetime.fromisoformat(entry_data["updated_at"]),
                expires_at=(
                    datetime.fromisoformat(entry_data["expires_at"])
                    if entry_data["expires_at"] else None
                ),
                visibility=MemoryVisibility(entry_data["visibility"]),
                tags=entry_data["tags"],
                references=entry_data["references"],
                access_count=entry_data["access_count"],
                last_accessed=(
                    datetime.fromisoformat(entry_data["last_accessed"])
                    if entry_data["last_accessed"] else None
                ),
            )
            self._entries[eid] = entry
        
        self._key_index = data.get("key_index", {})
        self._tag_index = data.get("tag_index", {})
    
    def get_stats(self) -> Dict[str, Any]:
        """获取存储统计"""
        cognitive = self.find_by_type(MemoryType.COGNITIVE)
        notebook = self.find_by_type(MemoryType.NOTEBOOK)
        
        return {
            "total_entries": len(self._entries),
            "cognitive_count": len(cognitive),
            "notebook_count": len(notebook),
            "unique_tags": len(self._tag_index),
            "unique_keys": len(self._key_index),
        }


class MemoryService:
    """
    记忆服务：高层 API
    
    通过消息网络接收请求，操作记忆存储
    """
    
    def __init__(
        self,
        store: Optional[MemoryStore] = None,
        storage_path: Optional[str] = None,
    ):
        self.store = store or MemoryStore(storage_path)
        self.module_id = f"memory_{uuid.uuid4().hex[:8]}"
    
    # ========== Cognitive Memory API ==========
    
    def store_knowledge(
        self,
        key: str,
        value: Any,
        tags: List[str],
        created_by: str = "system",
    ) -> str:
        """存储认知知识"""
        entry = MemoryEntry(
            memory_type=MemoryType.COGNITIVE,
            key=key,
            value=value,
            tags=tags,
            created_by=created_by,
            visibility=MemoryVisibility.SHARED,
        )
        return self.store.put(entry)
    
    def get_knowledge(self, key: str) -> Optional[Any]:
        """获取认知知识"""
        entry = self.store.get_by_key(MemoryType.COGNITIVE, key)
        return entry.value if entry else None
    
    def find_knowledge(self, tags: List[str]) -> List[Dict[str, Any]]:
        """查找认知知识"""
        entries = self.store.find_by_tags(tags)
        entries = [e for e in entries if e.memory_type == MemoryType.COGNITIVE]
        return [{"key": e.key, "value": e.value, "tags": e.tags} for e in entries]
    
    # ========== Notebook Memory API ==========
    
    def store_task_state(
        self,
        task_id: str,
        state: Dict[str, Any],
        created_by: str = "system",
        ttl_seconds: int = 3600,
    ) -> str:
        """存储任务状态（短期）"""
        from datetime import timedelta
        
        entry = MemoryEntry(
            memory_type=MemoryType.NOTEBOOK,
            key=f"task:{task_id}",
            value=state,
            tags=["task", f"task:{task_id}"],
            created_by=created_by,
            expires_at=datetime.now() + timedelta(seconds=ttl_seconds),
            visibility=MemoryVisibility.SHARED,
        )
        return self.store.put(entry)
    
    def get_task_state(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务状态"""
        entry = self.store.get_by_key(MemoryType.NOTEBOOK, f"task:{task_id}")
        return entry.value if entry else None
    
    def store_working_context(
        self,
        context_id: str,
        context: Dict[str, Any],
        created_by: str = "system",
        ttl_seconds: int = 1800,
    ) -> str:
        """存储工作上下文"""
        from datetime import timedelta
        
        entry = MemoryEntry(
            memory_type=MemoryType.NOTEBOOK,
            key=f"context:{context_id}",
            value=context,
            tags=["context", f"context:{context_id}"],
            created_by=created_by,
            expires_at=datetime.now() + timedelta(seconds=ttl_seconds),
        )
        return self.store.put(entry)
    
    def get_working_context(self, context_id: str) -> Optional[Dict[str, Any]]:
        """获取工作上下文"""
        entry = self.store.get_by_key(MemoryType.NOTEBOOK, f"context:{context_id}")
        return entry.value if entry else None
    
    # ========== 清理方法 ==========
    
    def cleanup_expired(self) -> int:
        """清理过期条目"""
        expired = [
            e.entry_id for e in self.store._entries.values()
            if e.is_expired()
        ]
        for entry_id in expired:
            self.store.delete(entry_id)
        return len(expired)
    
    def cleanup_old_notebook(self, max_age_hours: int = 24) -> int:
        """清理旧的 Notebook 记忆"""
        from datetime import timedelta
        
        cutoff = datetime.now() - timedelta(hours=max_age_hours)
        old_entries = [
            e.entry_id for e in self.store._entries.values()
            if e.memory_type == MemoryType.NOTEBOOK
            and e.created_at < cutoff
        ]
        for entry_id in old_entries:
            self.store.delete(entry_id)
        return len(old_entries)


# ========== 全局记忆服务实例 ==========

_default_memory_service: Optional[MemoryService] = None


def get_memory_service(storage_path: Optional[str] = None) -> MemoryService:
    """获取全局记忆服务实例"""
    global _default_memory_service
    if _default_memory_service is None:
        _default_memory_service = MemoryService(storage_path=storage_path)
    return _default_memory_service
