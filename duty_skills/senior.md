---
skill_set_id: senior_duty_skills
role: senior
name: 高级工程师职责技能
description: |
  高级工程师完成职责所需的技能集合
  包括开发、审查、设计等核心能力

version: 1.0
author: Human Engineer
---

# Duty Skills: 高级工程师

## 技能列表

### 1. Code Development (代码开发)

**技能 ID**: `duty.code_dev`

**描述**: 高质量代码开发能力

**子技能**:
| 子技能 | 描述 |
|--------|------|
| `design_before_code` | 编码前先设计 |
| `test_driven` | 测试驱动开发 |
| `refactor_safely` | 安全重构 |

**使用场景**:
- 新功能开发
- 模块重构
- 性能优化

---

### 2. Code Review (代码审查)

**技能 ID**: `duty.code_review`

**描述**: 系统性代码审查能力

**子技能**:
| 子技能 | 描述 |
|--------|------|
| `review_architecture` | 架构审查 |
| `review_security` | 安全检查 |
| `review_performance` | 性能检查 |
| `review_style` | 风格规范检查 |

**审查清单**:
```markdown
- [ ] 代码逻辑正确
- [ ] 无安全隐患
- [ ] 性能合理
- [ ] 符合规范
- [ ] 有单元测试
- [ ] 文档完整
```

**使用场景**:
- PR 审查
- 代码质量检查
- 安全审计

---

### 3. System Design (系统设计)

**技能 ID**: `duty.system_design`

**描述**: 系统架构设计能力

**子技能**:
| 子技能 | 描述 |
|--------|------|
| `requirement_analysis` | 需求分析 |
| `architecture_design` | 架构设计 |
| `interface_design` | 接口设计 |
| `data_modeling` | 数据建模 |

**设计产出**:
- 架构文档
- 接口定义
- 数据模型
- 部署方案

**使用场景**:
- 新项目启动
- 系统重构
- 技术方案评审

---

### 4. Documentation (文档编写)

**技能 ID**: `duty.documentation`

**描述**: 技术文档编写能力

**子技能**:
| 子技能 | 描述 |
|--------|------|
| `api_doc` | API 文档 |
| `design_doc` | 设计文档 |
| `user_guide` | 用户指南 |
| `tech_spec` | 技术规格 |

**使用场景**:
- 新功能文档
- API 文档更新
- 技术方案记录

---

### 5. Mentoring (指导)

**技能 ID**: `duty.mentoring`

**描述**: 指导初级工程师的能力

**子技能**:
| 子技能 | 描述 |
|--------|------|
| `code_review_feedback` | 审查反馈 |
| `tech_guidance` | 技术指导 |
| `best_practices` | 最佳实践传授 |

**使用场景**:
- 代码审查反馈
- 技术分享
- 问题解答

---

## 技能组合使用

### 场景：新功能开发

```
1. duty.system_design.requirement_analysis
   → 分析需求，明确目标

2. duty.system_design.architecture_design
   → 设计架构，产出文档

3. duty.code_dev
   → 按照设计编码

4. duty.code_review
   → 自审代码

5. duty.documentation
   → 编写文档
```

### 场景：代码审查

```
1. duty.code_review.review_architecture
   → 审查架构合理性

2. duty.code_review.review_security
   → 检查安全隐患

3. duty.code_review.review_performance
   → 检查性能问题

4. duty.mentoring.code_review_feedback
   → 给出建设性反馈
```

---

## 技能熟练度要求

| 技能 | 要求熟练度 |
|------|-----------|
| Code Development | 专家 |
| Code Review | 专家 |
| System Design | 熟练 |
| Documentation | 熟练 |
| Mentoring | 熟练 |
