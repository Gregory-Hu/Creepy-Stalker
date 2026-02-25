"""
完整系统演示：四层架构

演示如何使用完整的四层架构：
- 基础设施层：消息网络、模块注册
- 记忆层：认知记忆、笔记本记忆
- 服务层：执行智能体
- 应用层：编排、会议、报告
"""
import asyncio
import os
import sys

# 添加路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from infra import (
    get_message_network,
    get_module_registry,
    Message,
    MessageType,
    ModuleType,
)
from memory import get_memory_service, MemoryType
from services import create_agent, get_available_agent_types
from application import (
    OrchestrationService,
    MeetingService,
    ReportingService,
)


async def run_demo():
    """运行完整系统演示"""
    
    print("=" * 70)
    print("OpenHands Agent 框架 - 四层架构演示")
    print("=" * 70)
    
    # ========== 1. 初始化基础设施层 ==========
    print("\n[1] 初始化基础设施层...")
    
    network = get_message_network()
    registry = get_module_registry()
    
    print(f"    ✓ 消息网络已初始化")
    print(f"    ✓ 模块注册表已初始化")
    
    # ========== 2. 初始化记忆层 ==========
    print("\n[2] 初始化记忆层...")
    
    memory = get_memory_service(storage_path="./workspace/memory")
    print(f"    ✓ 记忆服务已初始化 (路径：./workspace/memory)")
    
    # ========== 3. 初始化服务层 ==========
    print("\n[3] 初始化服务层（执行智能体）...")
    
    available_agents = get_available_agent_types()
    print(f"    可用智能体类型：{available_agents}")
    
    # ========== 4. 初始化应用层 ==========
    print("\n[4] 初始化应用层...")
    
    # 编排服务
    orchestration = OrchestrationService()
    print(f"    ✓ 编排服务已初始化 (ID: {orchestration.orchestrator_id})")
    
    # 会议服务
    meeting = MeetingService()
    print(f"    ✓ 会议服务已初始化 (ID: {meeting.service_id})")
    
    # 报告服务
    reporting = ReportingService(output_dir="./reports")
    print(f"    ✓ 报告服务已初始化 (ID: {reporting.service_id})")
    
    # ========== 5. 加载 SOP ==========
    print("\n[5] 加载 SOP...")
    
    sops_dir = os.path.join(os.path.dirname(__file__), "..", "sops")
    if os.path.exists(sops_dir):
        for filename in os.listdir(sops_dir):
            if filename.endswith(".md"):
                sop = orchestration.load_sop(os.path.join(sops_dir, filename))
                print(f"    ✓ 加载 SOP: {sop.name}")
    
    # ========== 6. 创建执行智能体 ==========
    print("\n[6] 创建执行智能体...")
    
    file_agent = orchestration.create_agent("file_operation")
    print(f"    ✓ 文件操作智能体 (ID: {file_agent.agent_id})")
    
    code_agent = orchestration.create_agent("code_analysis")
    print(f"    ✓ 代码分析智能体 (ID: {code_agent.agent_id})")
    
    doc_agent = orchestration.create_agent("document")
    print(f"    ✓ 文档智能体 (ID: {doc_agent.agent_id})")
    
    # ========== 7. 提交任务 ==========
    print("\n[7] 提交任务...")
    
    # 任务 1: 读取文件
    task1_id = await orchestration.submit_task({
        "name": "读取配置文件",
        "action": "read",
        "params": {"path": "config.example.toml"},
        "agent_type": "file_operation",
    })
    print(f"    ✓ 任务 1 已提交 (ID: {task1_id})")
    
    # 任务 2: 分析代码
    task2_id = await orchestration.submit_task({
        "name": "分析代码结构",
        "action": "analyze",
        "params": {
            "path": os.path.join(os.path.dirname(__file__), "orchestration.py"),
            "analysis_type": "structure",
        },
        "agent_type": "code_analysis",
    })
    print(f"    ✓ 任务 2 已提交 (ID: {task2_id})")
    
    # 任务 3: 生成报告
    task3_id = await orchestration.submit_task({
        "name": "生成系统状态报告",
        "action": "generate_report",
        "params": {
            "template_id": "default_task_completion",
            "data": {
                "system": "OpenHands Agent Framework",
                "status": "running",
                "components": {
                    "orchestration": "active",
                    "meeting": "active",
                    "reporting": "active",
                }
            },
        },
        "agent_type": "document",
    })
    print(f"    ✓ 任务 3 已提交 (ID: {task3_id})")
    
    # ========== 8. 执行任务 ==========
    print("\n[8] 执行任务...")
    
    # 获取任务计划
    for task_id in [task1_id, task2_id, task3_id]:
        plan = orchestration.task_plans.get(task_id)
        if plan:
            result = await orchestration.execute_plan(plan)
            status = result.get("status", "unknown")
            print(f"    → 任务 {task_id}: {status}")
    
    # ========== 9. 查询状态 ==========
    print("\n[9] 系统状态...")
    
    print(f"\n    编排服务状态:")
    orch_status = orchestration.get_status()
    for key, value in orch_status.items():
        print(f"      - {key}: {value}")
    
    print(f"\n    报告服务状态:")
    rep_status = reporting.get_status()
    for key, value in rep_status.items():
        print(f"      - {key}: {value}")
    
    print(f"\n    模块注册表状态:")
    reg_stats = registry.get_stats()
    print(f"      - 总模块数：{reg_stats['total_modules']}")
    print(f"      - 按类型：{reg_stats['by_type']}")
    
    print(f"\n    记忆服务状态:")
    mem_stats = memory.store.get_stats()
    print(f"      - 总条目数：{mem_stats['total_entries']}")
    print(f"      - 认知记忆：{mem_stats['cognitive_count']}")
    print(f"      - 笔记本记忆：{mem_stats['notebook_count']}")
    
    # ========== 10. 生成最终报告 ==========
    print("\n[10] 生成演示报告...")
    
    report = await reporting.generate_report(
        template_id="default_task_completion",
        context={
            "title": "系统演示报告",
            "task_id": "demo_run",
            "status": "completed",
            "results": [
                f"创建了 {orch_status['managed_agents']} 个智能体",
                f"执行了 {len(orchestration.task_plans)} 个任务",
                f"加载了 {orch_status['sops_loaded']} 个 SOP",
            ],
        },
    )
    print(f"    ✓ 报告已生成 (ID: {report.report_id})")
    print(f"    ✓ 报告已保存到：{reporting.output_dir}/")
    
    # ========== 完成 ==========
    print("\n" + "=" * 70)
    print("演示完成!")
    print("=" * 70)
    
    # 清理
    print("\n清理资源...")
    orchestration.stop()
    network.stop()
    
    print("✓ 所有服务已停止")


def main():
    """主函数"""
    # 创建工作目录
    os.makedirs("./workspace", exist_ok=True)
    os.makedirs("./workspace/memory", exist_ok=True)
    os.makedirs("./reports", exist_ok=True)
    os.makedirs("./skills", exist_ok=True)
    os.makedirs("./sops", exist_ok=True)
    
    # 运行演示
    asyncio.run(run_demo())


if __name__ == "__main__":
    main()
