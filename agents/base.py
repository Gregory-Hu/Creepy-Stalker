"""
基础 Agent 类定义
"""
from abc import ABC, abstractmethod
from typing import Optional, List

from openhands.sdk import LLM, Conversation


class BaseAgent(ABC):
    """自定义 Agent 基类"""
    
    def __init__(
        self,
        llm: LLM,
        name: str = "custom-agent",
        system_prompt: Optional[str] = None,
    ):
        self.llm = llm
        self.name = name
        self.system_prompt = system_prompt or self._default_system_prompt()
    
    @abstractmethod
    def _default_system_prompt(self) -> str:
        """返回默认的系统提示词"""
        pass
    
    @abstractmethod
    def get_tools(self) -> List[str]:
        """返回 Agent 可用的工具列表"""
        pass
    
    def create_conversation(self, workspace: str) -> Conversation:
        """创建对话实例"""
        from openhands.tools.preset.default import get_default_agent
        
        agent = get_default_agent(
            llm=self.llm,
            cli_mode=True,
        )
        
        return Conversation(
            agent=agent,
            workspace=workspace,
        )
    
    async def run(self, task: str, workspace: str) -> str:
        """运行 Agent 执行任务"""
        conversation = self.create_conversation(workspace)
        conversation.send_message(task)
        conversation.run()
        
        # 返回最后的事件内容
        result = conversation.state.events[-1]
        if hasattr(result, "llm_message"):
            from openhands.sdk.llm import content_to_str
            return "".join(content_to_str(result.llm_message.content))
        return str(result)
