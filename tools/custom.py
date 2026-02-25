"""
自定义工具示例
"""
from openhands.sdk.tools import Tool, register_tool


@register_tool("HelloTool")
class HelloTool:
    """一个简单的问候工具示例"""
    
    name = "HelloTool"
    description = "返回一个友好的问候语"
    
    def execute(self, name: str = "World") -> str:
        """执行问候"""
        return f"Hello, {name}! Welcome to OpenHands!"
    
    @property
    def spec(self):
        """返回工具规格"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "要问候的名字",
                        "default": "World"
                    }
                }
            }
        }


# 你可以在这里添加更多自定义工具
# 例如：
# - 数据库查询工具
# - API 调用工具
# - 文件处理工具
# - 等等...
