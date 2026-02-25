"""
角色定义：Manager / Expert / Senior / Junior

角色差异 = Orchestration 的复杂度 + Atomic Skill 的范围

这些是预定义的角色模板，可直接使用或自定义
"""
from typing import List, Dict, Any
from .agent_lifecycle import AgentRole, RoleDescription, OnboardingSpec


# ========== 预定义角色描述 ==========

def get_manager_role() -> RoleDescription:
    """
    Manager 角色
    
    特点：
    - 多任务、多 Agent、依赖多
    - 几乎不做具体执行
    - 负责任务分解和分配
    """
    return RoleDescription(
        role=AgentRole.MANAGER,
        name="项目 Manager",
        description="""
你是项目 Manager，负责协调多个 Agent 完成复杂项目。

你的职责：
1. 接收高层目标，分解为多个子任务
2. 将子任务分配给合适的 Agent（Expert/Senior/Junior）
3. 监控进度，处理依赖关系
4. 汇总结果，向上汇报

你不做具体执行工作，而是通过管理 Task 状态来推进项目。
""",
        # Orchestration 特点
        max_concurrent_tasks=10,
        supports_task_decomposition=True,
        requires_explicit_steps=False,
        
        # Atomic Skill 特点
        allowed_skills=[
            "ListFilesSkill",      # 查看项目结构
            "ReadFileSkill",       # 读取报告
            "WriteFileSkill",      # 写入计划
        ],
        restricted_skills=[
            "ExecuteCommandSkill",  # Manager 不执行命令
            "AnalyzeCodeSkill",     # Manager 不分析代码
        ],
        
        # 约束
        max_context_steps=5,
        requires_approval_for=[],
    )


def get_expert_role() -> RoleDescription:
    """
    Expert 角色
    
    特点：
    - 单大任务、强阶段性
    - 系统级分析
    - 需要深度专业知识
    """
    return RoleDescription(
        role=AgentRole.EXPERT,
        name="技术 Expert",
        description="""
你是技术 Expert，负责解决复杂的技术问题。

你的职责：
1. 接收一个大任务（如：设计一个新模块）
2. 分析需求，制定技术方案
3. 分阶段执行，每个阶段有明确的交付物
4. 遇到不确定性时，主动寻求澄清

你有较强的自主性，但需要在关键节点汇报进度。
""",
        # Orchestration 特点
        max_concurrent_tasks=3,
        supports_task_decomposition=True,
        requires_explicit_steps=True,
        
        # Atomic Skill 特点
        allowed_skills=[
            "ReadFileSkill",
            "WriteFileSkill",
            "ListFilesSkill",
            "SearchTextSkill",
            "AnalyzeCodeSkill",
            "ExecuteCommandSkill",
        ],
        restricted_skills=[],
        
        # 约束
        max_context_steps=20,
        requires_approval_for=[
            "ExecuteCommandSkill",  # 执行命令需要审批
        ],
    )


def get_senior_role() -> RoleDescription:
    """
    Senior 角色
    
    特点：
    - 单模块、弱生命周期
    - 模块级分析
    - 独立完成明确的任务
    """
    return RoleDescription(
        role=AgentRole.SENIOR,
        name="高级开发 Senior",
        description="""
你是高级开发工程师，负责完成具体的开发任务。

你的职责：
1. 接收明确的模块级任务
2. 按照既定规范完成实现
3. 保证代码质量
4. 遇到问题时主动沟通

你有中等的自主性，任务边界清晰。
""",
        # Orchestration 特点
        max_concurrent_tasks=2,
        supports_task_decomposition=False,
        requires_explicit_steps=True,
        
        # Atomic Skill 特点
        allowed_skills=[
            "ReadFileSkill",
            "WriteFileSkill",
            "ListFilesSkill",
            "SearchTextSkill",
            "AnalyzeCodeSkill",
            "ExecuteCommandSkill",
        ],
        restricted_skills=[],
        
        # 约束
        max_context_steps=10,
        requires_approval_for=[],
    )


def get_junior_role() -> RoleDescription:
    """
    Junior 角色
    
    特点：
    - 无 Orchestration
    - 极原子、强约束
    - 执行简单、明确的任务
    """
    return RoleDescription(
        role=AgentRole.JUNIOR,
        name="初级开发 Junior",
        description="""
你是初级开发工程师，负责执行简单、明确的任务。

你的职责：
1. 接收原子级的任务指令
2. 严格按照指令执行
3. 不自主决策，不自由发挥
4. 遇到任何不确定立即上报

你没有自主性，但执行效率高、可控性强。
""",
        # Orchestration 特点
        max_concurrent_tasks=1,
        supports_task_decomposition=False,
        requires_explicit_steps=True,
        
        # Atomic Skill 特点
        allowed_skills=[
            "ReadFileSkill",
            "WriteFileSkill",
            "ListFilesSkill",
        ],
        restricted_skills=[
            "ExecuteCommandSkill",  # Junior 不能执行命令
            "SearchTextSkill",      # Junior 不能搜索
        ],
        
        # 约束
        max_context_steps=3,
        requires_approval_for=[
            "WriteFileSkill",  # 写文件需要审批
        ],
    )


# ========== 预定义 SOP 模板 ==========

def get_coding_sop() -> List[Dict[str, Any]]:
    """编码任务的标准操作程序"""
    return [
        {
            "phase": "理解需求",
            "steps": [
                {"action": "read_files", "target": "需求文档"},
                {"action": "ask_clarification", "if": "需求不明确"},
            ]
        },
        {
            "phase": "设计方案",
            "steps": [
                {"action": "analyze_existing_code", "target": "相关模块"},
                {"action": "create_design_doc", "output": "DESIGN.md"},
            ]
        },
        {
            "phase": "实现代码",
            "steps": [
                {"action": "create_files", "pattern": "*.py"},
                {"action": "implement_logic"},
                {"action": "add_tests"},
            ]
        },
        {
            "phase": "代码审查",
            "steps": [
                {"action": "self_review"},
                {"action": "request_review", "target": "Senior/Expert"},
            ]
        },
    ]


def get_code_review_sop() -> List[Dict[str, Any]]:
    """代码审查的标准操作程序"""
    return [
        {
            "phase": "准备",
            "steps": [
                {"action": "read_pr_description"},
                {"action": "list_changed_files"},
            ]
        },
        {
            "phase": "审查",
            "steps": [
                {"action": "check_code_quality"},
                {"action": "check_security"},
                {"action": "check_performance"},
                {"action": "check_tests"},
            ]
        },
        {
            "phase": "反馈",
            "steps": [
                {"action": "write_review_comments"},
                {"action": "suggest_improvements"},
                {"action": "approve_or_request_changes"},
            ]
        },
    ]


# ========== 预定义任务模板 ==========

def get_feature_development_template() -> Dict[str, Any]:
    """功能开发任务模板"""
    return {
        "name": "功能开发",
        "description": "开发一个新功能",
        "completion_condition": "all_steps",
        "steps": [
            {
                "step_id": "understand_requirements",
                "name": "理解需求",
                "skill": "ReadFileSkill",
                "inputs": {"file_path": "requirements.md"},
            },
            {
                "step_id": "analyze_existing",
                "name": "分析现有代码",
                "skill": "AnalyzeCodeSkill",
                "inputs": {"file_path": "src/", "analysis_type": "structure"},
                "dependencies": ["understand_requirements"],
            },
            {
                "step_id": "implement",
                "name": "实现功能",
                "skill": "WriteFileSkill",
                "inputs": {},  # 动态填充
                "dependencies": ["analyze_existing"],
            },
            {
                "step_id": "test",
                "name": "编写测试",
                "skill": "WriteFileSkill",
                "inputs": {},
                "dependencies": ["implement"],
            },
        ],
    }


def get_bug_fix_template() -> Dict[str, Any]:
    """Bug 修复任务模板"""
    return {
        "name": "Bug 修复",
        "description": "分析并修复一个 Bug",
        "completion_condition": "all_steps",
        "steps": [
            {
                "step_id": "reproduce_bug",
                "name": "复现 Bug",
                "skill": "ExecuteCommandSkill",
                "inputs": {"command": "python test_bug.py"},
            },
            {
                "step_id": "locate_root_cause",
                "name": "定位根因",
                "skill": "SearchTextSkill",
                "inputs": {"directory": "src/", "pattern": "bug_related_code"},
                "dependencies": ["reproduce_bug"],
            },
            {
                "step_id": "fix",
                "name": "修复 Bug",
                "skill": "WriteFileSkill",
                "inputs": {},
                "dependencies": ["locate_root_cause"],
            },
            {
                "step_id": "verify",
                "name": "验证修复",
                "skill": "ExecuteCommandSkill",
                "inputs": {"command": "python test_bug.py"},
                "dependencies": ["fix"],
            },
        ],
    }


def get_code_review_template() -> Dict[str, Any]:
    """代码审查任务模板"""
    return {
        "name": "代码审查",
        "description": "审查一个 Pull Request",
        "completion_condition": "all_steps",
        "steps": [
            {
                "step_id": "read_pr",
                "name": "阅读 PR 描述",
                "skill": "ReadFileSkill",
                "inputs": {"file_path": "PR_DESCRIPTION.md"},
            },
            {
                "step_id": "list_changes",
                "name": "列出变更文件",
                "skill": "ListFilesSkill",
                "inputs": {"directory": "changed_files/"},
                "dependencies": ["read_pr"],
            },
            {
                "step_id": "review_each",
                "name": "逐个审查文件",
                "skill": "AnalyzeCodeSkill",
                "inputs": {},
                "dependencies": ["list_changes"],
            },
            {
                "step_id": "write_feedback",
                "name": "编写审查意见",
                "skill": "WriteFileSkill",
                "inputs": {},
                "dependencies": ["review_each"],
            },
        ],
    }


# ========== 便捷函数 ==========

def create_onboarding_spec(
    role: AgentRole,
    task_templates: List[Dict[str, Any]] = None,
    initial_tasks: List[Dict[str, Any]] = None,
) -> OnboardingSpec:
    """
    创建入职规范的便捷函数
    
    示例：
        spec = create_onboarding_spec(
            role=AgentRole.SENIOR,
            task_templates=[get_feature_development_template()],
            initial_tasks=[{...}]
        )
    """
    # 获取角色描述
    role_descriptions = {
        AgentRole.MANAGER: get_manager_role(),
        AgentRole.EXPERT: get_expert_role(),
        AgentRole.SENIOR: get_senior_role(),
        AgentRole.JUNIOR: get_junior_role(),
    }
    
    role_desc = role_descriptions.get(role, get_junior_role())
    
    # 默认任务模板
    if task_templates is None:
        task_templates = [
            get_feature_development_template(),
            get_bug_fix_template(),
        ]
    
    # 默认初始任务
    if initial_tasks is None:
        initial_tasks = []
    
    return OnboardingSpec(
        role_description=role_desc,
        sop_steps=get_coding_sop(),
        task_templates=task_templates,
        step_templates=[],
        initial_tasks=initial_tasks,
    )
