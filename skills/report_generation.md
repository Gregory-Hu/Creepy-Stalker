---
skill_id: report_generation
name: 报告生成技能
description: 根据模板和数据生成结构化报告
version: 1.0
author: Human Engineer
tags:
  - report
  - document
  - generation

inputs:
  template_id:
    type: string
    description: 报告模板 ID
    required: true
  data:
    type: object
    description: 报告数据
    required: true
  output_format:
    type: string
    description: 输出格式 (markdown/html/json)
    required: false
    default: markdown
  title:
    type: string
    description: 报告标题
    required: false

outputs:
  content:
    type: string
    description: 生成的报告内容
  path:
    type: string
    description: 保存的文件路径
  metadata:
    type: object
    description: 报告元数据
---

# 报告生成技能 (Report Generation Skill)

## 技能说明

根据预定义的模板和数据生成结构化报告。支持多种输出格式。

## 使用示例

### 生成任务完成报告

```yaml
action: generate_report
params:
  template_id: task_completion
  data:
    task_id: "task_123"
    task_name: "代码重构"
    status: completed
    results:
      - "重构了 5 个模块"
      - "提高了代码覆盖率到 85%"
  title: "任务完成报告 - task_123"
```

### 生成代码审查报告

```yaml
action: generate_report
params:
  template_id: code_review
  data:
    pr_id: "PR-456"
    reviewer: "Agent"
    findings:
      - type: bug
        severity: high
        description: "潜在的空指针异常"
      - type: suggestion
        severity: low
        description: "可以提取为公共函数"
  output_format: markdown
```

## 内置模板

| 模板 ID | 描述 |
|--------|------|
| task_completion | 任务完成报告 |
| task_failure | 任务失败报告 |
| code_review | 代码审查报告 |
| meeting_summary | 会议纪要 |
| daily_summary | 日报 |

## 输出格式

### Markdown

```markdown
# 报告标题

Generated: 2024-01-15 10:30:00

## 任务信息
- 任务 ID: task_123
- 状态：completed

## 结果
- 结果 1
- 结果 2
```

### HTML

```html
<html>
<head><title>报告标题</title></head>
<body>
<h1>报告标题</h1>
...
</body>
</html>
```

### JSON

```json
{
  "title": "报告标题",
  "generated_at": "2024-01-15T10:30:00",
  "sections": {...}
}
```
