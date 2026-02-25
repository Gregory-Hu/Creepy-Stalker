---
sop_id: multi_agent_collaboration
name: 多 Agent 协作标准操作程序
description: 多个 Agent 协作完成复杂任务的流程
version: 1.0
author: Human Engineer
tags:
  - collaboration
  - multi-agent
  - meeting

prerequisites:
  - 任务需要多个 Agent 协作
  - 所有参与 Agent 已注册

roles:
  - role: initiator
    agent_type: orchestration
    responsibility: 发起和协调会议
  - role: participant
    agent_type: "*"
    responsibility: 参与讨论和执行

steps:
  - step_id: 1
    name: 识别协作需求
    description: 判断任务是否需要多 Agent 协作
    agent_type: orchestration
    action: evaluate
    params:
      task: "${task}"
      criteria:
        - requires_multiple_skills
        - requires_consensus
    output_key: collaboration_needed
    
  - step_id: 2
    name: 确定参与 Agent
    description: 根据任务需求确定参与的 Agent
    agent_type: orchestration
    action: select_agents
    params:
      required_capabilities: "${task.required_skills}"
    output_key: participants
    
  - step_id: 3
    name: 发起会议
    description: 创建会议并邀请参与者
    agent_type: meeting
    action: create_meeting
    params:
      topic: "${task.name}"
      participants: "${participants}"
      agenda: "${task.agenda}"
    output_key: meeting_id
    
  - step_id: 4
    name: 任务分解讨论
    description: 各 Agent 讨论如何分解任务
    agent_type: meeting
    action: discuss
    params:
      meeting_id: "${meeting_id}"
      topic: task_decomposition
    output_key: task_breakdown
    
  - step_id: 5
    name: 任务分配
    description: 将子任务分配给合适的 Agent
    agent_type: orchestration
    action: assign_tasks
    params:
      tasks: "${task_breakdown}"
      agents: "${participants}"
    output_key: assignments
    
  - step_id: 6
    name: 并行执行
    description: 各 Agent 执行分配的任务
    agent_type: "*"
    action: execute
    params:
      task: "${assignments[self.agent_id]}"
    output_key: execution_results
    parallel: true
    
  - step_id: 7
    name: 结果汇总
    description: 汇总所有执行结果
    agent_type: orchestration
    action: aggregate
    params:
      results: "${execution_results}"
    output_key: aggregated_result
    
  - step_id: 8
    name: 共识确认
    description: 确认所有参与 Agent 对结果达成一致
    agent_type: meeting
    action: vote
    params:
      meeting_id: "${meeting_id}"
      proposal: "${aggregated_result}"
    output_key: consensus
    
  - step_id: 9
    name: 生成报告
    description: 生成协作完成报告
    agent_type: document
    action: generate_report
    params:
      template_id: meeting_summary
      data:
        meeting_id: "${meeting_id}"
        participants: "${participants}"
        result: "${aggregated_result}"
        consensus: "${consensus}"
    output_key: final_report

conditions:
  - condition_id: consensus_reached
    description: 是否达成共识
    check: consensus.approved == true
    on_true: complete
    on_false: return_to_step_4

completion_criteria:
  - 所有子任务已完成
  - 结果已汇总
  - 达成共识或超时
---

# 多 Agent 协作标准操作程序 (Multi-Agent Collaboration SOP)

## 流程概述

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ 1. 识别需求  │ ──→ │ 2. 确定参与  │ ──→ │  3. 发起会议  │
└─────────────┘     └─────────────┘     └─────────────┘
                                              │
                                              ↓
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ 9. 生成报告  │ ←── │ 8. 共识确认  │ ←── │ 7. 结果汇总  │
└─────────────┘     └─────────────┘     └─────────────┘
      ↑                                       │
      │                                       ↓
      │                               ┌─────────────┐
      │                               │   6. 执行    │ ←──┐
      │                               └─────────────┘    │
      │                                    ↑             │
      │                                    │             │
      │                               ┌─────────────┐    │
      └────────────────────────────── │ 5. 任务分配  │ ←─┘
                                      └─────────────┘
                                            ↑
                                      ┌─────────────┐
                                      │ 4. 任务分解  │
                                      └─────────────┘
```

## 会议流程

### 阶段 1: 准备

1. 确定会议主题和议程
2. 邀请相关 Agent
3. 准备背景资料

### 阶段 2: 讨论

1. 各 Agent 发表意见
2. 讨论任务分解方案
3. 识别依赖关系

### 阶段 3: 分配

1. 根据能力分配任务
2. 确定交付时间
3. 建立沟通机制

### 阶段 4: 执行

1. 各 Agent 并行执行
2. 定期同步进度
3. 处理阻塞问题

### 阶段 5: 汇总

1. 收集执行结果
2. 整合交付物
3. 质量检查

### 阶段 6: 确认

1. 投票确认结果
2. 记录会议纪要
3. 归档协作过程

## 通信协议

### A2A 消息格式

```json
{
  "type": "a2a.task_request",
  "source": "orchestrator_001",
  "target": "file_operation_002",
  "payload": {
    "task_id": "task_123",
    "action": "read",
    "params": {"path": "file.txt"}
  }
}
```

### 投票机制

| 投票选项 | 含义 |
|---------|------|
| agree | 同意方案 |
| disagree | 反对方案 |
| abstain | 弃权 |

## 冲突解决

| 冲突类型 | 解决方式 |
|---------|---------|
| 任务分配冲突 | 由 Orchestrator 仲裁 |
| 结果分歧 | 投票决定 |
| 资源竞争 | 优先级调度 |
