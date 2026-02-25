---
skill_id: code_analysis
name: 代码分析技能
description: 分析代码结构、质量和潜在问题
version: 1.0
author: Human Engineer
tags:
  - code
  - analysis
  - quality

inputs:
  path:
    type: string
    description: 文件或目录路径
    required: true
  analysis_type:
    type: string
    description: 分析类型 (structure/quality/issues)
    required: true
    enum:
      - structure
      - quality
      - issues
  language:
    type: string
    description: 编程语言
    required: false
    default: python

outputs:
  analysis:
    type: object
    description: 分析结果
  summary:
    type: string
    description: 分析摘要
---

# 代码分析技能 (Code Analysis Skill)

## 技能说明

分析代码的结构、质量和潜在问题。支持多种分析类型。

## 分析类型

### 1. Structure（结构分析）

分析代码的组织结构：
- 类的定义
- 函数的定义
- 导入的模块
- 代码行数统计

### 2. Quality（质量分析）

评估代码质量：
- 函数长度检查
- 代码复杂度
- 命名规范
- 注释覆盖率

### 3. Issues（问题分析）

识别潜在问题：
- 裸 except 语句
- 硬编码字符串
- TODO/FIXME 标记
- 可能的安全漏洞

## 使用示例

### 结构分析

```yaml
action: analyze
params:
  path: "src/module.py"
  analysis_type: structure
```

### 质量检查

```yaml
action: analyze
params:
  path: "src/"
  analysis_type: quality
```

### 问题扫描

```yaml
action: analyze
params:
  path: "src/"
  analysis_type: issues
```

## 输出示例

### Structure 输出

```json
{
  "classes": ["MyClass", "HelperClass"],
  "functions": ["func1", "func2", "helper"],
  "total_lines": 250
}
```

### Quality 输出

```json
{
  "issues": [
    {"type": "long_function", "name": "process_data", "lines": 85}
  ],
  "score": 75
}
```

### Issues 输出

```json
{
  "issues": [
    {"line": 42, "type": "bare_except"},
    {"line": 108, "type": "todo", "content": "# TODO: refactor"}
  ]
}
```
