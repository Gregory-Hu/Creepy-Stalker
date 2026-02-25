---
skill_id: file_write
name: 文件写入技能
description: 创建或覆盖文件
version: 1.0
author: Human Engineer
tags:
  - file
  - write
  - io

inputs:
  path:
    type: string
    description: 文件路径
    required: true
  content:
    type: string
    description: 文件内容
    required: true
  create_dirs:
    type: boolean
    description: 是否自动创建目录
    required: false
    default: true

outputs:
  status:
    type: string
    description: 执行状态 (success/error)
  path:
    type: string
    description: 写入的文件路径
  bytes:
    type: integer
    description: 写入的字节数
  error:
    type: string
    description: 错误信息（如有）
---

# 文件写入技能 (File Write Skill)

## 技能说明

创建新文件或覆盖已存在的文件。支持自动创建目录结构。

## 使用示例

### 创建文件

```yaml
action: write
params:
  path: "output/result.txt"
  content: "Hello, World!"
```

### 创建带目录的文件

```yaml
action: write
params:
  path: "reports/2024/january.md"
  content: "# Report\n\nContent here..."
  create_dirs: true
```

## 执行步骤

1. 验证文件路径
2. 如果 create_dirs=true，创建必要的目录
3. 写入文件内容
4. 返回写入结果

## 错误处理

| 错误类型 | 处理方式 |
|---------|---------|
| 路径无效 | 返回错误信息 |
| 权限不足 | 返回错误信息 |
| 磁盘空间不足 | 返回错误信息 |

## 安全注意事项

- 会覆盖已存在的文件
- 不会写入敏感目录（/etc, /system 等）
- 内容会被验证
