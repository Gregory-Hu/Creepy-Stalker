# OpenHands Agent 框架 - 四层架构

基于 **显式任务状态机 + 任务清单驱动 + 原子执行技能** 的可控 Agent 框架，
采用清晰的分层架构设计，支持 MCP/A2A 协议，Skills 和 SOPs 由人类工程师用 Markdown 编写。

## 快速开始

### 1. 配置 API Key

**第一步：复制配置文件**

```bash
copy .env.example .env
```

**第二步：编辑 `.env` 文件，填入你的 DeepSeek API Key**

```bash
# LLM 配置
LLM_API_KEY=sk-your-deepseek-api-key-here
LLM_MODEL=deepseek/deepseek-chat
LLM_BASE_URL=https://api.deepseek.com
```

**第三步：验证配置**

```bash
python examples\deepseek_example.py
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 运行演示

```bash
python examples\full_system_demo.py
```

## 配置说明

### 环境变量 (.env 文件)

| 变量 | 描述 | 默认值 |
|------|------|--------|
| `LLM_API_KEY` | DeepSeek API Key | 必填 |
| `LLM_MODEL` | 模型名称 | `deepseek/deepseek-chat` |
| `LLM_BASE_URL` | API 端点 | `https://api.deepseek.com` |
| `WORKSPACE_DIR` | 工作目录 | `./workspace` |
| `MEMORY_STORAGE_PATH` | 记忆存储路径 | `./workspace/memory` |
| `REPORTS_DIR` | 报告输出目录 | `./reports` |

### 获取 DeepSeek API Key

1. 访问 [DeepSeek 开放平台](https://platform.deepseek.com/)
2. 注册/登录账号
3. 进入「API Keys」页面
4. 创建新的 API Key
5. 复制 API Key 到 `.env` 文件


```
┌─────────────────────────────────────────────────────────────┐
│                      应用层（Application Layer）              │
├───────────────┬───────────────┬─────────────────────────────┤
│  Orchestration│  Meeting       │  Reporting                  │
│  （编排协调）  │  （会议协作）  │  （报告生成）                │
├───────────────┴───────────────┴─────────────────────────────┤
│                      服务层（Service Layer）                  │
├─────────────────────────────────────────────────────────────┤
│  Execution Agents（执行智能体）                               │
│  - FileOperationAgent  - CodeAnalysisAgent  - DocumentAgent │
├─────────────────────────────────────────────────────────────┤
│                      记忆层（Memory Layer）                   │
├─────────────────────────────────────────────────────────────┤
│  Cognitive Memory      │  Notebook Memory                   │
│  （长期认知结果存储）  │  （短期任务状态记录）                │
├─────────────────────────────────────────────────────────────┤
│                    基础设施层（Infrastructure Layer）         │
├─────────────────────────────────────────────────────────────┤
│  Messaging Network（消息网络）                                │
│  （支持 MCP / A2A 协议，负责所有模块间通信）                  │
│  Module Registry（模块注册表）                                │
└─────────────────────────────────────────────────────────────┘
```

## 各层职责

### 基础设施层 (Infrastructure)

| 模块 | 职责 |
|------|------|
| **Messaging Network** | 消息总线，支持 MCP/A2A 协议，所有模块间通信 |
| **Module Registry** | 模块注册、发现、健康检查 |

### 记忆层 (Memory)

| 模块 | 职责 | 存储类型 |
|------|------|---------|
| **Cognitive Memory** | 长期认知结果（知识、模式、学习） | 持久化存储 |
| **Notebook Memory** | 短期任务状态（工作上下文、中间结果） | 临时缓存 |

### 服务层 (Services)

| 智能体 | 职责 | 技能 |
|--------|------|------|
| **FileOperationAgent** | 文件读写、搜索 | file_read, file_write, list_files |
| **CodeAnalysisAgent** | 代码结构、质量分析 | code_structure, code_quality |
| **DocumentAgent** | 文档生成、格式化 | report_generation, markdown_format |

### 应用层 (Application)

| 服务 | 职责 |
|------|------|
| **Orchestration** | 任务分解、智能体调度、进度跟踪 |
| **Meeting** | 多 Agent 协作、协商、投票、共识 |
| **Reporting** | 事件监听、报告生成、分发 |

## 项目结构

```
agent/
├── infra/                     # 基础设施层
│   ├── messaging.py           # 消息网络 (MCP/A2A)
│   └── registry.py            # 模块注册表
├── memory/                    # 记忆层
│   └── memory_service.py      # 记忆服务
├── services/                  # 服务层
│   └── execution_agents.py    # 执行智能体
├── application/               # 应用层
│   ├── orchestration.py       # 编排服务
│   ├── meeting.py             # 会议服务
│   └── reporting.py           # 报告服务
├── skills/                    # 技能定义 (Markdown)
│   ├── file_read.md
│   ├── file_write.md
│   ├── code_analysis.md
│   └── report_generation.md
├── sops/                      # 标准操作程序 (Markdown)
│   ├── code_development.md
│   ├── code_review.md
│   └── multi_agent_collaboration.md
├── examples/
│   └── full_system_demo.py    # 完整系统演示
└── workspace/                 # 工作目录
```

## 快速开始

### 1. 安装依赖

```bash
pip install pyyaml
```

### 2. 运行演示

```bash
python examples/full_system_demo.py
```

### 3. 查看报告

```bash
ls reports/
```

## 使用示例

### 提交任务

```python
from application import OrchestrationService

# 创建编排服务
orchestrator = OrchestrationService()

# 创建智能体
file_agent = orchestrator.create_agent("file_operation")
code_agent = orchestrator.create_agent("code_analysis")

# 提交任务
task_id = await orchestrator.submit_task({
    "name": "分析代码结构",
    "action": "analyze",
    "params": {"path": "src/main.py", "analysis_type": "structure"},
    "agent_type": "code_analysis",
})

# 执行任务
result = await orchestrator.execute_task(task_id)
```

### 发起多 Agent 会议

```python
from application import MeetingService

# 创建会议服务
meeting = MeetingService()

# 创建会议
agenda = meeting.create_meeting(
    topic="架构设计讨论",
    description="讨论新模块的架构设计",
    participants=["agent_1", "agent_2", "agent_3"],
)

# 开始会议
meeting.start_meeting(agenda.agenda_id)

# 提出方案
await meeting.propose(
    meeting_id=agenda.agenda_id,
    proposer_id="agent_1",
    proposal="采用微服务架构",
)

# 投票
await meeting.vote(
    meeting_id=agenda.agenda_id,
    voter_id="agent_2",
    proposal_id="proposal_1",
    vote_value="yes",
)

# 结束会议
meeting.end_meeting(agenda.agenda_id, outcome={"decision": "approved"})
```

### 生成报告

```python
from application import ReportingService

# 创建报告服务
reporting = ReportingService(output_dir="./reports")

# 生成报告
report = await reporting.generate_report(
    template_id="task_completion",
    context={
        "title": "任务完成报告",
        "task_id": "task_123",
        "status": "completed",
        "results": ["结果 1", "结果 2"],
    },
)

# 报告已保存到 ./reports/
```

## Skills 和 SOPs

### Skills（技能）

技能由人类工程师用 Markdown 编写，定义在 `skills/` 目录。

示例：`skills/file_read.md`

```markdown
---
skill_id: file_read
name: 文件读取技能
inputs:
  path:
    type: string
    required: true
outputs:
  content:
    type: string
---

# 文件读取技能

读取指定文件的内容...
```

### SOPs（标准操作程序）

SOP 由人类工程师用 Markdown 编写，定义在 `sops/` 目录。

示例：`sops/code_development.md`

```markdown
---
sop_id: code_development
name: 代码开发标准操作程序
steps:
  - step_id: 1
    name: 理解需求
    agent_type: file_operation
    action: read
    params:
      path: "requirements.md"
  - step_id: 2
    name: 分析现有代码
    agent_type: code_analysis
    action: analyze
    params:
      path: "src/"
---

# 代码开发 SOP

详细流程说明...
```

## 消息协议

### MCP（消息控制协议）

用于系统级消息：

| 消息类型 | 描述 |
|---------|------|
| `mcp.create_agent` | 创建智能体 |
| `mcp.start_task` | 启动任务 |
| `mcp.stop_task` | 停止任务 |
| `mcp.status_query` | 状态查询 |

### A2A（智能体间协议）

用于智能体协作：

| 消息类型 | 描述 |
|---------|------|
| `a2a.task_request` | 任务请求 |
| `a2a.task_response` | 任务响应 |
| `a2a.collaboration_request` | 协作请求 |
| `a2a.negotiation` | 协商 |
| `a2a.consensus` | 共识 |

## 设计理念

> **Agent 是一个被分配岗位与职责的执行实体。**
>
> 通过四层架构实现：
> - **基础设施层**：统一通信，模块解耦
> - **记忆层**：认知与状态分离，高效访问
> - **服务层**：可插拔智能体，专注功能
> - **应用层**：编排、协作、报告，业务逻辑
>
> **Skills 和 SOPs 由人类工程师编写**，确保可控性和可审计性。

## 参考资源

- [OpenHands 官方文档](https://docs.openhands.dev/)
- [GitHub 仓库](https://github.com/OpenHands/OpenHands)
