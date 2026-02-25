"""
代码审查 Agent
"""
from typing import List

from openhands.sdk import LLM

from .base import BaseAgent


class ReviewerAgent(BaseAgent):
    """专注于代码审查的 Agent"""
    
    def __init__(self, llm: LLM, name: str = "reviewer-agent"):
        super().__init__(llm=llm, name=name)
    
    def _default_system_prompt(self) -> str:
        return """你是一个经验丰富的代码审查专家。你的任务是审查代码并提供建设性的反馈。

请从以下维度进行审查：
1. **代码质量**: 代码是否清晰、简洁、易于理解
2. **最佳实践**: 是否遵循了语言和框架的最佳实践
3. **潜在 Bug**: 识别可能的错误和边界情况
4. **安全性**: 检查安全漏洞和风险
5. **性能**: 识别性能瓶颈和优化机会
6. **可测试性**: 代码是否易于测试

提供具体、可操作的改进建议。"""
    
    def get_tools(self) -> List[str]:
        return [
            "GlobTool",      # 文件搜索
            "GrepTool",      # 内容搜索
            "FileReadTool",  # 文件读取
        ]
