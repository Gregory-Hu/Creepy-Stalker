"""
应用层：Reporting（报告生成）

职责：
- 监听任务状态事件
- 当任务达到特定里程碑（如完成、出错、需要人工干预）时，自动生成结构化报告
- 采用事件驱动模式，与编排层松耦合
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime
import uuid
import asyncio
import os

from infra import (
    Message, MessageType, MessagePriority,
    get_message_network, get_module_registry,
    ModuleType, ModuleStatus,
)
from memory import MemoryService, MemoryType as MemoryTypeEnum, get_memory_service


@dataclass
class ReportTemplate:
    """报告模板"""
    template_id: str
    name: str
    description: str
    
    # 触发条件
    trigger_events: List[str] = field(default_factory=list)  # 如：task_completed, task_failed
    
    # 报告结构
    sections: List[Dict[str, Any]] = field(default_factory=list)
    
    # 输出格式
    output_format: str = "markdown"  # markdown, html, json
    
    # 元数据
    version: str = "1.0"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "template_id": self.template_id,
            "name": self.name,
            "description": self.description,
            "trigger_events": self.trigger_events,
            "sections": self.sections,
            "output_format": self.output_format,
            "version": self.version,
        }


@dataclass
class GeneratedReport:
    """生成的报告"""
    report_id: str
    template_id: str
    title: str
    
    # 报告内容
    content: str
    sections: Dict[str, Any] = field(default_factory=dict)
    
    # 关联数据
    related_task_id: Optional[str] = None
    related_meeting_id: Optional[str] = None
    
    # 元数据
    generated_at: datetime = field(default_factory=datetime.now)
    generated_by: str = ""
    
    # 分发状态
    distributed_to: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_id": self.report_id,
            "template_id": self.template_id,
            "title": self.title,
            "content": self.content,
            "sections": self.sections,
            "related_task_id": self.related_task_id,
            "related_meeting_id": self.related_meeting_id,
            "generated_at": self.generated_at.isoformat(),
            "generated_by": self.generated_by,
            "distributed_to": self.distributed_to,
        }


class ReportingService:
    """
    报告生成服务
    
    核心职责：
    1. 监听任务事件
    2. 根据模板生成报告
    3. 分发报告
    """
    
    def __init__(self, service_id: Optional[str] = None, output_dir: str = "./reports"):
        self.service_id = service_id or f"reporting_{uuid.uuid4().hex[:8]}"
        self.output_dir = output_dir
        self.memory = get_memory_service()
        self.network = get_message_network()
        
        # 报告模板
        self.templates: Dict[str, ReportTemplate] = {}
        
        # 生成的报告
        self.reports: Dict[str, GeneratedReport] = {}
        
        # 事件处理器
        self.event_handlers: Dict[str, List[Callable]] = {}
        
        # 注册到模块注册表
        self._register_self()
        
        # 注册事件监听
        self._register_event_listeners()
        
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
    
    def _register_self(self) -> None:
        """注册自己到模块注册表"""
        registry = get_module_registry()
        
        module_info = ModuleInfo(
            module_id=self.service_id,
            module_type=ModuleType.REPORTING,
            name="Reporting Service",
            description="Automated report generation and distribution",
            status=ModuleStatus.READY,
            capabilities=["task_report", "meeting_report", "summary_report"],
        )
        
        registry.register(module_info)
    
    def _register_event_listeners(self) -> None:
        """注册事件监听器"""
        # 监听任务完成事件
        self.network.subscribe(
            subscriber_id=self.service_id,
            topic="task_events",
            callback=self._handle_task_event,
        )
        
        # 监听会议完成事件
        self.network.subscribe(
            subscriber_id=self.service_id,
            topic="meeting_events",
            callback=self._handle_meeting_event,
        )
    
    # ========== 模板管理 ==========
    
    def register_template(self, template: ReportTemplate) -> None:
        """注册报告模板"""
        self.templates[template.template_id] = template
    
    def get_template(self, template_id: str) -> Optional[ReportTemplate]:
        """获取模板"""
        return self.templates.get(template_id)
    
    def load_templates_from_directory(self, templates_dir: str) -> int:
        """从目录加载模板"""
        count = 0
        if not os.path.exists(templates_dir):
            return 0
        
        for filename in os.listdir(templates_dir):
            if filename.endswith(".md"):
                template = self._parse_template_from_markdown(
                    os.path.join(templates_dir, filename)
                )
                if template:
                    self.register_template(template)
                    count += 1
        
        return count
    
    def _parse_template_from_markdown(self, path: str) -> Optional[ReportTemplate]:
        """从 Markdown 文件解析模板"""
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # 解析 YAML frontmatter
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                import yaml
                yaml_content = parts[1]
                data = yaml.safe_load(yaml_content) or {}
                
                return ReportTemplate(
                    template_id=data.get("template_id", str(uuid.uuid4())[:8]),
                    name=data.get("name", "Unnamed Template"),
                    description=data.get("description", ""),
                    trigger_events=data.get("trigger_events", []),
                    sections=data.get("sections", []),
                    output_format=data.get("output_format", "markdown"),
                    version=data.get("version", "1.0"),
                )
        
        return None
    
    # ========== 报告生成 ==========
    
    async def generate_report(
        self,
        template_id: str,
        context: Dict[str, Any],
    ) -> GeneratedReport:
        """生成报告"""
        template = self.get_template(template_id)
        if not template:
            raise ValueError(f"Template not found: {template_id}")
        
        # 生成报告内容
        content = self._render_template(template, context)
        
        report = GeneratedReport(
            report_id=str(uuid.uuid4())[:8],
            template_id=template_id,
            title=context.get("title", f"Report - {datetime.now().strftime('%Y-%m-%d')}"),
            content=content,
            sections=context,
            related_task_id=context.get("task_id"),
            related_meeting_id=context.get("meeting_id"),
            generated_by=self.service_id,
        )
        
        self.reports[report.report_id] = report
        
        # 保存到文件
        self._save_report_to_file(report)
        
        # 存储到记忆
        self.memory.store_knowledge(
            key=f"report:{report.report_id}",
            value=report.to_dict(),
            tags=["report", f"template:{template_id}"],
            created_by=self.service_id,
        )
        
        # 发布报告生成事件
        event = Message(
            message_type=MessageType.EVENT_REPORT_GENERATED,
            source=self.service_id,
            topic="report_events",
            payload={"report_id": report.report_id, "title": report.title},
        )
        await self.network.publish(event)
        
        return report
    
    def _render_template(
        self,
        template: ReportTemplate,
        context: Dict[str, Any],
    ) -> str:
        """渲染模板"""
        lines = []
        
        # 标题
        title = context.get("title", "Report")
        lines.append(f"# {title}\n")
        
        # 生成时间
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        lines.append(f"Template: {template.name}\n")
        
        # 渲染各部分
        for section in template.sections:
            section_name = section.get("name", "Section")
            section_key = section.get("key", "")
            
            lines.append(f"\n## {section_name}\n")
            
            if section_key and section_key in context:
                value = context[section_key]
                if isinstance(value, dict):
                    for k, v in value.items():
                        lines.append(f"- **{k}**: {v}")
                elif isinstance(value, list):
                    for item in value:
                        lines.append(f"- {item}")
                else:
                    lines.append(str(value))
        
        # 如果没有预定义 sections，输出所有 context
        if not template.sections:
            lines.append("\n## Details\n")
            for key, value in context.items():
                if key not in ("title", "task_id", "meeting_id"):
                    lines.append(f"\n### {key}\n{value}\n")
        
        return "\n".join(lines)
    
    def _save_report_to_file(self, report: GeneratedReport) -> str:
        """保存报告到文件"""
        filename = f"{report.report_id}_{report.title[:30].replace(' ', '_')}.md"
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(report.content)
        
        return filepath
    
    # ========== 事件处理 ==========
    
    async def _handle_task_event(self, message: Message) -> None:
        """处理任务事件"""
        payload = message.payload
        task_id = payload.get("task_id")
        result = payload.get("result", {})
        status = result.get("status")
        
        # 根据状态选择模板
        if status == "completed":
            template = self._get_default_task_completion_template()
            await self.generate_report(
                template_id=template.template_id,
                context={
                    "title": f"Task Completion Report - {task_id}",
                    "task_id": task_id,
                    "status": status,
                    "results": result.get("results", []),
                },
            )
        
        elif status == "failed":
            template = self._get_default_task_failure_template()
            await self.generate_report(
                template_id=template.template_id,
                context={
                    "title": f"Task Failure Report - {task_id}",
                    "task_id": task_id,
                    "status": status,
                    "error": result.get("error", "Unknown error"),
                },
            )
    
    async def _handle_meeting_event(self, message: Message) -> None:
        """处理会议事件"""
        # 类似任务事件处理
        pass
    
    # ========== 默认模板 ==========
    
    def _get_default_task_completion_template(self) -> ReportTemplate:
        """获取默认任务完成模板"""
        template_id = "default_task_completion"
        
        if template_id not in self.templates:
            self.templates[template_id] = ReportTemplate(
                template_id=template_id,
                name="Task Completion Report",
                description="Default template for task completion",
                trigger_events=["task_completed"],
                sections=[
                    {"name": "Task Info", "key": "task_info"},
                    {"name": "Results", "key": "results"},
                    {"name": "Summary", "key": "summary"},
                ],
                output_format="markdown",
                version="1.0",
            )
        
        return self.templates[template_id]
    
    def _get_default_task_failure_template(self) -> ReportTemplate:
        """获取默认任务失败模板"""
        template_id = "default_task_failure"
        
        if template_id not in self.templates:
            self.templates[template_id] = ReportTemplate(
                template_id=template_id,
                name="Task Failure Report",
                description="Default template for task failure",
                trigger_events=["task_failed"],
                sections=[
                    {"name": "Task Info", "key": "task_info"},
                    {"name": "Error Details", "key": "error"},
                    {"name": "Recommendations", "key": "recommendations"},
                ],
                output_format="markdown",
                version="1.0",
            )
        
        return self.templates[template_id]
    
    # ========== 状态查询 ==========
    
    def get_report(self, report_id: str) -> Optional[GeneratedReport]:
        """获取报告"""
        return self.reports.get(report_id)
    
    def list_reports(self, limit: int = 20) -> List[Dict[str, Any]]:
        """列出报告"""
        sorted_reports = sorted(
            self.reports.values(),
            key=lambda r: r.generated_at,
            reverse=True,
        )
        return [r.to_dict() for r in sorted_reports[:limit]]
    
    def get_status(self) -> Dict[str, Any]:
        """获取服务状态"""
        return {
            "service_id": self.service_id,
            "templates_loaded": len(self.templates),
            "reports_generated": len(self.reports),
            "output_dir": self.output_dir,
        }
