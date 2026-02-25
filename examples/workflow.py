"""
规划 + 执行工作流示例

演示如何使用两个 Agent 协作完成任务：
1. Planning Agent: 分析任务并创建详细实现计划
2. Execution Agent: 根据计划执行代码编写
"""
import os
import tempfile
from pathlib import Path

from openhands.sdk import LLM, Conversation
from openhands.sdk.llm import content_to_str
from openhands.tools.preset.default import get_default_agent
from openhands.tools.preset.planning import get_planning_agent


def get_event_content(event):
    """从事件中提取内容"""
    if hasattr(event, "llm_message"):
        return "".join(content_to_str(event.llm_message.content))
    return str(event)


def main():
    # 检查 API 密钥
    api_key = os.getenv("LLM_API_KEY")
    if not api_key:
        print("错误：请设置 LLM_API_KEY 环境变量")
        return
    
    # 配置 LLM
    model = os.getenv("LLM_MODEL", "anthropic/claude-sonnet-4-5-20250929")
    print(f"使用模型：{model}\n")
    
    llm = LLM(
        model=model,
        api_key=api_key,
        usage_id="agent",
    )
    
    # 创建临时工作区
    workspace_dir = Path(tempfile.mkdtemp())
    print(f"工作目录：{workspace_dir}\n")
    
    # 任务描述
    task = """
创建一个 Python 网页爬虫，要求：
- 从新闻网站抓取文章标题和 URL
- 使用重试逻辑优雅地处理 HTTP 错误
- 将结果保存到带时间戳的 JSON 文件
- 使用 requests 和 BeautifulSoup 库

请不要询问任何澄清问题，直接创建实现计划。
"""
    
    # ========== 阶段 1: 规划 ==========
    print("=" * 60)
    print("阶段 1: 规划 - 分析任务并创建实现计划")
    print("=" * 60)
    
    planning_agent = get_planning_agent(llm=llm)
    planning_conversation = Conversation(
        agent=planning_agent,
        workspace=str(workspace_dir),
    )
    
    print("\n规划 Agent 正在分析任务...\n")
    planning_conversation.send_message(
        f"请分析这个任务并创建详细的实现计划:\n\n{task}"
    )
    planning_conversation.run()
    
    planning_result = get_event_content(planning_conversation.state.events[-1])
    print("\n规划完成!")
    print(f"计划已保存到：{workspace_dir}/PLAN.md\n")
    
    # ========== 阶段 2: 执行 ==========
    print("=" * 60)
    print("阶段 2: 执行 - 根据计划实现代码")
    print("=" * 60)
    
    execution_agent = get_default_agent(llm=llm, cli_mode=True)
    execution_conversation = Conversation(
        agent=execution_agent,
        workspace=str(workspace_dir),
    )
    
    execution_prompt = f"""
请根据实现计划完成代码编写。

详细的实现计划已创建并保存在：{workspace_dir}/PLAN.md

请阅读计划文件，并按照计划实现所有功能。
"""
    
    print("\n执行 Agent 正在实现代码...\n")
    execution_conversation.send_message(execution_prompt)
    execution_conversation.run()
    
    # 获取结果
    execution_result = get_event_content(execution_conversation.state.events[-1])
    
    print("\n" + "=" * 60)
    print("执行结果:")
    print("=" * 60)
    print(execution_result)
    
    print(f"\n累计成本：${llm.metrics.accumulated_cost:.4f}")
    print(f"项目文件已创建在：{workspace_dir}")


if __name__ == "__main__":
    main()
