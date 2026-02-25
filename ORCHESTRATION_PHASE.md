# OpenHands Agent 框架 - Orchestration Phase

## Orchestration Phase 流程

```
┌─────────────────────────────────────────────────────────────┐
│ Phase 1: Agent 创建                                           │
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
```

## 运行示例

```bash
# 激活虚拟环境
.\venv\Scripts\Activate.ps1

# 运行 Orchestration Phase 示例
python examples\orchestration_phase_demo.py
```

## 核心概念

### 1. JD (Job Description)

工作描述，定义 Agent 的角色、职责、要求等。

**位置**: `jd/`

**示例**:
```yaml
---
jd_id: senior_python_dev
role: senior
name: 高级 Python 开发工程师
responsibilities:
  - 负责 Python 后端服务的设计和开发
  - 参与代码审查，确保代码质量
requirements:
  required_skills:
    - python_programming
    - web_frameworks
---
```

### 2. Resource Bundle

资源包，包含 Agent 工作所需的各种资源。

**资源类型**:
| 类型 | 说明 |
|------|------|
| code | 代码目录 |
| document | 文档 |
| config | 配置文件 |
| tool | 工具 |
| api | API 访问 |

### 3. Duty Skills

职责技能，按 Role 分类，定义完成职责所需的能力。

**位置**: `duty_skills/`

**按 Role 分类**:
- `senior.md` - 高级工程师职责技能
- `junior.md` - 初级工程师职责技能

### 4. Orchestration Skills

编排技能，按 Role 分类，定义自我编排工作的能力。

**位置**: `orchestration_skills/`

**核心技能**:
| 技能 | 说明 |
|------|------|
| Task Intake | 任务接收 |
| Task Decomposition | 任务分解 |
| Planning | 规划 |
| Progress Tracking | 进度跟踪 |
| Quality Control | 质量控制 |

## 使用示例

### 创建 Agent

```python
from orchestration import get_agent_creator, ResourceBundle, Resource

# 获取创建器
creator = get_agent_creator()

# 创建资源包
resource_bundle = ResourceBundle(
    bundle_id="my_resources",
    name="我的资源",
    workspace="./workspace",
)

# 添加资源
resource_bundle.add_resource(Resource(
    resource_id="src_code",
    name="源代码",
    resource_type="code",
    path="./src",
    read_only=False,
    required=True,
))

# 创建 Agent
agent = creator.create_agent(
    jd_id="senior_python_dev",
    resource_bundle=resource_bundle,
    name="我的 Agent",
)
```

### 快速浏览

```python
# 浏览 JD 和资源
result = creator.quick_browse(agent)

print(result["jd_summary"])       # JD 摘要
print(result["resource_summary"]) # 资源摘要
```

### 启动 Orchestration

```python
# 定义初始任务
initial_tasks = [
    {
        "task_id": "task_1",
        "name": "项目初始化",
        "description": "设置项目结构",
        "priority": "high",
    },
]

# 启动 Orchestration
onboarding_result = creator.start_orchestration(
    agent=agent,
    initial_tasks=initial_tasks,
)

# 检查状态
if onboarding_result.status == "success":
    print("Orchestration 启动成功!")
    print(f"任务数：{len(onboarding_result.initial_tasks)}")
```

## 项目结构

```
agent/
├── orchestration/              # Orchestration 模块
│   ├── __init__.py
│   ├── jd.py                   # JD 管理
│   ├── resource_manager.py     # 资源管理
│   └── agent_lifecycle.py      # Agent 生命周期
├── jd/                         # Job Descriptions
│   ├── senior_python_dev.md
│   └── junior_developer.md
├── duty_skills/                # 职责技能 (按 Role)
│   ├── senior.md
│   └── junior.md
├── orchestration_skills/       # 编排技能 (按 Role)
│   ├── senior.md
│   └── junior.md
├── examples/
│   └── orchestration_phase_demo.py
└── ...
```

## Role 对比

| 维度 | Senior | Junior |
|------|--------|--------|
| Duty Skills | 开发、审查、设计、指导 | 任务执行、基础编码、测试 |
| Orchestration Skills | 完整任务分解、规划、质量控制 | 简单规划、状态报告 |
| 自主性 | 高 | 低 |
| 约束 | 重大变更需评审 | 所有代码需审查 |

## 下一步

Orchestration Phase 完成后，Agent 已具备：
1. ✅ 明确的职责 (JD)
2. ✅ 可用的资源 (Resource Bundle)
3. ✅ 职责技能 (Duty Skills)
4. ✅ 编排技能 (Orchestration Skills)
5. ✅ 任务状态图 (Task Graph)

接下来进入 **Execution Phase**，Agent 将使用 Duty Skills 执行具体任务。
