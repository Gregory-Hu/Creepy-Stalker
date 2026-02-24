
# Agent架构设计

“显式任务状态机 + 任务清单驱动 + 原子执行技能”

```
【自我管理层】   ← orchestration skills（任务生命周期）
【任务层】       ← step / task（像日程表）
【执行层】       ← atomic skills（怎么把一步做好）
```

这三层 必须严格解耦

核心原理是不断让Agent行为可控，给人类专家提供一种相对便捷的agent编排方式
- 不需要“全局反思”
  - 消除
    - “我现在在干嘛？”
    - “接下来做什么？”
  - 这些都在 状态里
- 上下文不会无限增长
  - Orchestration Skill 只看：
    - task state
    - step list
  - Atomic Skill 只看：
    - 当前 step 的 inputs
- 不依赖“通用智能自我编排”
  - 把“自我编排”提前工程化
  - 把“智能”限制在局部、短时、目标明确的地方
  ‘
这样上下文是分片的，而不是累积的

在这套架构里
- 角色差异 ≠ 智能差异
- 角色差异 = Orchestration 的复杂度 + Atomic Skill 的范围

以芯片设计为例
| 角色      | Orchestration 特点 | Atomic Skill 特点 |
| ------- | ---------------- | --------------- |
| Manager | 多任务、多 Agent、依赖多  | 几乎不做具体执行        |
| Expert  | 单大任务、强阶段性        | 系统级分析           |
| Senior  | 单模块、弱生命周期        | 模块级分析           |
| Junior  | 无 Orchestration  | 极原子、强约束         |

再强调一遍可控性，为了让Agent高度可控
- Agent 不能“自己发明工作”（暂时）
  - 所有 Task 来自：
    - 入职文件
    - 上级指派
  - 没有 prompt 让他“自由发挥”
- Agent 不会无限反思
  - 任务状态在结构里
  - 不在上下文里
  - LLM 不需要“回忆自己做过什么”
- 能被审计、被打断、被替换，就像人一样
  - 今天你走了
  - 明天另一个人接手你的 TODO 列表
  - 工作仍然继续

总结
- Agent 是一个被分配岗位与职责的执行实体。
- 它通过 Orchestration Skill 建立显式的任务状态机，
- 并通过 Atomic Skill 在严格约束下逐步完成任务。
- Agent 的智能体现在其对流程的遵守与对单步执行的质量，而非自由推理

## Agent Life Cycle
CREATE → ONBOARD → EXECUTE

### CREATE，创建一个新的Agent
- 分配 Agent ID
- 分配 Role（Manager / Expert / Senior / Junior）
- 装载可用 Skill 清单（但不执行）

### ONBOARD（方案的核心）
- 输入：
  - 入职职责说明（Role Description）
  - 入职文件（SOP / Orchestration Spec）
- 动作：
  - 构建 显式任务状态机
  - 初始化 Task / Step 列表
  - 标注每个 Step 的完成条件与信号
- 输出：
  - Agent 专属 Task State Graph

### EXECUTE
“逐一执行，就像日程表上的一个任务一样”

## Orchestration Skill
概念
- 显式 Task Lifecycle
- Step = 日程表里的“一条待办事项”

Orchestration Skill 的职责
  - 维护 task / step 状态
  - 判断 step 是否满足 completion condition
  - 决定是否推进到下一个 step
  - 注册 / 等待信号
  - 记录进度

## Atomic Skill
一个 Atomic Skill 必须满足：
 - 输入明确
 - 输出明确
 - 无长期上下文
 - 无跨 step 状态


## Signal Driven Continuation
