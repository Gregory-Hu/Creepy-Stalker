---
skill_set_id: senior_orchestration_skills
role: senior
name: 高级工程师编排技能
description: |
  高级工程师自我编排工作所需的技能
  包括任务分解、进度管理、质量控制等

version: 1.0
author: Human Engineer
---

# Orchestration Skills: 高级工程师

## 技能概述

Orchestration Skills 是 Agent **自我编排**工作的能力，区别于 Duty Skills（完成具体职责的能力）。

| 维度 | Orchestration Skills | Duty Skills |
|------|---------------------|-------------|
| 目的 | 管理工作流程 | 完成具体任务 |
| 输出 | 计划、状态、进度 | 代码、文档、审查意见 |
| 时机 | 任务开始前和进行中 | 任务执行时 |

---

## 技能列表

### 1. Task Intake (任务接收)

**技能 ID**: `orch.task_intake`

**描述**: 接收和理解分配的任务

**子技能**:
| 子技能 | 描述 |
|--------|------|
| `parse_task_description` | 解析任务描述 |
| `identify_requirements` | 识别需求 |
| `clarify_ambiguity` | 澄清模糊点 |
| `estimate_effort` | 评估工作量 |

**输入**:
- 任务描述
- 需求文档
- 相关文件

**输出**:
- 任务理解摘要
- 问题列表（如有模糊）
- 工作量评估

**流程**:
```
1. 阅读任务描述
2. 识别关键需求
3. 检查相关文档
4. 列出模糊问题
5. 评估工作量
```

---

### 2. Task Decomposition (任务分解)

**技能 ID**: `orch.task_decompose`

**描述**: 将大任务分解为可执行的子任务

**子技能**:
| 子技能 | 描述 |
|--------|------|
| `identify_phases` | 识别阶段 |
| `define_subtasks` | 定义子任务 |
| `set_dependencies` | 设置依赖 |
| `estimate_subtask` | 估子任务工作量 |

**分解原则**:
- 每个子任务 < 4 小时
- 子任务有明确交付物
- 依赖关系清晰

**输出**:
```yaml
task_id: task_001
phases:
  - name: 设计
    subtasks:
      - id: 1.1
        name: 需求分析
        estimate: 1h
      - id: 1.2
        name: 架构设计
        estimate: 2h
  - name: 实现
    subtasks:
      - id: 2.1
        name: 核心功能
        estimate: 4h
      - id: 2.2
        name: 单元测试
        estimate: 2h
  - name: 文档
    subtasks:
      - id: 3.1
        name: API 文档
        estimate: 1h
```

---

### 3. Planning (规划)

**技能 ID**: `orch.planning`

**描述**: 制定执行计划

**子技能**:
| 子技能 | 描述 |
|--------|------|
| `prioritize_tasks` | 优先级排序 |
| `schedule_time` | 时间安排 |
| `identify_risks` | 识别风险 |
| `define_milestones` | 定义里程碑 |

**计划模板**:
```markdown
# 任务计划

## 目标
[任务目标]

## 里程碑
1. [日期] 完成设计
2. [日期] 完成实现
3. [日期] 完成测试

## 风险
- [风险 1] + 缓解措施
- [风险 2] + 缓解措施

## 依赖
- [依赖项]
```

---

### 4. Progress Tracking (进度跟踪)

**技能 ID**: `orch.progress_track`

**描述**: 跟踪任务进度

**子技能**:
| 子技能 | 描述 |
|--------|------|
| `update_status` | 更新状态 |
| `log_work` | 记录工作 |
| `identify_blockers` | 识别阻塞 |
| `report_progress` | 报告进度 |

**状态定义**:
| 状态 | 说明 |
|------|------|
| `pending` | 等待开始 |
| `in_progress` | 进行中 |
| `blocked` | 被阻塞 |
| `completed` | 已完成 |

**进度报告格式**:
```markdown
## 进度报告 - [日期]

### 已完成
- [ ] 任务 1
- [ ] 任务 2

### 进行中
- [ ] 任务 3 (50%)

### 阻塞
- [ ] 任务 4 - 等待 XX 反馈

### 下一步
- 继续任务 3
- 开始任务 5
```

---

### 5. Quality Control (质量控制)

**技能 ID**: `orch.quality_control`

**描述**: 确保工作质量

**子技能**:
| 子技能 | 描述 |
|--------|------|
| `self_review` | 自审 |
| `checklist_review` | 清单检查 |
| `define_done` | 完成定义检查 |

**检查清单**:
```markdown
## 完成定义 (DoD)

- [ ] 代码已实现
- [ ] 单元测试通过
- [ ] 代码已审查
- [ ] 文档已更新
- [ ] 无已知 Bug
```

---

### 6. Communication (沟通)

**技能 ID**: `orch.communication`

**描述**: 有效沟通

**子技能**:
| 子技能 | 描述 |
|--------|------|
| `ask_for_help` | 寻求帮助 |
| `provide_update` | 提供更新 |
| `escalate_issue` | 升级问题 |

---

## 完整工作流

```
┌─────────────────┐
│  Task Intake    │  接收任务
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│  Decomposition  │  分解任务
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│   Planning      │  制定计划
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│  Execution      │  执行 (使用 Duty Skills)
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│ Progress Track  │  跟踪进度
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│ Quality Control │  质量控制
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│  Communication  │  沟通报告
└─────────────────┘
```

---

## 与 Duty Skills 的配合

```
Orchestration Skills          Duty Skills
─────────────────           ────────────────
orch.task_intake            → 理解要做什么
orch.task_decompose         → 分解为步骤
orch.planning               → 安排顺序
                              ↓
                            duty.code_dev    (执行编码)
                            duty.code_review (执行审查)
                            duty.testing     (执行测试)
                              ↓
orch.progress_track         → 更新进度
orch.quality_control        → 质量检查
orch.communication          → 报告结果
```
