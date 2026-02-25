"""
简单 Agent 示例

运行此脚本前，请确保已设置环境变量:
export LLM_API_KEY="your-api-key"
"""
import os
from openhands.sdk import LLM, Conversation
from openhands.tools.preset.default import get_default_agent


def main():
    # 检查 API 密钥
    api_key = os.getenv("LLM_API_KEY")
    if not api_key:
        print("错误：请设置 LLM_API_KEY 环境变量")
        print("例如：export LLM_API_KEY='your-api-key'")
        return
    
    # 配置 LLM
    model = os.getenv("LLM_MODEL", "anthropic/claude-sonnet-4-5-20250929")
    print(f"使用模型：{model}")
    
    llm = LLM(
        model=model,
        api_key=api_key,
    )
    
    # 创建默认 Agent
    agent = get_default_agent(llm=llm, cli_mode=True)
    
    # 创建对话
    workspace = "./workspace"
    os.makedirs(workspace, exist_ok=True)
    
    conversation = Conversation(
        agent=agent,
        workspace=workspace,
    )
    
    # 发送任务
    task = "创建一个 Python 函数，计算斐波那契数列的前 n 项"
    print(f"\n任务：{task}\n")
    print("Agent 正在执行任务...\n")
    
    conversation.send_message(task)
    conversation.run()
    
    # 获取结果
    result = conversation.state.events[-1]
    if hasattr(result, "llm_message"):
        from openhands.sdk.llm import content_to_str
        content = "".join(content_to_str(result.llm_message.content))
        print("\n" + "="*60)
        print("执行结果:")
        print("="*60)
        print(content)
    
    print(f"\n累计成本：${llm.metrics.accumulated_cost:.4f}")
    print(f"文件已创建在：{workspace}")


if __name__ == "__main__":
    main()
