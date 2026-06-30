# Agent 规划与推理

> Agent 如何理解复杂任务、制定计划并在执行中调整。

## 核心问题

面对一个复杂任务，Agent 应该如何分解、规划、执行和修正？

## 结论

高质量规划需要 **任务分解、依赖识别、执行监控、动态修正** 四个能力。

---

## 1. 任务分解（Decomposition）

把复杂目标拆成可执行子任务。

- 按模块拆分
- 按依赖顺序拆分
- 每个子任务有明确的完成标准

## 2. 依赖识别（Dependency Awareness）

识别子任务之间的先后关系。

- 哪些任务可以并行？
- 哪些任务必须先完成？
- 哪些任务相互阻塞？

## 3. 执行监控（Execution Monitoring）

跟踪每个子任务的执行状态。

- 使用 `TodoWrite` 管理进度
- 关键步骤输出中间结果
- 失败时及时报告

## 4. 动态修正（Dynamic Adaptation）

当计划遇到意外时调整。

- 工具调用失败 → 换备用方案
- 用户纠正 → 更新计划
- 发现新约束 → 重新排序

## 常见推理模式

| 模式 | 说明 | 示例 |
|------|------|------|
| Chain-of-Thought | 逐步推理 | 解决数学/逻辑问题 |
| ReAct | 推理-行动交替 | 探索性任务 |
| Reflection | 执行后反思 | 代码审查后的改进 |
| Plan-and-Solve | 先规划再解决 | 多步骤工程任务 |

## 关联笔记

- [[Agent_Architecture_Components]] — 推理层在架构中的位置
- [[Agent_Tools_MCP_Integration]] — 工具调用辅助推理

## 标签

#Agent #Planning #Reasoning #ReAct
