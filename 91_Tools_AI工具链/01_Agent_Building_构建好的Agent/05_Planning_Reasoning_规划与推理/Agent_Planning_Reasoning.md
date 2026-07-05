# Agent 规划与推理

> Agent 如何理解复杂任务、制定计划并在执行中调整。本文基于论文 *Agent Systems with Harness Engineering* 中的 **Agent Workflow** 组件。

## 核心问题

面对一个复杂任务，Agent 应该如何分解、规划、执行和修正？

## 结论

高质量规划需要 **任务分解、依赖识别、执行监控、动态修正** 四个能力。Agent Workflow 的核心是 **感知-规划-执行循环**。

---

## 1. Agent Workflow 循环

```text
Perceive（感知）
    ↓
Plan（规划）
    ↓
Act（执行）
    ↓
Observe（观察）
    ↓
（循环）
```

### 1.1 Perceive（感知）

- 理解用户输入
- 读取环境状态
- 识别当前约束

### 1.2 Plan（规划）

- 分解任务
- 选择执行策略
- 识别依赖关系

### 1.3 Act（执行）

- 调用工具
- 读写文件
- 执行命令

### 1.4 Observe（观察）

- 收集执行反馈
- 判断是否达到预期
- 决定是否修正

## 2. 任务分解（Decomposition）

把复杂目标拆成可执行子任务。

- 按模块拆分
- 按依赖顺序拆分
- 每个子任务有明确的完成标准

## 3. 依赖识别（Dependency Awareness）

识别子任务之间的先后关系。

- 哪些任务可以并行？
- 哪些任务必须先完成？
- 哪些任务相互阻塞？

## 4. 执行监控（Execution Monitoring）

跟踪每个子任务的执行状态。

- 使用 `TodoWrite` 管理进度
- 关键步骤输出中间结果
- 失败时及时报告

## 5. 动态修正（Dynamic Adaptation）

当计划遇到意外时调整。

- 工具调用失败 → 换备用方案
- 用户纠正 → 更新计划
- 发现新约束 → 重新排序

## 6. 常见推理模式

| 模式 | 说明 | 示例 |
|------|------|------|
| Chain-of-Thought | 逐步推理 | 解决数学/逻辑问题 |
| ReAct | 推理-行动交替 | 探索性任务 |
| Reflection | 执行后反思 | 代码审查后的改进 |
| Plan-and-Solve | 先规划再解决 | 多步骤工程任务 |

## 关联笔记

- [[Agent_Architecture_Components]] — Workflow 在 Harness 架构中的位置
- [[Agent_Tools_MCP_Integration]] — 工具调用辅助推理
- [论文分析笔记](../99_Attachments_附件/50738_Agent_Systems_with_Harne/50738_Agent_Systems_with_Harne_分析笔记.md)

## 标签

#Agent #Planning #Reasoning #ReAct #HarnessEngineering
