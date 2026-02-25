"""
芯片设计场景示例

演示如何使用多层 Agent 协作完成芯片设计任务：
- Manager: 协调整体流程
- Expert: 负责架构设计
- Senior: 负责模块实现
- Junior: 负责文档整理
"""
import os
import sys
from datetime import datetime

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import (
    create_agent,
    AgentRole,
    create_onboarding_spec,
    get_manager_role,
    get_expert_role,
    get_senior_role,
    get_junior_role,
    Signal,
)


# ========== 芯片设计任务模板 ==========

def get_chip_design_template() -> dict:
    """芯片设计任务模板"""
    return {
        "name": "芯片模块设计",
        "description": "设计一个芯片模块，包括架构、RTL 实现、验证",
        "completion_condition": "all_steps",
        "steps": [
            {
                "step_id": "spec_analysis",
                "name": "分析规格文档",
                "skill": "ReadFileSkill",
                "inputs": {"file_path": "specs/module_spec.md"},
            },
            {
                "step_id": "architecture_design",
                "name": "架构设计",
                "skill": "WriteFileSkill",
                "inputs": {
                    "file_path": "design/architecture.md",
                    "content": "# 架构设计文档\n...",
                },
                "dependencies": ["spec_analysis"],
            },
            {
                "step_id": "rtl_implementation",
                "name": "RTL 实现",
                "skill": "WriteFileSkill",
                "inputs": {},
                "dependencies": ["architecture_design"],
            },
            {
                "step_id": "testbench",
                "name": "编写 Testbench",
                "skill": "WriteFileSkill",
                "inputs": {},
                "dependencies": ["rtl_implementation"],
            },
            {
                "step_id": "simulation",
                "name": "仿真验证",
                "skill": "ExecuteCommandSkill",
                "inputs": {"command": "vsim -c testbench"},
                "dependencies": ["testbench"],
            },
            {
                "step_id": "synthesis",
                "name": "综合",
                "skill": "ExecuteCommandSkill",
                "inputs": {"command": "dc_shell -f synthesis.tcl"},
                "dependencies": ["simulation"],
            },
            {
                "step_id": "report",
                "name": "生成报告",
                "skill": "WriteFileSkill",
                "inputs": {},
                "dependencies": ["synthesis"],
            },
        ],
    }


def get_verification_template() -> dict:
    """验证任务模板"""
    return {
        "name": "模块验证",
        "description": "验证芯片模块功能正确性",
        "completion_condition": "all_steps",
        "steps": [
            {
                "step_id": "read_spec",
                "name": "阅读规格",
                "skill": "ReadFileSkill",
                "inputs": {"file_path": "specs/module_spec.md"},
            },
            {
                "step_id": "read_rtl",
                "name": "阅读 RTL 代码",
                "skill": "ReadFileSkill",
                "inputs": {"file_path": "rtl/module.v"},
                "dependencies": ["read_spec"],
            },
            {
                "step_id": "create_testplan",
                "name": "创建验证计划",
                "skill": "WriteFileSkill",
                "inputs": {},
                "dependencies": ["read_rtl"],
            },
            {
                "step_id": "create_testbench",
                "name": "创建 Testbench",
                "skill": "WriteFileSkill",
                "inputs": {},
                "dependencies": ["create_testplan"],
            },
            {
                "step_id": "run_simulation",
                "name": "运行仿真",
                "skill": "ExecuteCommandSkill",
                "inputs": {"command": "vcs -o simv testbench.v"},
                "dependencies": ["create_testbench"],
            },
            {
                "step_id": "coverage",
                "name": "覆盖率分析",
                "skill": "AnalyzeCodeSkill",
                "inputs": {"file_path": "coverage/", "analysis_type": "structure"},
                "dependencies": ["run_simulation"],
            },
        ],
    }


# ========== 创建各角色 Agent ==========

def create_manager_agent(workspace: str) -> "AgentLifecycleManager":
    """创建 Manager Agent"""
    from core.agent_lifecycle import AgentLifecycleManager, AgentConfig
    
    config = AgentConfig(
        role=AgentRole.MANAGER,
        name="芯片设计 Manager",
        workspace=workspace,
    )
    
    manager = AgentLifecycleManager.create(config)
    
    spec = create_onboarding_spec(
        role=AgentRole.MANAGER,
        task_templates=[
            get_chip_design_template(),
            get_verification_template(),
        ],
        initial_tasks=[
            {
                "name": "项目启动",
                "description": "启动芯片设计项目，协调各角色工作",
                "completion_condition": "all_steps",
                "steps": [
                    {
                        "step_id": "setup_workspace",
                        "name": "设置工作目录",
                        "skill": "ListFilesSkill",
                        "inputs": {"directory": workspace},
                    },
                    {
                        "step_id": "create_project_structure",
                        "name": "创建项目结构",
                        "skill": "WriteFileSkill",
                        "inputs": {
                            "file_path": f"{workspace}/PROJECT_PLAN.md",
                            "content": generate_project_plan(),
                        },
                    },
                ],
            },
        ],
    )
    
    manager.onboard(spec)
    return manager


def create_expert_agent(workspace: str) -> "AgentLifecycleManager":
    """创建 Expert Agent（架构设计）"""
    from core.agent_lifecycle import AgentLifecycleManager, AgentConfig
    
    config = AgentConfig(
        role=AgentRole.EXPERT,
        name="架构设计 Expert",
        workspace=workspace,
    )
    
    expert = AgentLifecycleManager.create(config)
    
    spec = create_onboarding_spec(
        role=AgentRole.EXPERT,
        task_templates=[get_chip_design_template()],
        initial_tasks=[
            {
                "name": "架构设计",
                "description": "根据规格文档设计芯片架构",
                "completion_condition": "all_steps",
                "steps": [
                    {
                        "step_id": "read_specs",
                        "name": "阅读规格文档",
                        "skill": "ReadFileSkill",
                        "inputs": {"file_path": f"{workspace}/specs/module_spec.md"},
                    },
                    {
                        "step_id": "design_architecture",
                        "name": "设计架构",
                        "skill": "WriteFileSkill",
                        "inputs": {
                            "file_path": f"{workspace}/design/architecture.md",
                            "content": generate_architecture_template(),
                        },
                        "dependencies": ["read_specs"],
                    },
                    {
                        "step_id": "review_architecture",
                        "name": "审查架构",
                        "skill": "AnalyzeCodeSkill",
                        "inputs": {
                            "file_path": f"{workspace}/design/architecture.md",
                            "analysis_type": "quality",
                        },
                        "dependencies": ["design_architecture"],
                    },
                ],
            },
        ],
    )
    
    expert.onboard(spec)
    return expert


def create_senior_agent(workspace: str) -> "AgentLifecycleManager":
    """创建 Senior Agent（RTL 实现）"""
    from core.agent_lifecycle import AgentLifecycleManager, AgentConfig
    
    config = AgentConfig(
        role=AgentRole.SENIOR,
        name="RTL 实现 Senior",
        workspace=workspace,
    )
    
    senior = AgentLifecycleManager.create(config)
    
    spec = create_onboarding_spec(
        role=AgentRole.SENIOR,
        task_templates=[get_chip_design_template()],
        initial_tasks=[
            {
                "name": "RTL 实现",
                "description": "根据架构设计实现 RTL 代码",
                "completion_condition": "all_steps",
                "steps": [
                    {
                        "step_id": "read_architecture",
                        "name": "阅读架构文档",
                        "skill": "ReadFileSkill",
                        "inputs": {"file_path": f"{workspace}/design/architecture.md"},
                    },
                    {
                        "step_id": "implement_rtl",
                        "name": "实现 RTL",
                        "skill": "WriteFileSkill",
                        "inputs": {
                            "file_path": f"{workspace}/rtl/module.v",
                            "content": generate_rtl_template(),
                        },
                        "dependencies": ["read_architecture"],
                    },
                    {
                        "step_id": "lint_check",
                        "name": "Linter 检查",
                        "skill": "AnalyzeCodeSkill",
                        "inputs": {
                            "file_path": f"{workspace}/rtl/module.v",
                            "analysis_type": "issues",
                        },
                        "dependencies": ["implement_rtl"],
                    },
                ],
            },
        ],
    )
    
    senior.onboard(spec)
    return senior


def create_junior_agent(workspace: str) -> "AgentLifecycleManager":
    """创建 Junior Agent（文档整理）"""
    from core.agent_lifecycle import AgentLifecycleManager, AgentConfig
    
    config = AgentConfig(
        role=AgentRole.JUNIOR,
        name="文档整理 Junior",
        workspace=workspace,
    )
    
    junior = AgentLifecycleManager.create(config)
    
    spec = create_onboarding_spec(
        role=AgentRole.JUNIOR,
        task_templates=[],
        initial_tasks=[
            {
                "name": "整理文档",
                "description": "整理项目文档",
                "completion_condition": "all_steps",
                "steps": [
                    {
                        "step_id": "list_docs",
                        "name": "列出文档",
                        "skill": "ListFilesSkill",
                        "inputs": {"directory": workspace, "pattern": "*.md"},
                    },
                    {
                        "step_id": "create_index",
                        "name": "创建索引",
                        "skill": "WriteFileSkill",
                        "inputs": {
                            "file_path": f"{workspace}/docs/README.md",
                            "content": generate_doc_index(),
                        },
                        "dependencies": ["list_docs"],
                    },
                ],
            },
        ],
    )
    
    junior.onboard(spec)
    return junior


# ========== 模板生成函数 ==========

def generate_project_plan() -> str:
    return f"""# 芯片设计项目计划

生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 项目结构

```
project/
├── specs/           # 规格文档
├── design/          # 设计文档
├── rtl/             # RTL 代码
├── tb/              # Testbench
├── sim/             # 仿真脚本
├── syn/             # 综合脚本
└── docs/            # 文档
```

## 里程碑

1. 架构设计完成
2. RTL 实现完成
3. 验证通过
4. 综合完成

## 角色分工

- Manager: 项目协调
- Expert: 架构设计
- Senior: RTL 实现
- Junior: 文档整理
"""


def generate_architecture_template() -> str:
    return """# 芯片模块架构设计

## 模块概述

### 功能描述
[描述模块的功能]

### 性能指标
- 频率目标：[XXX MHz]
- 面积目标：[XXX um²]
- 功耗目标：[XXX mW]

## 架构设计

### 顶层框图
```
+------------------+
|                  |
|   Module Name    |
|                  |
+------------------+
```

### 子模块划分
1. 子模块 A：功能描述
2. 子模块 B：功能描述

## 接口定义

### 输入信号
| 信号名 | 位宽 | 描述 |
|-------|------|------|
| clk   | 1    | 时钟 |
| rst_n | 1    | 复位 |

### 输出信号
| 信号名 | 位宽 | 描述 |
|-------|------|------|
| done  | 1    | 完成标志 |

## 时序图

[时序图描述]

## 设计考虑

### 面积优化
[优化策略]

### 功耗优化
[优化策略]

### 时序优化
[优化策略]
"""


def generate_rtl_template() -> str:
    return """module chip_module (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        start,
    output reg         done,
    // 其他端口
);

// ========== 参数定义 ==========
parameter WIDTH = 32;

// ========== 内部信号 ==========
reg [WIDTH-1:0] data_reg;
wire            valid;

// ========== 主逻辑 ==========
always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        done <= 1'b0;
        data_reg <= 'b0;
    end else begin
        if (start) begin
            // 实现逻辑
            done <= 1'b1;
        end else begin
            done <= 1'b0;
        end
    end
end

// ========== 输出赋值 ==========
assign valid = done;

endmodule
"""


def generate_doc_index() -> str:
    return f"""# 项目文档索引

生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 文档分类

### 规格文档
- [模块规格](../specs/module_spec.md)

### 设计文档
- [架构设计](../design/architecture.md)

### 实现文档
- [RTL 代码](../rtl/module.v)

### 验证文档
- [验证计划](tb/testplan.md)

## 更新历史

| 日期 | 作者 | 变更 |
|------|------|------|
| {datetime.now().strftime('%Y-%m-%d')} | Agent | 初始版本 |
"""


# ========== 主流程演示 ==========

def run_chip_design_demo():
    """运行芯片设计演示"""
    workspace = "./workspace/chip_design"
    os.makedirs(workspace, exist_ok=True)
    
    # 创建子目录
    for subdir in ["specs", "design", "rtl", "tb", "sim", "syn", "docs"]:
        os.makedirs(f"{workspace}/{subdir}", exist_ok=True)
    
    # 创建规格文档
    with open(f"{workspace}/specs/module_spec.md", "w") as f:
        f.write("""# 模块规格

## 功能
实现一个简单的 FIFO 缓冲区。

## 要求
- 深度：16
- 宽度：32 位
- 支持满/空标志
- 支持同时读写
""")
    
    print("=" * 60)
    print("芯片设计多 Agent 协作演示")
    print("=" * 60)
    
    # 创建各角色 Agent
    print("\n[1] 创建 Manager Agent...")
    manager = create_manager_agent(workspace)
    print(f"    状态：{manager.state.value}")
    
    print("\n[2] 创建 Expert Agent...")
    expert = create_expert_agent(workspace)
    print(f"    状态：{expert.state.value}")
    
    print("\n[3] 创建 Senior Agent...")
    senior = create_senior_agent(workspace)
    print(f"    状态：{senior.state.value}")
    
    print("\n[4] 创建 Junior Agent...")
    junior = create_junior_agent(workspace)
    print(f"    状态：{junior.state.value}")
    
    # 执行流程
    print("\n" + "=" * 60)
    print("执行流程")
    print("=" * 60)
    
    # Manager 先执行（创建项目计划）
    print("\n[Manager] 执行项目启动...")
    manager.start_execution()
    manager_results = manager.run_loop(max_steps=5)
    for result in manager_results:
        print(f"    → {result[:100]}...")
    
    # 发送信号给 Expert（项目计划已完成）
    print("\n[Signal] 发送 'project_started' 信号给 Expert...")
    expert.send_signal(Signal(name="project_started", source=manager.agent_id))
    
    # Expert 执行架构设计
    print("\n[Expert] 执行架构设计...")
    expert.start_execution()
    expert_results = expert.run_loop(max_steps=5)
    for result in expert_results:
        print(f"    → {result[:100]}...")
    
    # 发送信号给 Senior（架构设计已完成）
    print("\n[Signal] 发送 'architecture_completed' 信号给 Senior...")
    senior.send_signal(Signal(name="architecture_completed", source=expert.agent_id))
    
    # Senior 执行 RTL 实现
    print("\n[Senior] 执行 RTL 实现...")
    senior.start_execution()
    senior_results = senior.run_loop(max_steps=5)
    for result in senior_results:
        print(f"    → {result[:100]}...")
    
    # Junior 执行文档整理
    print("\n[Junior] 执行文档整理...")
    junior.start_execution()
    junior_results = junior.run_loop(max_steps=5)
    for result in junior_results:
        print(f"    → {result[:100]}...")
    
    # 汇总状态
    print("\n" + "=" * 60)
    print("最终状态")
    print("=" * 60)
    
    for agent in [manager, expert, senior, junior]:
        status = agent.get_status()
        print(f"\n{status['name']}:")
        print(f"    状态：{status['state']}")
        print(f"    完成任务：{status['completed_tasks']}")
        print(f"    失败任务：{status['failed_tasks']}")
    
    print(f"\n工作目录：{workspace}")
    print("=" * 60)


if __name__ == "__main__":
    run_chip_design_demo()
