# Agent 核心设计原则

> 设计 Agent 时应遵循的元规则，用于指导架构选择、Skill 设计和人机协作。本文原则部分基于论文 *Agent Systems with Harness Engineering* 提出的 Harness Engineering 思想。

## 核心问题

一个"好"的 Agent 应该遵循哪些高层次原则？

## 结论

好 Agent 的设计应围绕五个核心原则：**目标清晰、边界明确、Harness 与模型双向协同、可进化、可解释**。

---

## 1. 目标清晰（Goal Clarity）

Agent 必须清楚知道它要帮用户完成什么。

- 每个任务都有明确的成功标准
- 不主动扩大范围
- 遇到歧义时优先澄清，而不是猜测

## 2. 边界明确（Scope Boundaries）

Agent 要知道自己能做什么、不能做什么。

- 超出能力时主动说明
- 不越权执行危险操作（删除、推送、部署等）
- 遵守项目规范（如 `CLAUDE.md`）

## 3. Harness 与模型双向协同（Harness-Model Co-evolution）

这是 *Agent Systems with Harness Engineering* 的核心理念。

```text
Agent System = Foundation Model + Harness

Harness Engineering = Scaffold Optimization + Model Adaptation
                      (脚手架优化)          (模型适配)
```

**核心观点**：

- Harness 不是简单的"模型包装"，而是**与模型协同进化**的独立组件。
- 好的 Harness 能让中等能力的模型完成长程任务；好的模型能让 Harness 实现更复杂的工作流。
- **双向优化**：
  - Scaffold 为模型设计 → 提供合适的上下文、工具、记忆、工作流。
  - 模型为 Scaffold 适配 → 通过 Context Engineering 和 Agentic Training 提升在特定 Harness 中的表现。

**设计启示**：

- 不要把所有问题都丢给模型解决。
- 明确"哪些能力靠 Harness 解决，哪些靠模型解决"。
- 当模型在某类任务上反复失败时，优先考虑改进 Harness（如增加记忆、细化工作流、优化 Skill 触发）。

## 4. 可进化（Evolvability）

Agent 应该能从经验中学习。

- 记录错误和纠正（`.learnings/`）
- 提取复用模式为 Skill
- 定期晋升学习到项目规范

## 5. 可解释（Explainability）

Agent 的行为应该可被理解和审计。

- 说明为什么采取某个行动
- 保留决策痕迹
- 输出结构化，便于复查

---

## 原则与论文的映射

| 本文件原则 | 论文中的概念 |
|------------|--------------|
| 目标清晰、边界明确 | User-Centric Persistence、Safety 设计 |
| Harness 与模型双向协同 | Harness Engineering = Scaffold + Model |
| 可进化 | Memory Systems、Skill Libraries 的渐进式演化 |
| 可解释 | 评估从"单步正确"转向"过程质量" |

## 关联笔记

- [[Agent_Skill_Development_Guide]] — 原则落地为 Skill 的方法
- [[Agent_Architecture_Components]] — 原则在 Harness 架构中的体现
- [论文分析笔记](../99_Attachments_附件/50738_Agent_Systems_with_Harne/50738_Agent_Systems_with_Harne_分析笔记.md)

## 标签

#Agent #DesignPrinciples #HarnessEngineering #ClaudeCode
