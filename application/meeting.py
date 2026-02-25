"""
应用层：Meeting（会议协作）

职责：
- 当任务需要多个智能体协作或复杂决策时，发起"会议"
- 让相关智能体通过 A2A 协议进行对话、协商、投票等
- 最终达成共识或生成解决方案
- 会议过程被记录到认知记忆中
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable, Awaitable
from datetime import datetime
import uuid
import asyncio

from infra import (
    Message, MessageType, MessagePriority,
    get_message_network, get_module_registry,
    ModuleType, ModuleStatus,
)
from memory import MemoryService, MemoryType as MemoryTypeEnum, get_memory_service


@dataclass
class MeetingAgenda:
    """会议议程"""
    agenda_id: str
    topic: str
    description: str
    
    # 参与方
    participants: List[str] = field(default_factory=list)  # agent_ids
    
    # 议程项目
    items: List[Dict[str, Any]] = field(default_factory=list)
    
    # 目标
    expected_outcome: str = ""
    
    # 状态
    status: str = "scheduled"  # scheduled, in_progress, completed, cancelled
    
    # 元数据
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "agenda_id": self.agenda_id,
            "topic": self.topic,
            "description": self.description,
            "participants": self.participants,
            "items": self.items,
            "expected_outcome": self.expected_outcome,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


@dataclass
class MeetingMessage:
    """会议中的消息"""
    message_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    sender_id: str = ""
    content: str = ""
    message_type: str = "statement"  # statement, question, proposal, vote
    
    timestamp: datetime = field(default_factory=datetime.now)
    in_reply_to: Optional[str] = None  # 回复的消息 ID
    
    # 投票相关
    vote_target: Optional[str] = None
    vote_value: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "message_id": self.message_id,
            "sender_id": self.sender_id,
            "content": self.content,
            "message_type": self.message_type,
            "timestamp": self.timestamp.isoformat(),
            "in_reply_to": self.in_reply_to,
            "vote_target": self.vote_target,
            "vote_value": self.vote_value,
        }


class MeetingService:
    """
    会议协作服务
    
    核心职责：
    1. 发起会议
    2. 协调多方对话
    3. 记录会议过程
    4. 达成共识
    """
    
    def __init__(self, service_id: Optional[str] = None):
        self.service_id = service_id or f"meeting_{uuid.uuid4().hex[:8]}"
        self.memory = get_memory_service()
        self.network = get_message_network()
        
        # 进行中的会议
        self.active_meetings: Dict[str, MeetingAgenda] = {}
        
        # 会议记录
        self.meeting_records: Dict[str, List[MeetingMessage]] = {}
        
        # 共识结果
        self.consensus_results: Dict[str, Dict[str, Any]] = {}
        
        # 注册到模块注册表
        self._register_self()
        
        # 注册消息处理器
        self._register_message_handlers()
    
    def _register_self(self) -> None:
        """注册自己到模块注册表"""
        registry = get_module_registry()
        
        module_info = ModuleInfo(
            module_id=self.service_id,
            module_type=ModuleType.MEETING,
            name="Meeting Service",
            description="Multi-agent collaboration and consensus building",
            status=ModuleStatus.READY,
            capabilities=["collaboration", "negotiation", "voting", "consensus"],
        )
        
        registry.register(module_info)
    
    def _register_message_handlers(self) -> None:
        """注册消息处理器"""
        self.network.register_handler(
            MessageType.A2A_COLLABORATION_REQUEST,
            self._handle_collaboration_request,
        )
        
        self.network.register_handler(
            MessageType.A2A_NEGOTIATION,
            self._handle_negotiation,
        )
    
    # ========== 会议管理 ==========
    
    def create_meeting(
        self,
        topic: str,
        description: str,
        participants: List[str],
        agenda_items: Optional[List[Dict[str, Any]]] = None,
        expected_outcome: str = "",
    ) -> MeetingAgenda:
        """创建会议"""
        agenda = MeetingAgenda(
            agenda_id=str(uuid.uuid4())[:8],
            topic=topic,
            description=description,
            participants=participants,
            items=agenda_items or [],
            expected_outcome=expected_outcome,
        )
        
        self.active_meetings[agenda.agenda_id] = agenda
        self.meeting_records[agenda.agenda_id] = []
        
        return agenda
    
    def start_meeting(self, agenda_id: str) -> bool:
        """开始会议"""
        agenda = self.active_meetings.get(agenda_id)
        if not agenda:
            return False
        
        agenda.status = "in_progress"
        agenda.started_at = datetime.now()
        
        # 发送会议开始通知
        self._broadcast_to_participants(
            agenda_id,
            MessageType.A2A_COLLABORATION_REQUEST,
            {
                "meeting_id": agenda_id,
                "topic": agenda.topic,
                "action": "meeting_started",
            },
        )
        
        return True
    
    def end_meeting(self, agenda_id: str, outcome: Optional[Dict[str, Any]] = None) -> bool:
        """结束会议"""
        agenda = self.active_meetings.get(agenda_id)
        if not agenda:
            return False
        
        agenda.status = "completed"
        agenda.completed_at = datetime.now()
        
        # 保存会议记录到认知记忆
        self._save_meeting_to_memory(agenda_id, outcome)
        
        # 发送会议结束通知
        self._broadcast_to_participants(
            agenda_id,
            MessageType.A2A_CONSENSUS,
            {
                "meeting_id": agenda_id,
                "action": "meeting_ended",
                "outcome": outcome,
            },
        )
        
        return True
    
    def add_message(
        self,
        meeting_id: str,
        sender_id: str,
        content: str,
        message_type: str = "statement",
        in_reply_to: Optional[str] = None,
    ) -> MeetingMessage:
        """添加会议消息"""
        messages = self.meeting_records.get(meeting_id, [])
        
        message = MeetingMessage(
            sender_id=sender_id,
            content=content,
            message_type=message_type,
            in_reply_to=in_reply_to,
        )
        
        messages.append(message)
        self.meeting_records[meeting_id] = messages
        
        return message
    
    # ========== 协商与投票 ==========
    
    async def propose(
        self,
        meeting_id: str,
        proposer_id: str,
        proposal: str,
    ) -> Dict[str, Any]:
        """提出方案"""
        # 添加 proposal 到会议记录
        self.add_message(
            meeting_id=meeting_id,
            sender_id=proposer_id,
            content=proposal,
            message_type="proposal",
        )
        
        # 通知其他参与者
        agenda = self.active_meetings.get(meeting_id)
        if not agenda:
            return {"status": "error", "message": "Meeting not found"}
        
        for participant in agenda.participants:
            if participant != proposer_id:
                message = Message(
                    message_type=MessageType.A2A_NEGOTIATION,
                    source=proposer_id,
                    target=participant,
                    payload={
                        "meeting_id": meeting_id,
                        "type": "proposal",
                        "content": proposal,
                    },
                )
                await self.network.send(message)
        
        return {"status": "proposed", "proposal": proposal}
    
    async def vote(
        self,
        meeting_id: str,
        voter_id: str,
        proposal_id: str,
        vote_value: str,
    ) -> Dict[str, Any]:
        """投票"""
        # 记录投票
        self.add_message(
            meeting_id=meeting_id,
            sender_id=voter_id,
            content=f"Vote: {vote_value}",
            message_type="vote",
        )
        
        # 检查是否达成共识
        consensus = self._check_consensus(meeting_id, proposal_id)
        
        return {
            "status": "voted",
            "vote": vote_value,
            "consensus_reached": consensus["reached"],
        }
    
    def _check_consensus(
        self,
        meeting_id: str,
        proposal_id: str,
    ) -> Dict[str, Any]:
        """检查是否达成共识"""
        messages = self.meeting_records.get(meeting_id, [])
        
        # 统计投票
        votes = [m for m in messages if m.message_type == "vote" and m.vote_target == proposal_id]
        
        if not votes:
            return {"reached": False, "reason": "No votes"}
        
        # 简单多数原则
        yes_votes = sum(1 for v in votes if v.vote_value == "yes" or v.vote_value == "agree")
        no_votes = sum(1 for v in votes if v.vote_value == "no" or v.vote_value == "disagree")
        
        total_participants = len(self.active_meetings.get(meeting_id, {}).participants)
        required_majority = total_participants // 2 + 1
        
        if yes_votes >= required_majority:
            return {"reached": True, "result": "approved", "votes": yes_votes}
        elif no_votes >= required_majority:
            return {"reached": True, "result": "rejected", "votes": no_votes}
        
        return {"reached": False, "reason": "No majority"}
    
    # ========== 消息处理 ==========
    
    async def _handle_collaboration_request(self, message: Message) -> None:
        """处理协作请求"""
        context = message.payload.get("context", {})
        meeting_id = context.get("meeting_id")
        
        if meeting_id and meeting_id in self.active_meetings:
            # 添加消息到会议记录
            self.add_message(
                meeting_id=meeting_id,
                sender_id=message.source,
                content=str(context.get("message", "")),
            )
    
    async def _handle_negotiation(self, message: Message) -> None:
        """处理协商消息"""
        payload = message.payload
        meeting_id = payload.get("meeting_id")
        
        if meeting_id:
            # 转发给其他参与者
            agenda = self.active_meetings.get(meeting_id)
            if agenda:
                for participant in agenda.participants:
                    if participant != message.source:
                        forward = Message(
                            message_type=MessageType.A2A_NEGOTIATION,
                            source=message.source,
                            target=participant,
                            payload=payload,
                        )
                        await self.network.send(forward)
    
    # ========== 工具方法 ==========
    
    def _broadcast_to_participants(
        self,
        meeting_id: str,
        message_type: MessageType,
        payload: Dict[str, Any],
    ) -> None:
        """广播给会议参与者"""
        agenda = self.active_meetings.get(meeting_id)
        if not agenda:
            return
        
        for participant in agenda.participants:
            message = Message(
                message_type=message_type,
                source=self.service_id,
                target=participant,
                payload=payload,
            )
            asyncio.create_task(self.network.send(message))
    
    def _save_meeting_to_memory(
        self,
        meeting_id: str,
        outcome: Optional[Dict[str, Any]],
    ) -> None:
        """保存会议记录到记忆"""
        agenda = self.active_meetings.get(meeting_id)
        if not agenda:
            return
        
        messages = self.meeting_records.get(meeting_id, [])
        
        record = {
            "agenda": agenda.to_dict(),
            "messages": [m.to_dict() for m in messages],
            "outcome": outcome,
        }
        
        # 存储到认知记忆
        self.memory.store_knowledge(
            key=f"meeting:{meeting_id}",
            value=record,
            tags=["meeting", "collaboration", f"meeting:{meeting_id}"],
            created_by=self.service_id,
        )
    
    # ========== 状态查询 ==========
    
    def get_meeting_status(self, meeting_id: str) -> Optional[Dict[str, Any]]:
        """获取会议状态"""
        agenda = self.active_meetings.get(meeting_id)
        if not agenda:
            return None
        
        messages = self.meeting_records.get(meeting_id, [])
        
        return {
            "agenda": agenda.to_dict(),
            "message_count": len(messages),
            "consensus_results": self.consensus_results.get(meeting_id),
        }
    
    def get_meeting_history(self, meeting_id: str) -> List[Dict[str, Any]]:
        """获取会议历史"""
        messages = self.meeting_records.get(meeting_id, [])
        return [m.to_dict() for m in messages]
