# 构建好的 Agent

> 本专题系统梳理如何设计、开发、评估和迭代高质量的 AI Agent。核心框架采用 **Harness Engineering**（论文 *Agent Systems with Harness Engineering*）：把 Agent 系统看作 **Foundation Model + Harness**，通过 **Scaffold 优化** 与 **模型适配** 的双向协同，解决长程任务中的系统性失败。

---

## 目录结构

```text
01_Agent_Building_构建好的Agent/
├── INDEX.md                                    ← 本文件
├── 01_Design_Principles_设计原则/
│   └── Agent_Design_Core_Principles.md         ← 核心设计原则
├── 02_Architecture_架构设计/
│   └── Agent_Architecture_Components.md        ← Harness 架构与四大组件
├── 03_Skill_Development_Skill开发/
│   └── Agent_Skill_Development_Guide.md        ← Skill 开发方法论
├── 04_Memory_Learning_记忆与学习/
│   └── Agent_Memory_Learning_System.md         ← 记忆系统与持续学习
├── 05_Planning_Reasoning_规划与推理/
│   └── Agent_Planning_Reasoning.md             ← Agent Workflow 与推理
├── 06_Tools_MCP_工具与MCP/
│   └── Agent_Tools_MCP_Integration.md          ← Action Interface 与工具集成
├── 07_Human_Collaboration_人机协作/
│   └── Agent_Human_Collaboration.md            ← 人机协作模式
├── 08_Evaluation_评估/
│   └── Agent_Evaluation_Metrics.md             ← 过程质量评估
└── 09_Case_Studies_案例/
    └── Agent_Case_Studies.md                   ← Claude Code / OpenClaw / Hermes 对比
```

---

## 核心问题

一个"好"的 Agent 应该具备哪些特征？如何在 Claude Code、OpenClaw、AutoGPT 等不同平台上落地？

## 结论

高质量 Agent = **强大的 Harness** + **适配的模型** + **清晰的人机边界**。

具体而言：

1. **Harness 是独立的研究对象**：不是简单的模型包装，而是与模型协同进化的系统层。
2. **四大组件构成 Harness 设计空间**：Workflow、Memory、Skills、Multi-Agent。
3. **模型适配与 Scaffold 设计互补**：Context Engineering 控制推理时看到什么；Agentic Training 把行为内化为模型参数。
4. **评估要从"单步正确"转向"过程质量"**：轨迹、状态一致性、安全性、成本效率同样重要。

## 关键层面

| 层面 | 核心问题 | 对应文件 |
|------|----------|----------|
| 设计原则 | Agent 应该遵循哪些元规则？ | [`Agent_Design_Core_Principles.md`](01_Design_Principles_设计原则/Agent_Design_Core_Principles.md) |
| 架构设计 | Harness 由哪些组件构成？ | [`Agent_Architecture_Components.md`](02_Architecture_架构设计/Agent_Architecture_Components.md) |
| Skill 开发 | 如何把能力封装成可复用 Skill？ | [`Agent_Skill_Development_Guide.md`](03_Skill_Development_Skill开发/Agent_Skill_Development_Guide.md) |
| 记忆与学习 | Agent 如何记住偏好和避免重复犯错？ | [`Agent_Memory_Learning_System.md`](04_Memory_Learning_记忆与学习/Agent_Memory_Learning_System.md) |
| 规划与推理 | Agent 如何分解复杂任务？ | [`Agent_Planning_Reasoning.md`](05_Planning_Reasoning_规划与推理/Agent_Planning_Reasoning.md) |
| 工具与 MCP | Agent 如何调用外部工具和 MCP？ | [`Agent_Tools_MCP_Integration.md`](06_Tools_MCP_工具与MCP/Agent_Tools_MCP_Integration.md) |
| 人机协作 | Agent 如何与人类高效配合？ | [`Agent_Human_Collaboration.md`](07_Human_Collaboration_人机协作/Agent_Human_Collaboration.md) |
| 评估 | 如何判断 Agent 好不好？ | [`Agent_Evaluation_Metrics.md`](08_Evaluation_评估/Agent_Evaluation_Metrics.md) |
| 案例 | 优秀 Agent 是怎么设计的？ | [`Agent_Case_Studies.md`](09_Case_Studies_案例/Agent_Case_Studies.md) |

## 原始资料

- 论文 PDF：[99_Attachments_附件/50738_Agent_Systems_with_Harne/50738_Agent_Systems_with_Harne.pdf](../99_Attachments_附件/50738_Agent_Systems_with_Harne/50738_Agent_Systems_with_Harne.pdf)
- 论文 Markdown：[99_Attachments_附件/50738_Agent_Systems_with_Harne/50738_Agent_Systems_with_Harne.md](../99_Attachments_附件/50738_Agent_Systems_with_Harne/50738_Agent_Systems_with_Harne.md)
- 分析笔记：[99_Attachments_附件/50738_Agent_Systems_with_Harne/50738_Agent_Systems_with_Harne_分析笔记.md](../99_Attachments_附件/50738_Agent_Systems_with_Harne/50738_Agent_Systems_with_Harne_分析笔记.md)

## 关联笔记

- [[context-compress]] — 本仓库已落地的 Skill 示例
- [[self-improving-agent]] — 持续学习与记忆沉淀机制
- [[CLAUDE.md]] — 项目级 Agent 工作规范

## 待补充问题

- [x] 引入 Harness Engineering 核心框架
- [x] 补充 Claude Code / OpenClaw / Hermes Agent 对比
- [ ] 结合论文细节深化每个组件的讨论
- [ ] 增加失败案例与复盘
- [ ] 补充评估基准映射

## 标签

#Agent #ClaudeCode #Skill #MCP #HarnessEngineering #AI工具链

## Agent 整理记录

- 2026-06-30：建立专题骨架，完成 Skill 开发指南首版。
- 2026-06-30：整合论文 *Agent Systems with Harness Engineering*，重写架构、原则、评估与案例。
