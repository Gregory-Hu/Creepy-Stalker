---
sop_id: code_development
name: 代码开发标准操作程序
description: 从需求到实现的完整代码开发流程
version: 1.0
author: Human Engineer
tags:
  - development
  - coding
  - workflow

prerequisites:
  - 需求文档已提供
  - 开发环境已配置

roles:
  - agent_type: code_analysis
    responsibility: 代码分析和审查
  - agent_type: file_operation
    responsibility: 文件读写
  - agent_type: document
    responsibility: 文档生成

steps:
  - step_id: 1
    name: 理解需求
    description: 阅读并理解需求文档
    agent_type: file_operation
    action: read
    params:
      path: "requirements.md"
    output_key: requirements_content
    
  - step_id: 2
    name: 分析现有代码
    description: 分析相关模块的现有代码结构
    agent_type: code_analysis
    action: analyze
    params:
      path: "src/"
      analysis_type: structure
    output_key: existing_structure
    dependencies:
      - 1
    
  - step_id: 3
    name: 设计方案
    description: 根据需求和现有结构设计方案
    agent_type: document
    action: generate_report
    params:
      template_id: design_doc
      data:
        requirements: "${requirements_content}"
        existing: "${existing_structure}"
    output_key: design_doc
    dependencies:
      - 1
      - 2
    
  - step_id: 4
    name: 实现代码
    description: 按照设计方案实现代码
    agent_type: file_operation
    action: write
    params:
      path: "src/new_module.py"
      content: "${design_doc.implementation}"
    dependencies:
      - 3
    
  - step_id: 5
    name: 代码审查
    description: 审查实现的代码
    agent_type: code_analysis
    action: analyze
    params:
      path: "src/new_module.py"
      analysis_type: quality
    output_key: review_result
    dependencies:
      - 4
    
  - step_id: 6
    name: 生成报告
    description: 生成开发完成报告
    agent_type: document
    action: generate_report
    params:
      template_id: task_completion
      data:
        task_type: code_development
        review: "${review_result}"
    dependencies:
      - 5

conditions:
  - condition_id: review_pass
    description: 代码审查通过
    check: review_result.issues.length == 0
    on_true: proceed_to_step_6
    on_false: return_to_step_4

completion_criteria:
  - 代码已实现
  - 代码审查通过
  - 报告已生成
---

# 代码开发标准操作程序 (Code Development SOP)

## 流程概述

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  1. 理解需求  │ ──→ │ 2. 分析现有  │ ──→ │  3. 设计方案  │
└─────────────┘     └─────────────┘     └─────────────┘
                                              │
                                              ↓
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  6. 生成报告  │ ←── │  5. 代码审查  │ ←── │  4. 实现代码  │
└─────────────┘     └─────────────┘     └─────────────┘
                          │
                          ↓
                    ┌─────────────┐
                    │ 审查通过？   │
                    └─────────────┘
                      │         │
                     是        否
                      │         │
                      ↓         ↓
                   继续      返回步骤 4
```

## 详细步骤说明

### 步骤 1: 理解需求

**目标**: 阅读需求文档，理解开发任务

**输入**: requirements.md

**输出**: 需求内容摘要

**执行 Agent**: FileOperationAgent

### 步骤 2: 分析现有代码

**目标**: 了解现有代码结构，避免重复造轮子

**输入**: src/ 目录

**输出**: 代码结构分析

**执行 Agent**: CodeAnalysisAgent

### 步骤 3: 设计方案

**目标**: 制定实现方案

**输入**: 需求内容 + 现有结构

**输出**: 设计文档

**执行 Agent**: DocumentAgent

### 步骤 4: 实现代码

**目标**: 按照设计实现功能

**输入**: 设计文档

**输出**: 新模块代码

**执行 Agent**: FileOperationAgent

### 步骤 5: 代码审查

**目标**: 确保代码质量

**输入**: 新实现的代码

**输出**: 审查结果

**执行 Agent**: CodeAnalysisAgent

**条件判断**: 
- 如果审查通过 → 步骤 6
- 如果审查不通过 → 返回步骤 4 修改

### 步骤 6: 生成报告

**目标**: 记录开发过程和结果

**输入**: 审查结果

**输出**: 完成报告

**执行 Agent**: DocumentAgent

## 异常处理

| 异常 | 处理方式 |
|------|---------|
| 需求文档不存在 | 终止流程，生成错误报告 |
| 现有代码分析失败 | 跳过步骤 2，直接设计 |
| 代码审查多次不通过 | 升级给人类工程师 |

## 质量指标

- 代码覆盖率 > 80%
- 无严重质量问题
- 文档完整
