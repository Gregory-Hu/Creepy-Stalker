"""
代码编写 Agent
"""
from typing import List

from openhands.sdk import LLM

from .base import BaseAgent


class CoderAgent(BaseAgent):
    """专注于代码编写的 Agent"""
    
    def __init__(self, llm: LLM, name: str = "coder-agent"):
        super().__init__(llm=llm, name=name)
    
    def _default_system_prompt(self) -> str:
        return """你是一个专业的软件工程师助手。你的任务是帮助用户编写高质量、可维护的代码。

请遵循以下原则：
1. 编写简洁、可读性强的代码
2. 遵循最佳实践和设计模式
3. 添加必要的注释和文档
4. 考虑错误处理和边界情况
5. 优先使用标准库和成熟的第三方库

在编写代码前，先理解需求，如果有不清楚的地方，请先询问用户。"""
    
    def get_tools(self) -> List[str]:
        return [
            "GlobTool",      # 文件搜索
            "GrepTool",      # 内容搜索
            "FileEditorTool", # 文件编辑
            "BashTool",      # 执行命令
        ]
