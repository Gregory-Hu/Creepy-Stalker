"""
Orchestration Phase 完整示例

演示:
1. Agent 创建流程 (JD + Resource + Duty Skills)
2. Orchestration 启动流程 (Orchestration Skills)
"""
import os
import sys

# 添加路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orchestration import (
    get_agent_creator,
    get_jd_manager,
    ResourceBundle,
    Resource,
)


def main():
    """主函数"""
    print("=" * 70)
    print("Orchestration Phase 示例")
    print("=" * 70)
    
    # ========== Phase 1: Agent 创建 ==========
    print("\n" + "=" * 70)
    print("Phase 1: Agent 创建")
    print("=" * 70)
    
    # 1.1 获取创建器
    print("\n[1.1] 初始化 Agent 创建器...")
    creator = get_agent_creator()
    print("      [OK] Agent 创建器已初始化")
    
    # 1.2 查看可用的 JD
    print("\n[1.2] 查看可用的 JD...")
    jd_manager = get_jd_manager()
    jds = jd_manager.list_jds()
    print(f"      可用 JD ({len(jds)} 个):")
    for jd in jds:
        print(f"        - {jd['jd_id']}: {jd['name']} ({jd['role']})")
    
    # 1.3 创建资源包
    print("\n[1.3] 创建资源包...")
    workspace = "./workspace/demo_project"
    os.makedirs(workspace, exist_ok=True)
    
    # 创建示例资源
    resource_bundle = ResourceBundle(
        bundle_id="demo_resources",
        name="演示项目资源",
        description="演示项目所需资源",
        workspace=workspace,
    )
    
    # 添加代码资源
    src_dir = os.path.join(workspace, "src")
    os.makedirs(src_dir, exist_ok=True)
    resource_bundle.add_resource(Resource(
        resource_id="src_code",
        name="源代码",
        resource_type="code",
        path=src_dir,
        read_only=False,
        required=True,
        description="项目源代码目录",
    ))
    
    # 添加文档资源
    docs_dir = os.path.join(workspace, "docs")
    os.makedirs(docs_dir, exist_ok=True)
    resource_bundle.add_resource(Resource(
        resource_id="docs",
        name="文档",
        resource_type="document",
        path=docs_dir,
        read_only=True,
        required=True,
        description="项目文档",
    ))
    
    print(f"      [OK] 资源包已创建：{resource_bundle.name}")
    print(f"        - 工作空间：{workspace}")
    print(f"        - 资源数量：{len(resource_bundle.resources)}")
    
    # 1.4 创建 Agent
    print("\n[1.4] 创建 Agent...")
    print("      使用 JD: senior_python_dev")
    
    agent = creator.create_agent(
        jd_id="senior_python_dev",
        resource_bundle=resource_bundle,
        name="高级 Python 工程师 - Demo",
    )
    
    print(f"      [OK] Agent 已创建:")
    print(f"        - Agent ID: {agent.agent_id}")
    print(f"        - 名称：{agent.name}")
    print(f"        - JD: {agent.jd_id}")
    print(f"        - Role: {agent.jd.role if agent.jd else 'N/A'}")
    print(f"        - Duty Skills: {agent.duty_skills}")
    print(f"        - Orchestration Skills: {agent.orchestration_skills}")
    
    # ========== Phase 2: JD + Resource 快速浏览 ==========
    print("\n" + "=" * 70)
    print("Phase 2: JD + Resource 快速浏览")
    print("=" * 70)
    
    print("\n[2.1] 浏览 JD 摘要...")
    browse_result = creator.quick_browse(agent)
    
    jd_summary = browse_result["jd_summary"]
    print(f"      角色：{jd_summary.get('role', 'N/A')}")
    print(f"      名称：{jd_summary.get('name', 'N/A')}")
    print(f"      职责数量：{jd_summary.get('responsibilities_count', 0)}")
    print(f"      必需技能：{jd_summary.get('required_skills', [])}")
    print(f"      约束数量：{jd_summary.get('constraints_count', 0)}")
    
    print("\n[2.2] 浏览资源摘要...")
    resource_summary = browse_result["resource_summary"]
    print(f"      资源包：{resource_summary.get('bundle_name', 'N/A')}")
    print(f"      资源数量：{resource_summary.get('resources_count', 0)}")
    print(f"      工作空间：{resource_summary.get('workspace', 'N/A')}")
    print(f"      按类型：{resource_summary.get('by_type', {})}")
    
    print("\n[2.3] 技能加载状态...")
    print(f"      Duty Skills: {browse_result['duty_skills']}")
    print(f"      Orchestration Skills: {browse_result['orchestration_skills']}")
    
    # ========== Phase 3: Orchestration 启动 ==========
    print("\n" + "=" * 70)
    print("Phase 3: Orchestration 启动")
    print("=" * 70)
    
    print("\n[3.1] 启动 Orchestration...")
    print("      使用 Orchestration Skills 建立任务状态机...")
    
    # 定义初始任务
    initial_tasks = [
        {
            "task_id": "init_task_1",
            "name": "项目初始化",
            "description": "设置项目结构和基础配置",
            "priority": "high",
        },
        {
            "task_id": "init_task_2",
            "name": "代码审查",
            "description": "审查现有代码质量",
            "priority": "normal",
        },
    ]
    
    result = creator.start_orchestration(
        agent=agent,
        initial_tasks=initial_tasks,
    )
    
    if result.status == "success":
        print(f"      [OK] Orchestration 启动成功!")
        print(f"        - Agent ID: {result.agent_id}")
        print(f"        - 状态：{result.status}")
        print(f"        - 初始任务数：{len(result.initial_tasks)}")
        
        print("\n[3.2] 任务状态图...")
        task_graph = result.task_graph
        print(f"        - Agent: {task_graph['agent_id']}")
        print(f"        - Role: {task_graph['role']}")
        print(f"        - 状态：{task_graph['status']}")
        print(f"        - 任务列表:")
        for task in task_graph["tasks"]:
            status = task.get("status", "pending")
            print(f"          * {task['task_id']}: {task['name']} ({status})")
    else:
        print(f"      [ERROR] Orchestration 启动失败!")
        print(f"        - 错误：{result.error}")
    
    # ========== 完成 ==========
    print("\n" + "=" * 70)
    print("示例完成!")
    print("=" * 70)
    
    print("\n[流程总结]:")
    print("""
    ┌─────────────────────────────────────────────────────────────┐
    │ Phase 1: Agent 创建                                          │
    │  输入：JD + Resource Bundle                                   │
    │  加载：Duty Skills (按 Role)                                  │
    │  输出：AgentSpec                                             │
    ├─────────────────────────────────────────────────────────────┤
    │ Phase 2: JD + Resource 快速浏览                               │
    │  摘要：JD 职责、技能要求、约束                                  │
    │  摘要：资源类型、数量、位置                                    │
    │  输出：浏览报告                                              │
    ├─────────────────────────────────────────────────────────────┤
    │ Phase 3: Orchestration 启动                                   │
    │  输入：Orchestration Skills (按 Role)                         │
    │  建立：任务状态图                                             │
    │  创建：初始任务列表                                           │
    │  输出：AgentOnboardingResult                                 │
    └─────────────────────────────────────────────────────────────┘
    """)
    
    print("[创建的文件]:")
    print(f"   - 工作空间：{workspace}")
    print(f"   - 源代码目录：{src_dir}")
    print(f"   - 文档目录：{docs_dir}")


if __name__ == "__main__":
    main()
