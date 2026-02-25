---
sop_id: code_review
name: 代码审查标准操作程序
description: 对代码变更进行系统性审查的流程
version: 1.0
author: Human Engineer
tags:
  - review
  - quality
  - workflow

prerequisites:
  - 代码变更已完成
  - PR/MR 已创建

roles:
  - agent_type: code_analysis
    responsibility: 代码分析
  - agent_type: file_operation
    responsibility: 读取变更文件
  - agent_type: document
    responsibility: 生成审查报告

steps:
  - step_id: 1
    name: 获取变更列表
    description: 获取 PR/MR 中的变更文件列表
    agent_type: file_operation
    action: list
    params:
      directory: "changed_files/"
    output_key: changed_files
    
  - step_id: 2
    name: 阅读 PR 描述
    description: 理解变更目的和范围
    agent_type: file_operation
    action: read
    params:
      path: "PR_DESCRIPTION.md"
    output_key: pr_description
    
  - step_id: 3
    name: 逐个文件审查
    description: 对每个变更文件进行详细审查
    agent_type: code_analysis
    action: analyze
    params:
      path: "${changed_files[0]}"
      analysis_type: issues
    output_key: file_reviews
    dependencies:
      - 1
      - 2
    
  - step_id: 4
    name: 安全检查
    description: 检查潜在安全问题
    agent_type: code_analysis
    action: analyze
    params:
      path: "${changed_files[0]}"
      analysis_type: security
    output_key: security_review
    dependencies:
      - 3
    
  - step_id: 5
    name: 性能检查
    description: 检查潜在性能问题
    agent_type: code_analysis
    action: analyze
    params:
      path: "${changed_files[0]}"
      analysis_type: performance
    output_key: performance_review
    dependencies:
      - 3
    
  - step_id: 6
    name: 生成审查报告
    description: 汇总所有审查结果
    agent_type: document
    action: generate_report
    params:
      template_id: code_review
      data:
        pr_description: "${pr_description}"
        file_reviews: "${file_reviews}"
        security: "${security_review}"
        performance: "${performance_review}"
    output_key: review_report
    dependencies:
      - 4
      - 5
    
  - step_id: 7
    name: 给出审查结论
    description: 根据审查结果给出结论
    agent_type: document
    action: format_markdown
    params:
      content: "${review_report}"
    output_key: final_decision
    dependencies:
      - 6

conditions:
  - condition_id: has_critical_issues
    description: 是否有严重问题
    check: review_report.critical_issues.length > 0
    on_true: request_changes
    on_false: approve
  
  - condition_id: has_security_issues
    description: 是否有安全问题
    check: security_review.issues.length > 0
    on_true: request_changes
    on_false: proceed

completion_criteria:
  - 所有文件已审查
  - 审查报告已生成
  - 审查结论已给出

outputs:
  - review_report: 审查报告
  - final_decision: 审查结论 (approve/request_changes)
---

# 代码审查标准操作程序 (Code Review SOP)

## 流程概述

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ 1. 获取变更  │ ──→ │ 2. 阅读 PR  │ ──→ │ 3. 文件审查  │
└─────────────┘     └─────────────┘     └─────────────┘
                                              │
                    ┌─────────────────────────┼─────────────────────────┐
                    ↓                         ↓                         ↓
            ┌─────────────┐           ┌─────────────┐           ┌─────────────┐
            │  4. 安全检查  │           │ 5. 性能检查  │           │   ...       │
            └─────────────┘           └─────────────┘           └─────────────┘
                    │                         │
                    └───────────┬─────────────┘
                                ↓
                        ┌─────────────┐
                        │ 6. 生成报告  │
                        └─────────────┘
                                │
                                ↓
                        ┌─────────────┐
                        │ 7. 审查结论  │
                        └─────────────┘
```

## 审查维度

### 1. 代码质量

- [ ] 代码是否清晰易读
- [ ] 命名是否规范
- [ ] 函数是否过长
- [ ] 是否有重复代码

### 2. 功能正确性

- [ ] 是否实现需求
- [ ] 边界条件是否处理
- [ ] 错误处理是否完善

### 3. 安全性

- [ ] 是否有注入风险
- [ ] 敏感信息是否加密
- [ ] 权限检查是否到位

### 4. 性能

- [ ] 是否有性能瓶颈
- [ ] 是否有内存泄漏风险
- [ ] 算法复杂度是否合理

### 5. 测试

- [ ] 是否有单元测试
- [ ] 测试覆盖率是否足够
- [ ] 测试用例是否全面

## 审查结论

| 结论 | 条件 |
|------|------|
| Approve | 无严重问题，可以合并 |
| Request Changes | 有严重问题，需要修改 |
| Comment | 有建议，但不影响合并 |

## 审查报告模板

```markdown
# 代码审查报告

## PR 信息
- PR: #123
- 作者：@developer
- 变更：新增用户认证模块

## 审查结果

### 代码质量
评分：85/100
意见：整体良好，个别函数可优化

### 安全性
评分：90/100
意见：无明显安全问题

### 性能
评分：80/100
意见：循环内查询可优化

## 详细意见

1. [文件 1] 行 42: 建议提取为公共函数
2. [文件 2] 行 108: 缺少错误处理

## 结论

✅ Approve / ❌ Request Changes
```
