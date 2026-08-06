# 论文分析笔记

## 1. 基本信息
- **Title**: Agent Systems with Harness Engineering
- **Journal**: arXiv 预印本 / 技术报告
- **Year**: 2026
- **Corresponding author**: Wayne Xin Zhao (RUC), Yawen Li (BUPT), Zhe Xue (BUPT)
- **Research field**: LLM-based Agent Systems / 系统架构 / 工程化

---

## 2. 一句话总结

本文提出了 **Harness Engineering** 作为 Agent Systems 的新研究范式，证明了支撑架构（Harness）与基础模型的**双向协同优化**是构建可靠、可扩展、可控 Agent 系统的核心——仅靠模型能力无法解决长程任务中的系统性失败。

---

## 3. 科学问题

作者试图解决什么问题？

> 即使是最强的大模型（如 GPT-4/Claude），在缺乏充分系统支撑时，在长程任务中也会表现出**系统性失败**：
> - 多步规划中丢失中间目标
> - 工具调用时机/参数错误
> - 无法利用环境反馈修正早期错误
> 
> 这些失败**不是模型训练不足**导致的，而是 LLM **单轮生成接口** 与 现实世界 **有状态、迭代的问题求解** 之间的**结构性错配**。
>
> 核心问题：如何系统性地设计和优化支撑 LLM 的外围基础设施（Harness），使其从"文本生成器"进化为"可靠的自主 Agent"？

---

## 4. 核心假说（框架模型）

作者提出的 Harness Engineering 框架是什么？

```
Agent System = Foundation Model + Harness

Harness Engineering = Scaffold Optimization + Model Adaptation
                      (脚手架优化)          (模型适配)
                      
  ┌─────────────────────────────────────────────────────────────┐
  │                      Scaffold Side                           │
  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────┐  │
  │  │ Workflow │  │  Memory  │  │  Skills  │  │ Multi-Agent│  │
  │  │ perceive │  │ short-   │  │ acquire  │  │ centralized│  │
  │  │  plan    │  │ long-term│  │ manage   │  │decentralized│  │
  │  │  act     │  │          │  │ maintain │  │            │  │
  │  └──────────┘  └──────────┘  └──────────┘  └────────────┘  │
  └─────────────────────────────────────────────────────────────┘
                              ↕ Synergistic (协同)
  ┌─────────────────────────────────────────────────────────────┐
  │                     Model Side                               │
  │  ┌──────────────────┐      ┌──────────────────┐            │
  │  │Context Engineering│      │  Agentic Training │            │
  │  │ - prompt design   │      │  - SFT (imitation)│            │
  │  │ - RAG/retrieval   │      │  - RL (exploration)│           │
  │  │ - context mgmt    │      │  - reward design  │            │
  │  └──────────────────┘      └──────────────────┘            │
  └─────────────────────────────────────────────────────────────┘
```

**核心观点**：
- Harness 不是简单的"模型包装"，而是**与模型协同进化**的独立组件
- 好的 Harness 能让中等能力的模型完成长程任务；好的模型能让 Harness 实现更复杂的工作流
- **双向优化**：Harness 为模型设计 → 模型为 Harness 适配

---

## 5. 主要结论

1. **Harness 经历了三个演化阶段**：
   - Layer 1 (Action Interface): 模型↔环境的基本交互循环
   - Layer 2 (Workflow Infrastructure): 持久化工作空间 + 迭代工作流（如 coding agent）
   - Layer 3 (User-Centric Persistence): 跨会话的用户记忆和个性化（如个人助手）

2. **四个核心组件构成 Harness 设计空间**：
   - Agent Workflow（感知-规划-执行循环）
   - Memory Systems（短期/长期记忆，结构化/非结构化）
   - Skill Libraries（可复用行为单元，需管理维护）
   - Multi-Agent Orchestration（中心化/去中心化协调）

3. **模型侧适配与 Scaffold 设计是互补的**：
   - Context Engineering：推理时控制模型看到什么（prompt, RAG, 压缩）
   - Agentic Training：训练时将 Agent 行为内化为模型参数（SFT, RL）

4. **评估需要从"单步正确"转向"过程质量"**：
   - 最终答案正确 ≠ 过程可靠
   - 需要评估轨迹质量、状态一致性、安全性、成本效率

---

## 6. Figure-by-Figure 分析

### Figure 1：Agent 系统发展时间线
- **内容**：按时间排列的代表性工作，下排为 Scaffold-side（Workflow/Memory/Skills/Multi-Agent），上排为 Model-side（Context Engineering/Agentic Training）
- **支撑的结论**：两个维度是"协同"的——Scaffold 设计塑造了模型适配的方向，而改进的模型能力反过来支持更复杂的 Scaffold 架构
- **是否充分**：是，展示了领域全景，但偏列举性质，缺少深度关联分析

### Figure 2：论文结构总览
- **内容**：树状图展示本文的章节组织
- **作用**：帮助读者快速定位感兴趣的内容
- **评价**：清晰的导航图

### Figure 3：Harness 架构的三层演化
- **内容**：
  - Layer 1: Action Interface（基本 action-observation 循环）
  - Layer 2: Workflow Infrastructure（持久工作空间 + 迭代开发循环）
  - Layer 3: User-Centric Persistence（用户画像 + 跨会话连续性）
- **支撑的结论**：Harness 的 scope 随应用需求逐步扩大，从"工具调用"到"工作流编排"再到"用户连续性"
- **是否充分**：是，但第三层（User-Centric）的案例偏少，OpenClaw 几乎是唯一详例

### Figure 4：Harness 设计空间总览
- **内容**：四大组件（Workflow/Memory/Skills/Multi-Agent）与外部环境、模型适配的交互关系
- **支撑的结论**：Harness 不是孤立模块，而是与环境和模型形成闭环系统
- **是否充分**：是，作为综述的"总览图"很合适

### Table 1：三个代表性系统对比
- **内容**：Claude Code / OpenClaw / Hermes Agent 在四大组件上的设计差异
- **关键发现**：
  - Claude Code：optimizes for **human-in-the-loop safety**（分层权限、交互确认）
  - OpenClaw：optimizes for **composable extensibility**（声明式上下文、多通道路由）
  - Hermes Agent：optimizes for **autonomous self-governance**（预算控制、安全过滤、自适应提示）
- **支撑的结论**：同样的四个组件，不同的部署场景（开发者辅助/平台编排/自主终端）需要完全不同的设计权衡
- **是否充分**：是，将抽象概念落地到具体系统对比，非常有价值

---

## 7. 证据链总结

对于综述论文，证据链是**概念性的**而非实验性的：

```
问题观察
    ↓ (LLM 在长程任务中的系统性失败)
概念框架提出
    ↓ (Harness Engineering = Scaffold + Model, 双向协同)
组件系统分析
    ↓ (4大组件 × 设计原则 × 代表方法)
工业级案例验证
    ↓ (Claude Code / OpenClaw / Hermes Agent 对比)
评估基准综述
    ↓ (5大领域 × 数十个 benchmark)
未来方向识别
    (Efficiency / Safety / Continual Learning / State Modeling / Embodied / Evaluation)
```

**关键逻辑**：作者不是通过实验"证明"Harness 有效，而是通过：
1. **问题归因**：将失败归因于结构错配而非模型能力不足
2. **分类体系**：建立系统的 taxonomy 让领域有共同语言
3. **案例对比**：展示不同设计哲学在同样组件上的不同实现
4. **基准映射**：将已有 benchmark 映射到 Harness 的不同能力维度

---

## 8. 创新点

1. **正式提出 Harness Engineering 作为独立研究范式**：
   - 之前的工作分散在"Agent Framework""Prompt Engineering""Tool Use"等概念下
   - 本文将其统一为一个有明确定义、有分类体系、有评估维度的 discipline

2. **系统性的 Taxonomy（四大组件 + 两大模型适配方向）**：
   - 每个组件都有清晰的设计原则、代表方法、trade-off 分析
   - 不是简单罗列，而是有内在逻辑（从 Workflow → Memory → Skills → Multi-Agent，层层递进）

3. **"双向协同"框架**：
   - 不仅讲 Harness 怎么支撑模型，也讲模型怎么适配 Harness
   - 避免了单方面强调 Scaffold 或 Model 的偏见

4. **三个工业级系统的深度对比（Table 1）**：
   - 这是很多学术论文缺少的——将学术概念和工业实践连接起来
   - Claude Code / OpenClaw / Hermes Agent 分别代表三种设计哲学

5. **全面覆盖评估基准**：
   - Deep Research / Software Engineering / Tool Use / Computer Use / Scientific Research
   - Table 2 汇总了数十个 benchmark，可作为领域参考手册

---

## 9. 局限性

1. **缺乏统一实验验证**：
   - 本文是综述/框架论文，没有在自己的统一平台上做控制变量实验
   - 很多结论（如"好的 Harness 能让中等模型完成长程任务"）是定性的，缺少定量证据

2. **未深入探讨自动化 Harness 设计**：
   - 主要讨论的是手工设计的 Harness 组件
   - 对"自动搜索/学习最优 Harness 架构"（如 NAS for Agent Systems）讨论不足

3. **安全性和效率的讨论偏问题陈述**：
   - Section 6.1 (Efficiency) 和 6.2 (Safety) 更多是指出 gaps，而非给出系统性解决方案
   - 这与领域发展阶段有关——这些方向本身还不成熟

4. **具身智能（Embodied）讨论相对简略**：
   - Section 6.5 只占一小节，而 Embodied Agent 的 Harness 设计有其独特性（物理不可逆性、实时性等）

5. **评估基准难以区分模型 vs Harness 的贡献**（作者自己也承认）：
   - "Most fundamentally, current benchmarks rarely disentangle improvements attributable to the base model from those attributable to the harness"
   - 这是领域级问题，但也是本文未能解决的痛点

---

## 10. 对我课题的启发

### 可以借鉴的方法
- **Context Engineering 中的压缩策略**：
  - 区分"可重建信息"（工具输出）和"不可替代信息"（推理结论、用户决策）
  - 这个框架可直接用于设计任何长上下文 Agent 的内存管理
  
- **Memory 的分层生命周期管理**：
  - 工作记忆（session 内）→ 结构化/非结构化长期记忆 → Skill 的渐进式提取
  - 不同状态类型有不同的持久化和更新频率

- **Skill Library 的 progressive disclosure**：
  - 先加载 metadata/summary，按需展开完整内容
  - 解决大规模 skill 库的上下文窗口问题

### 可以借鉴的图
- **Figure 3（三层演化）**：如果做 Agent 系统的技术演进分析，这个分层框架非常清晰
- **Figure 4（设计空间总览）**：展示复杂系统的模块化关系时，这种"中心-外围"构图很有参考价值
- **Table 1（系统对比）**：将自己的系统和 SOTA 做结构化对比时，可以借鉴这个四维对比框架

### 可以借鉴的写作逻辑
```
问题归因（不是模型不行，是结构错配）
    → 概念框架（Harness Engineering 定义 + 三个视角）
    → 演化历史（三个阶段，展示领域如何发展到今天）
    → 组件拆解（4大组件，每个都有设计原则 + 代表方法 + 讨论）
    → 模型适配（Context Engineering + Agentic Training，补全双向优化）
    → 评估映射（5大领域 benchmark 综述）
    → 未来方向（6个 gaps，每个都有明确的问题陈述）
```
这个结构非常适合写一篇**领域综述**或**技术报告**。

### 可以补强我课题的实验
- 如果做 **Coding Agent**：重点参考 Section 3.1.3 (Action Execution) 中的 sandbox / MCP / tool granularity 设计
- 如果做 **多 Agent 系统**：Section 3.4 的 centralized vs decentralized 权衡、verification subagent 模式、artifact-mediated collaboration
- 如果做 **RAG/检索增强**：Section 4.1.1 的 active retrieval + agentic retrieval 框架
- 如果做 **模型微调**：Section 4.2 的 SFT vs RL 对比、outcome-level vs process-level reward 分析
- **通用建议**：任何 Agent 项目都应该明确"哪些能力靠 Harness 解决，哪些靠模型解决"，避免把所有问题丢给模型

---

> **总体评价**：这是一篇高质量的**领域综述 + 概念框架论文**，适合作为 Agent Systems 的入门教材和 reference。虽然没有新的实验结果，但其分类体系、设计原则总结、工业案例对比和基准映射对研究者非常实用。最大的价值在于**统一了领域语言**——让分散在 framework design、prompt engineering、tool use、RAG 等方向的工作有了一个共同的分析框架。
