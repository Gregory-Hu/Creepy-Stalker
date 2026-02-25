---
skill_set_id: junior_duty_skills
role: junior
name: 初级工程师职责技能
description: |
  初级工程师完成职责所需的技能集合
  侧重基础开发和任务执行

version: 1.0
author: Human Engineer
---

# Duty Skills: 初级工程师

## 技能列表

### 1. Task Execution (任务执行)

**技能 ID**: `duty.task_exec`

**描述**: 执行分配的开发任务

**子技能**:
| 子技能 | 描述 |
|--------|------|
| `understand_requirement` | 理解任务需求 |
| `follow_spec` | 遵循规范 |
| `ask_questions` | 主动提问 |

**使用场景**:
- 功能开发
- Bug 修复
- 简单优化

---

### 2. Basic Coding (基础编码)

**技能 ID**: `duty.basic_coding`

**描述**: 基础代码编写能力

**子技能**:
| 子技能 | 描述 |
|--------|------|
| `read_existing_code` | 阅读现有代码 |
| `write_simple_function` | 编写简单函数 |
| `debug_basic` | 基础调试 |

**编码规范**:
```markdown
- 函数不超过 50 行
- 必须有注释
- 变量命名清晰
- 避免嵌套过深
```

**使用场景**:
- 简单功能实现
- 工具函数编写
- 测试代码编写

---

### 3. Testing (测试)

**技能 ID**: `duty.testing`

**描述**: 编写单元测试

**子技能**:
| 子技能 | 描述 |
|--------|------|
| `write_unit_test` | 编写单元测试 |
| `run_tests` | 运行测试 |
| `fix_failing_tests` | 修复失败测试 |

**测试要求**:
- 新功能必须有测试
- 测试覆盖率 > 80%
- 测试用例清晰

**使用场景**:
- 新功能测试
- 回归测试
- Bug 验证

---

### 4. Bug Fixing (Bug 修复)

**技能 ID**: `duty.bug_fix`

**描述**: 分析和修复 Bug

**子技能**:
| 子技能 | 描述 |
|--------|------|
| `reproduce_bug` | 复现 Bug |
| `locate_root_cause` | 定位根因 |
| `implement_fix` | 实施修复 |
| `verify_fix` | 验证修复 |

**修复流程**:
```
1. 复现 Bug
2. 定位问题
3. 设计修复方案
4. 实施修复
5. 验证修复
6. 提交审查
```

**使用场景**:
- Bug 修复
- 问题排查

---

### 5. Documentation (文档)

**技能 ID**: `duty.documentation`

**描述**: 基础文档编写

**子技能**:
| 子技能 | 描述 |
|--------|------|
| `comment_code` | 代码注释 |
| `update_api_doc` | 更新 API 文档 |
| `write_note` | 编写笔记 |

**使用场景**:
- 代码注释
- API 文档更新
- 学习笔记

---

## 技能组合使用

### 场景：功能开发

```
1. duty.task_exec.understand_requirement
   → 理解任务需求

2. duty.basic_coding.read_existing_code
   → 阅读相关代码

3. duty.basic_coding.write_simple_function
   → 实现功能

4. duty.testing.write_unit_test
   → 编写测试

5. duty.documentation.comment_code
   → 添加注释
```

### 场景：Bug 修复

```
1. duty.bug_fix.reproduce_bug
   → 复现 Bug

2. duty.bug_fix.locate_root_cause
   → 定位根因

3. duty.bug_fix.implement_fix
   → 实施修复

4. duty.testing.verify_fix
   → 验证修复

5. 提交审查
```

---

## 工作约束

| 约束 | 说明 |
|------|------|
| 代码审查 | 所有代码必须审查 |
| 权限限制 | 无生产环境权限 |
| 问题上报 | 不确定问题及时上报 |

---

## 技能熟练度要求

| 技能 | 要求熟练度 |
|------|-----------|
| Task Execution | 熟练 |
| Basic Coding | 熟练 |
| Testing | 基础 |
| Bug Fixing | 基础 |
| Documentation | 基础 |
