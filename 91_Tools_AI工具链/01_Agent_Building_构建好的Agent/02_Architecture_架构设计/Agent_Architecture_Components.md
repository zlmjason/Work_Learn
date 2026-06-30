# Agent 架构组成

> 介绍 Agent 的核心组件和 Harness 架构。内容基于论文 *Agent Systems with Harness Engineering* 的 Harness Engineering 框架。

## 核心问题

一个 Agent 由哪些部分组成？Harness 在 Agent 系统中扮演什么角色？

## 结论

Agent 系统 = **Foundation Model + Harness**。Harness 由 **Workflow、Memory、Skills、Multi-Agent** 四大组件构成，并随应用需求从 Layer 1 演化到 Layer 3。

---

## 1. Agent 系统 = Foundation Model + Harness

```text
┌─────────────────────────────────────────────┐
│                Agent System                 │
│  ┌─────────────────────────────────────┐    │
│  │        Foundation Model             │    │
│  │  (Reasoning, Generation, Planning)  │    │
│  └─────────────────────────────────────┘    │
│                      ↑↓                      │
│  ┌─────────────────────────────────────┐    │
│  │            Harness                  │    │
│  │  Workflow + Memory + Skills +       │    │
│  │  Multi-Agent + Context Engineering  │    │
│  └─────────────────────────────────────┘    │
│                      ↑↓                      │
│              External Environment            │
└─────────────────────────────────────────────┘
```

**Harness 不是包装，而是系统层**：

- 它决定模型看到什么（Context Engineering）
- 它记录状态（Memory）
- 它组织行动（Workflow、Skills、Tools）
- 它协调多个模型/Agent（Multi-Agent）

## 2. Harness 的三层演化

| 层级 | 名称 | 核心能力 | 代表场景 |
|------|------|----------|----------|
| Layer 1 | Action Interface | 模型↔环境的基本交互循环 | 单次工具调用、问答 |
| Layer 2 | Workflow Infrastructure | 持久化工作空间 + 迭代工作流 | Coding Agent、数据分析 |
| Layer 3 | User-Centric Persistence | 用户画像 + 跨会话连续性 | 个人助手、长期陪伴 Agent |

**演化逻辑**：

- Layer 1 解决"能不能调用工具"
- Layer 2 解决"能不能完成多步骤、有状态的任务"
- Layer 3 解决"能不能理解用户、跨会话保持一致"

## 3. Harness 的四大组件

### 3.1 Agent Workflow

Agent 的感知-规划-执行循环。

- **Perceive**：理解用户输入和环境状态
- **Plan**：分解任务、选择策略
- **Act**：调用工具或执行动作
- **Observe**：收集反馈，决定下一步

常见模式：ReAct、Plan-and-Execute、Reflexion。

### 3.2 Memory Systems

持久化经验和上下文。

| 类型 | 时间尺度 | 形式 | 示例 |
|------|----------|------|------|
| 短期记忆 | 当前会话 | 上下文窗口、工作记忆 | 对话历史、TodoWrite |
| 长期记忆 | 跨会话 | 结构化/非结构化存储 | `.learnings/`、用户画像 |
| 外部记忆 | 任意 | RAG、数据库 | 知识库检索 |

### 3.3 Skill Libraries

可复用的行为单元。

- Skill 是面向任务的封装
- 需要管理：注册、版本、触发、维护
- 大规模 Skill 库需要 **progressive disclosure**：先加载 metadata/summary，按需展开完整内容

详见 [[Agent_Skill_Development_Guide]]。

### 3.4 Multi-Agent Orchestration

多个 Agent 的协调机制。

| 模式 | 特点 | 适用场景 |
|------|------|----------|
| 中心化（Centralized） | 一个协调者分配任务 | 任务明确、需要统一调度 |
| 去中心化（Decentralized） | Agent 之间直接协作 | 开放性系统、需要弹性 |
| Artifact-Mediated | 通过共享产物协作 | 代码审查、文档协作 |

## 4. 模型侧适配

Harness 为模型提供脚手架，模型也要为 Harness 做适配。

### 4.1 Context Engineering

推理时控制模型看到什么。

- Prompt Design
- RAG / Retrieval
- Context Management / Compression

### 4.2 Agentic Training

训练时将 Agent 行为内化为模型参数。

- SFT（模仿学习）
- RL（探索学习）
- Reward Design（Outcome-level vs Process-level）

## 5. 常见架构模式

| 模式 | 特点 | 适用场景 |
|------|------|----------|
| ReAct | 推理与行动交替 | 需要多步探索的任务 |
| Plan-and-Execute | 先规划再执行 | 目标明确、步骤可预见的任务 |
| Reflexion | 执行后自我反思 | 需要迭代改进的任务 |
| Multi-Agent | 多个 Agent 协作 | 复杂系统、需要分工 |

## 关联笔记

- [[Agent_Design_Core_Principles]] — 架构设计背后的原则
- [[Agent_Skill_Development_Guide]] — Skill Library 详细设计
- [[Agent_Memory_Learning_System]] — Memory Systems 详细设计
- [[Agent_Tools_MCP_Integration]] — Action Interface 详细设计
- [论文分析笔记](../99_Attachments_附件/50738_Agent_Systems_with_Harne/50738_Agent_Systems_with_Harne_分析笔记.md)

## 标签

#Agent #Architecture #HarnessEngineering #ReAct #MultiAgent
