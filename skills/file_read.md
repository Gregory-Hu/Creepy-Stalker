---
skill_id: file_read
name: 文件读取技能
description: 读取文件内容并返回
version: 1.0
author: Human Engineer
tags:
  - file
  - read
  - io

inputs:
  path:
    type: string
    description: 文件路径
    required: true
  max_lines:
    type: integer
    description: 最大读取行数
    required: false
    default: 1000

outputs:
  content:
    type: string
    description: 文件内容
  lines:
    type: integer
    description: 读取的行数
  error:
    type: string
    description: 错误信息（如有）
---

# 文件读取技能 (File Read Skill)

## 技能说明

读取指定文件的内容，支持限制最大读取行数。

## 使用示例

### 读取整个文件

```yaml
action: read
params:
  path: "src/main.py"
```

### 读取前 100 行

```yaml
action: read
params:
  path: "src/main.py"
  max_lines: 100
```

## 执行步骤

1. 验证文件路径是否有效
2. 检查文件是否存在
3. 读取文件内容
4. 如果超过 max_lines，截断内容
5. 返回内容和元数据

## 错误处理

| 错误类型 | 处理方式 |
|---------|---------|
| 文件不存在 | 返回错误信息 |
| 权限不足 | 返回错误信息 |
| 编码错误 | 尝试其他编码或返回错误 |

## 注意事项

- 仅支持文本文件
- 大文件会被截断
- 二进制文件会返回错误
