# Agent 评估指标与方法

> 如何判断一个 Agent 好不好？论文 *Agent Systems with Harness Engineering* 强调：评估要从"单步正确"转向"过程质量"。

## 核心问题

Agent 的质量应该从哪些维度评估？

## 结论

Agent 评估应从 **正确性、效率、可解释性、安全性、用户体验、过程质量** 六个维度展开。最终答案正确 ≠ 过程可靠。

---

## 1. 正确性（Correctness）

- 任务是否按预期完成？
- 输出是否符合规范？
- 是否引入了错误？

评估方法：人工检查、单元测试、回归测试、基准任务集。

## 2. 效率（Efficiency）

- 完成任务用了多少步？
- 调用了多少次工具？
- 消耗了多少 Token？

评估方法：步骤计数、Token 用量统计、时间测量。

## 3. 可解释性（Explainability）

- Agent 是否说明了决策原因？
- 输出是否结构化？
- 是否能追溯执行路径？

评估方法：日志审查、输出格式检查。

## 4. 安全性（Safety）

- 是否执行了未授权操作？
- 是否泄露了敏感信息？
- 是否有明确的权限边界？

评估方法：红队测试、权限审查、敏感信息扫描。

## 5. 用户体验（UX）

- 是否过度打断用户？
- 是否在合适时机寻求帮助？
- 输出是否易于理解？

评估方法：用户反馈、会话满意度评分。

## 6. 过程质量（Process Quality）

论文强调的关键维度：

- **轨迹质量**：执行路径是否合理？是否有冗余或回溯？
- **状态一致性**：Agent 对环境状态的理解是否与实际一致？
- **错误恢复能力**：遇到意外后能否正确修正？
- **成本效率**：Token、时间、API 调用成本是否可接受？

## 评估流程

```text
定义任务 → 收集输入 → 运行 Agent → 记录轨迹 → 多维打分 → 定位问题 → 迭代改进
```

## 评估基准映射

论文将 Agent 评估基准分为多个领域：

| 领域 | 关注点 |
|------|--------|
| Deep Research | 多源信息收集与综合 |
| Software Engineering | 代码生成、调试、项目管理 |
| Tool Use | 工具选择与调用准确性 |
| Computer Use | GUI 操作、环境交互 |
| Scientific Research | 实验设计、假设验证 |

## 关联笔记

- [[Agent_Design_Core_Principles]] — 评估原则来源
- [[Agent_Case_Studies]] — 具体案例评估
- [论文分析笔记](../99_Attachments_附件/50738_Agent_Systems_with_Harne/50738_Agent_Systems_with_Harne_分析笔记.md)

## 标签

#Agent #Evaluation #Metrics #Benchmark #HarnessEngineering
