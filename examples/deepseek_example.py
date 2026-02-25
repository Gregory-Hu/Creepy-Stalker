"""
DeepSeek API 使用示例

演示如何使用配置好的 DeepSeek API Key 调用 LLM
"""
import asyncio
import os
import sys
import re

# 添加路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import load_config, get_config
from services import create_agent


def clean_emoji(text: str) -> str:
    """移除 emoji 和特殊 Unicode 字符"""
    # 移除常见的 emoji 范围
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # 表情符号
        "\U0001F300-\U0001F5FF"  # 符号和象形文字
        "\U0001F680-\U0001F6FF"  # 交通和地图符号
        "\U0001F1E0-\U0001F1FF"  # 国旗
        "\U00002702-\U000027B0"  # 装饰符号
        "\U0001F900-\U0001F9FF"  # 补充符号
        "\U00002070-\U0000207F"  # 上标数字
        "\U00002080-\U0000209F"  # 下标数字
        "\U00002150-\U0000218F"  # 数字形式
        "\U00002190-\U000021FF"  # 箭头
        "\U00002200-\U000022FF"  # 数学运算符
        "]+",
        flags=re.UNICODE
    )
    return emoji_pattern.sub('', text)


async def main():
    """主函数"""
    print("=" * 60)
    print("DeepSeek API 使用示例")
    print("=" * 60)
    
    # 1. 加载配置
    print("\n[1] 加载配置...")
    config = load_config(".env")
    
    if not config.is_llm_configured:
        print("\n❌ 错误：LLM API Key 未配置!")
        print("\n请按以下步骤配置:")
        print("1. 复制 .env.example 为 .env:")
        print("   copy .env.example .env")
        print("2. 编辑 .env 文件，填入你的 DeepSeek API Key:")
        print("   LLM_API_KEY=sk-your-actual-api-key")
        print("3. 重新运行此脚本")
        return
    
    print(f"    [OK] API Key 已配置：{config.llm_api_key[:10]}...")
    print(f"    [OK] 模型：{config.llm_model}")
    print(f"    [OK] API 端点：{config.llm_base_url}")
    
    # 2. 创建 LLM 智能体
    print("\n[2] 创建 LLM 智能体...")
    agent = create_agent("llm_chat", agent_id="deepseek_agent")
    print(f"    [OK] 智能体已创建 (ID: {agent.agent_id})")
    
    # 3. 测试对话
    print("\n[3] 测试对话...")
    print("-" * 60)
    
    test_messages = [
        "你好，请介绍一下自己。",
        "请用 Python 写一个快速排序算法。",
        "解释一下什么是注意力机制。",
    ]
    
    for message in test_messages:
        print(f"\n用户：{message}")
        response = await agent.chat(message)
        response = clean_emoji(response)
        print(f"AI: {response[:200]}..." if len(response) > 200 else f"AI: {response}")
        print("-" * 60)
    
    # 4. 执行任务
    print("\n[4] 执行任务示例...")
    
    tasks = [
        {
            "name": "代码分析",
            "prompt": "请分析这段代码的时间复杂度和空间复杂度：\n\ndef fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)",
            "system_message": "你是一个专业的代码分析专家。",
        },
        {
            "name": "文档生成",
            "prompt": "为一个 Python 函数编写文档字符串，函数功能是计算两个日期的天数差。",
            "system_message": "你是一个专业的技术文档 writer。",
        },
    ]
    
    for task in tasks:
        print(f"\n任务：{task['name']}")
        result = await agent.execute(task)
        
        if result.get("status") == "success":
            content = result.get("content", "")
            content = clean_emoji(content)
            print(f"结果：{content[:300]}..." if len(content) > 300 else f"结果：{content}")
        else:
            print(f"错误：{result.get('message', '未知错误')}")
        
        print("-" * 60)
    
    print("\n[OK] 演示完成!")


if __name__ == "__main__":
    asyncio.run(main())
