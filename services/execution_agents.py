"""
服务层：Execution Agents（执行智能体）

执行具体功能的智能体集合，每个智能体负责一个特定的领域或任务。
它们是无状态的，通过消息网络接收任务并返回结果。
可插拔设计，新智能体只需注册到消息网络并遵循 A2A 协议即可加入系统。
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime
import uuid
import asyncio
import yaml
import os
import httpx

from infra import (
    Message, MessageType, MessagePriority,
    get_message_network, get_module_registry,
    ModuleType, ModuleStatus, ModuleInfo,
)
from config import get_config


@dataclass
class TaskDefinition:
    """
    任务定义
    
    从 Markdown 技能文件加载
    """
    task_id: str
    name: str
    description: str
    
    # 输入定义
    inputs: Dict[str, Any] = field(default_factory=dict)
    
    # 执行步骤（SOP）
    steps: List[Dict[str, Any]] = field(default_factory=list)
    
    # 输出定义
    outputs: Dict[str, Any] = field(default_factory=dict)
    
    # 元数据
    version: str = "1.0"
    tags: List[str] = field(default_factory=list)
    
    @classmethod
    def from_markdown(cls, markdown_path: str) -> "TaskDefinition":
        """从 Markdown 文件加载任务定义"""
        with open(markdown_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # 解析 YAML frontmatter
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                yaml_content = parts[1]
                body = parts[2].strip()
                
                data = yaml.safe_load(yaml_content) or {}
                
                return cls(
                    task_id=data.get("task_id", str(uuid.uuid4())[:8]),
                    name=data.get("name", "Unnamed Task"),
                    description=data.get("description", ""),
                    inputs=data.get("inputs", {}),
                    steps=data.get("steps", []),
                    outputs=data.get("outputs", {}),
                    version=data.get("version", "1.0"),
                    tags=data.get("tags", []),
                )
        
        # 没有 frontmatter，返回空定义
        return cls(
            task_id=str(uuid.uuid4())[:8],
            name=os.path.basename(markdown_path),
            description=content[:200],
        )


class ExecutionAgent(ABC):
    """
    执行智能体基类
    
    所有执行智能体必须继承此类
    """
    
    # 类变量，子类覆盖
    agent_type: str = "base_agent"
    description: str = "Base execution agent"
    
    def __init__(self, agent_id: Optional[str] = None):
        self.agent_id = agent_id or f"{self.agent_type}_{uuid.uuid4().hex[:8]}"
        self.status = ModuleStatus.REGISTERING
        
        # 能力列表
        self.capabilities: List[str] = []
        
        # 加载的技能
        self.skills: Dict[str, TaskDefinition] = {}
        
        # 当前任务
        self.current_task_id: Optional[str] = None
        self.task_history: List[Dict[str, Any]] = []
        
        # 消息网络
        self._network = None
    
    @property
    def network(self):
        """懒加载消息网络"""
        if self._network is None:
            self._network = get_message_network()
        return self._network
    
    # ========== 抽象方法 ==========
    
    @abstractmethod
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行任务
        
        子类必须实现此方法
        """
        pass
    
    # ========== 生命周期方法 ==========
    
    def register(self) -> None:
        """注册到模块注册表"""
        registry = get_module_registry()
        
        module_info = ModuleInfo(
            module_id=self.agent_id,
            module_type=ModuleType.EXECUTION_AGENT,
            name=self.agent_type,
            description=self.description,
            status=ModuleStatus.READY,
            capabilities=self.capabilities,
            config={
                "skills": list(self.skills.keys()),
            },
        )
        
        registry.register(module_info)
        self.status = ModuleStatus.READY
        
        # 注册消息处理器
        self._register_message_handlers()
    
    def unregister(self) -> None:
        """从注册表注销"""
        registry = get_module_registry()
        registry.unregister(self.agent_id)
        self.status = ModuleStatus.OFFLINE
    
    def _register_message_handlers(self) -> None:
        """注册消息处理器"""
        # 任务请求处理
        self.network.register_handler(
            MessageType.A2A_TASK_REQUEST,
            self._handle_task_request,
        )
        
        # 协作请求处理
        self.network.register_handler(
            MessageType.A2A_COLLABORATION_REQUEST,
            self._handle_collaboration_request,
        )
    
    # ========== 消息处理 ==========
    
    async def _handle_task_request(self, message: Message) -> Dict[str, Any]:
        """处理任务请求"""
        if message.target and message.target != self.agent_id:
            return {}
        
        task = message.payload.get("task", {})
        task_id = task.get("task_id", str(uuid.uuid4())[:8])
        
        # 更新状态
        self.status = ModuleStatus.BUSY
        self.current_task_id = task_id
        
        try:
            # 执行任务
            result = await self.execute(task)
            
            # 发送响应
            response = Message.task_response(
                source=self.agent_id,
                target=message.source,
                result={"status": "success", "data": result},
                correlation_id=message.message_id,
            )
            await self.network.respond(message, response)
            
            # 记录历史
            self.task_history.append({
                "task_id": task_id,
                "status": "completed",
                "timestamp": datetime.now().isoformat(),
            })
            
            return result
            
        except Exception as e:
            # 发送错误响应
            response = Message.task_response(
                source=self.agent_id,
                target=message.source,
                result={"status": "error", "message": str(e)},
                correlation_id=message.message_id,
            )
            await self.network.respond(message, response)
            
            self.task_history.append({
                "task_id": task_id,
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            })
            
            raise
        
        finally:
            self.status = ModuleStatus.READY
            self.current_task_id = None
    
    async def _handle_collaboration_request(self, message: Message) -> Dict[str, Any]:
        """处理协作请求"""
        context = message.payload.get("context", {})
        
        # 默认实现：简单响应
        response_data = {
            "agent_id": self.agent_id,
            "status": "available",
            "capabilities": self.capabilities,
        }
        
        response = Message(
            message_type=MessageType.A2A_COLLABORATION_RESPONSE,
            source=self.agent_id,
            target=message.source,
            payload={"response": response_data},
            correlation_id=message.message_id,
        )
        await self.network.respond(message, response)
        
        return response_data
    
    # ========== 技能管理 ==========
    
    def load_skill(self, skill_path: str) -> None:
        """加载技能文件"""
        task_def = TaskDefinition.from_markdown(skill_path)
        self.skills[task_def.task_id] = task_def
        
        # 更新能力列表
        if task_def.tags:
            self.capabilities.extend(task_def.tags)
    
    def load_skills_from_directory(self, skills_dir: str) -> int:
        """从目录加载所有技能文件"""
        count = 0
        if not os.path.exists(skills_dir):
            return 0
        
        for filename in os.listdir(skills_dir):
            if filename.endswith(".md"):
                skill_path = os.path.join(skills_dir, filename)
                self.load_skill(skill_path)
                count += 1
        
        return count
    
    def get_skill(self, skill_id: str) -> Optional[TaskDefinition]:
        """获取技能定义"""
        return self.skills.get(skill_id)
    
    # ========== 状态查询 ==========
    
    def get_status(self) -> Dict[str, Any]:
        """获取智能体状态"""
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "status": self.status.value,
            "capabilities": self.capabilities,
            "skills": list(self.skills.keys()),
            "current_task": self.current_task_id,
            "completed_tasks": len([t for t in self.task_history if t["status"] == "completed"]),
        }


# ========== 内置执行智能体 ==========

class FileOperationAgent(ExecutionAgent):
    """文件操作智能体"""
    
    agent_type = "file_operation"
    description = "负责文件读写、搜索等操作"
    
    def __init__(self, agent_id: Optional[str] = None):
        super().__init__(agent_id)
        self.capabilities = ["file_read", "file_write", "file_search", "list_files"]
        self.workspace = "./workspace"
    
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """执行文件操作任务"""
        action = task.get("action")
        params = task.get("params", {})
        
        if action == "read":
            return await self._read_file(params)
        elif action == "write":
            return await self._write_file(params)
        elif action == "list":
            return await self._list_files(params)
        elif action == "search":
            return await self._search_files(params)
        else:
            raise ValueError(f"Unknown action: {action}")
    
    async def _read_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """读取文件"""
        file_path = params.get("path")
        if not file_path:
            raise ValueError("Missing 'path' parameter")
        
        full_path = os.path.join(self.workspace, file_path.lstrip("/"))
        
        with open(full_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        return {"content": content, "lines": len(content.splitlines())}
    
    async def _write_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """写入文件"""
        file_path = params.get("path")
        content = params.get("content", "")
        
        if not file_path:
            raise ValueError("Missing 'path' parameter")
        
        full_path = os.path.join(self.workspace, file_path.lstrip("/"))
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        return {"status": "success", "path": file_path, "bytes": len(content)}
    
    async def _list_files(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """列出文件"""
        directory = params.get("directory", ".")
        pattern = params.get("pattern", "*")
        
        full_path = os.path.join(self.workspace, directory.lstrip("/"))
        
        import fnmatch
        files = []
        dirs = []
        
        for item in os.listdir(full_path):
            if fnmatch.fnmatch(item, pattern):
                item_path = os.path.join(full_path, item)
                if os.path.isdir(item_path):
                    dirs.append(item)
                else:
                    files.append(item)
        
        return {"directories": sorted(dirs), "files": sorted(files)}
    
    async def _search_files(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """搜索文件内容"""
        pattern = params.get("pattern")
        file_pattern = params.get("file_pattern", "*")
        
        if not pattern:
            raise ValueError("Missing 'pattern' parameter")
        
        results = []
        for root, dirs, filenames in os.walk(self.workspace):
            for filename in filenames:
                if fnmatch.fnmatch(filename, file_pattern):
                    file_path = os.path.join(root, filename)
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            for line_num, line in enumerate(f, 1):
                                if pattern.lower() in line.lower():
                                    results.append({
                                        "file": os.path.relpath(file_path, self.workspace),
                                        "line": line_num,
                                        "content": line.strip(),
                                    })
                    except (UnicodeDecodeError, PermissionError):
                        continue
        
        return {"matches": results[:50], "total": len(results)}


class CodeAnalysisAgent(ExecutionAgent):
    """代码分析智能体"""
    
    agent_type = "code_analysis"
    description = "负责代码结构分析、质量检查"
    
    def __init__(self, agent_id: Optional[str] = None):
        super().__init__(agent_id)
        self.capabilities = ["code_structure", "code_quality", "code_issues"]
    
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """执行代码分析任务"""
        action = task.get("action")
        params = task.get("params", {})
        
        if action == "structure":
            return await self._analyze_structure(params)
        elif action == "quality":
            return await self._analyze_quality(params)
        elif action == "issues":
            return await self._analyze_issues(params)
        else:
            raise ValueError(f"Unknown action: {action}")
    
    async def _analyze_structure(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """分析代码结构"""
        import re
        
        file_path = params.get("path")
        if not file_path:
            raise ValueError("Missing 'path' parameter")
        
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        classes = re.findall(r'^class\s+(\w+)', content, re.MULTILINE)
        functions = re.findall(r'^def\s+(\w+)', content, re.MULTILINE)
        
        return {
            "classes": classes,
            "functions": functions,
            "total_lines": len(content.splitlines()),
        }
    
    async def _analyze_quality(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """分析代码质量"""
        file_path = params.get("path")
        if not file_path:
            raise ValueError("Missing 'path' parameter")
        
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        issues = []
        
        # 检查长函数
        in_function = False
        function_start = 0
        function_name = ""
        
        for i, line in enumerate(lines, 1):
            if line.strip().startswith('def '):
                if in_function and i - function_start > 50:
                    issues.append({
                        "type": "long_function",
                        "name": function_name,
                        "lines": i - function_start,
                    })
                in_function = True
                function_start = i
                function_name = line.strip()
        
        return {"issues": issues, "total_lines": len(lines)}
    
    async def _analyze_issues(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """分析潜在问题"""
        import re
        
        file_path = params.get("path")
        if not file_path:
            raise ValueError("Missing 'path' parameter")
        
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        issues = []
        
        for i, line in enumerate(content.splitlines(), 1):
            # 裸 except
            if re.search(r'except\s*:', line):
                issues.append({"line": i, "type": "bare_except", "content": line.strip()})
            
            # TODO/FIXME
            if '# TODO' in line or '# FIXME' in line:
                issues.append({"line": i, "type": "todo", "content": line.strip()})
        
        return {"issues": issues}


class DocumentAgent(ExecutionAgent):
    """文档处理智能体"""
    
    agent_type = "document"
    description = "负责文档生成、格式化"
    
    def __init__(self, agent_id: Optional[str] = None):
        super().__init__(agent_id)
        self.capabilities = ["report_generation", "markdown_format", "summary"]
    
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """执行文档任务"""
        action = task.get("action")
        params = task.get("params", {})
        
        if action == "generate_report":
            return await self._generate_report(params)
        elif action == "format_markdown":
            return await self._format_markdown(params)
        elif action == "summarize":
            return await self._summarize(params)
        else:
            raise ValueError(f"Unknown action: {action}")
    
    async def _generate_report(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """生成报告"""
        title = params.get("title", "Report")
        sections = params.get("sections", [])
        
        content = [f"# {title}\n"]
        content.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        for section in sections:
            content.append(f"\n## {section.get('title', 'Section')}\n")
            content.append(section.get('content', ''))
        
        return {"content": "\n".join(content)}
    
    async def _format_markdown(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """格式化 Markdown"""
        content = params.get("content", "")
        # 简单格式化
        return {"formatted": content}
    
    async def _summarize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """生成摘要"""
        text = params.get("text", "")
        max_length = params.get("max_length", 200)
        
        summary = text[:max_length] + "..." if len(text) > max_length else text
        
        return {"summary": summary}


class LLMChatAgent(ExecutionAgent):
    """
    LLM 聊天智能体（使用 DeepSeek API）
    
    调用 DeepSeek API 进行对话、分析、生成等任务
    """
    
    agent_type = "llm_chat"
    description = "使用 DeepSeek API 进行智能对话和任务执行"
    
    def __init__(self, agent_id: Optional[str] = None):
        super().__init__(agent_id)
        self.capabilities = ["chat", "analysis", "generation", "reasoning"]
        
        # 加载配置
        config = get_config()
        self.api_key = config.llm_api_key
        self.model = config.llm_model
        self.base_url = config.llm_base_url
        
        # 对话历史（短期记忆）
        self.conversation_history: List[Dict[str, str]] = []
    
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """执行 LLM 任务"""
        config = get_config()
        
        # 检查 API Key
        if not config.is_llm_configured:
            return {
                "status": "error",
                "message": "LLM API Key 未配置，请在 .env 文件中配置 LLM_API_KEY",
            }
        
        prompt = task.get("prompt", task.get("description", ""))
        system_message = task.get("system_message", "你是一个有用的 AI 助手。")
        
        # 调用 DeepSeek API
        return await self._call_deepseek_api(system_message, prompt)
    
    async def _call_deepseek_api(
        self,
        system_message: str,
        user_message: str,
    ) -> Dict[str, Any]:
        """调用 DeepSeek API"""
        url = f"{self.base_url}/v1/chat/completions"
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        
        # 构建消息
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message},
        ]
        
        payload = {
            "model": self.model.replace("deepseek/", ""),  # 移除前缀
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 4096,
        }
        
        print(f"    [DEBUG] 请求 URL: {url}")
        print(f"    [DEBUG] 模型：{payload['model']}")
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(url, headers=headers, json=payload)
                
                # 打印响应状态
                print(f"    [DEBUG] 响应状态：{response.status_code}")
                
                if response.status_code != 200:
                    return {
                        "status": "error",
                        "message": f"API 错误 ({response.status_code}): {response.text[:200]}",
                    }
                
                response.raise_for_status()
                
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                
                return {
                    "status": "success",
                    "content": content,
                    "usage": data.get("usage", {}),
                }
                
        except httpx.HTTPError as e:
            return {
                "status": "error",
                "message": f"API 请求失败：{str(e)}",
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"调用 LLM 失败：{str(e)}",
            }
    
    async def chat(
        self,
        message: str,
        system_message: str = "你是一个有用的 AI 助手。",
    ) -> str:
        """对话接口"""
        result = await self.execute({
            "prompt": message,
            "system_message": system_message,
        })
        
        if result.get("status") == "success":
            return result.get("content", "")
        else:
            return f"错误：{result.get('message', '未知错误')}"


# ========== 工厂函数 ==========

def create_agent(agent_type: str, agent_id: Optional[str] = None) -> ExecutionAgent:
    """创建智能体"""
    agents = {
        "file_operation": FileOperationAgent,
        "code_analysis": CodeAnalysisAgent,
        "document": DocumentAgent,
        "llm_chat": LLMChatAgent,
    }

    agent_class = agents.get(agent_type)
    if not agent_class:
        raise ValueError(f"Unknown agent type: {agent_type}")

    return agent_class(agent_id)


def get_available_agent_types() -> List[str]:
    """获取可用的智能体类型"""
    return [
        "file_operation",
        "code_analysis",
        "document",
        "llm_chat",
    ]
