# Agent Skill 开发指南

> 本文档系统化介绍如何为 Claude Code / OpenClaw 等 Agent 平台设计、实现和维护高质量 Skill。核心视角来自论文 *Agent Systems with Harness Engineering* 中的 **Skill Libraries** 组件。

## 核心问题

一个好的 Skill 应该具备什么特征？如何让它既容易被模型正确调用，又便于长期维护？

## 结论

高质量 Skill = **聚焦的问题定义** + **清晰的触发条件** + **可执行的流程/脚本** + **明确的失败模式** + **可进化的结构**。

Skill 是 Harness 中**可复用的行为单元**，需要从"单文件提示"进化为"可管理的能力资产"。

---

## 1. 什么是 Skill

Skill 是 Agent 的**能力包**。它把一类任务的经验、流程、工具、陷阱封装成可复用资产，供模型在合适场景下调用。

在 Claude Code 中，Skill 通常以文件夹形式存在：

```text
.claude/skills/<skill-name>/
├── SKILL.md        ← 入口：触发条件 + 快速参考
├── reference.md    ← 详细用法 + 配置 + 示例
├── gotchas.md      ← 陷阱与失败模式
├── config.json     ← 默认参数与配置
└── scripts/        ← 可执行脚本
```

## 2. Skill 设计五步法

### 步骤 1：聚焦问题

每个 Skill 只解决**一个具体、可定义的问题**。

| 好示例 | 坏示例 |
|--------|--------|
| "压缩会话上下文，便于迁移到新会话" | "处理所有文档相关任务" |
| "提取网页/PDF 内容并输出 Markdown" | "帮用户做所有事情" |

问题越聚焦，触发条件和执行流程越清晰。

### 步骤 2：定义触发条件

模型通过 `SKILL.md` 顶部的 `description` 判断是否需要调用该 Skill。描述必须包含：

- 解决什么问题
- 什么时候用
- 典型触发词/命令

示例（`context-compress`）：

```yaml
---
name: context-compress
description: Compress conversation context when approaching the model's context window limit. Use when the session grows long, responses slow down, or the user explicitly asks to compress/summarize the conversation. Can be triggered manually via /context-compress or wired into settings.json hooks for automatic warnings.
metadata:
---
```

正文中也要列出触发词：

- `/context-compress`
- "上下文太多了，压缩一下"
- "快满了，帮我总结一下"

### 步骤 3：定义输出与行为

明确 Skill 被触发后，模型应该：

1. 执行什么操作
2. 输出什么格式
3. 遵守哪些约束

以 `context-compress` 为例：

| 优先级 | 保留内容 | 丢弃/精简内容 |
|--------|----------|---------------|
| P0 | 当前任务目标与用户最终意图 | 中间探索性提问 |
| P0 | 已达成的重要决策和约定 | 已推翻的旧方案 |
| P1 | 已修改/创建的文件清单及变更原因 | 未改动的文件全文 |
| P1 | 关键代码/配置片段（≤ 30 行） | 大段未修改代码 |
| P1 | 未完成的待办事项 | 已完成的详细步骤 |
| P2 | 用户硬性约束 | 一般性讨论 |
| P2 | 关键错误及其根因 | 完整日志 |

### 步骤 4：拆分多文件结构

参考本仓库 `ADR-20260628-001` 决策，Skill 必须采用多文件结构：

| 文件 | 作用 | 内容要点 |
|------|------|----------|
| `SKILL.md` | 入口 | YAML frontmatter、触发条件、快速参考、输出格式 |
| `reference.md` | 详细参考 | 完整用法、配置、示例、联动 |
| `gotchas.md` | 陷阱 | 常见失败模式 + 正确做法 |
| `config.json` | 配置 | 阈值、参数、Hook 命令 |
| `scripts/` | 脚本 | 可执行工具 |

**为什么分文件？**

- 模型按需读取，减少上下文开销
- 触发词和陷阱区更清晰
- 便于独立迭代

### 步骤 5：配置与脚本化

如果 Skill 需要参数或确定性操作，写成脚本。

`context-compress` 的 `config.json` 示例：

```json
{
  "name": "context-compress",
  "version": "1.1.0",
  "defaultContextLimit": 200000,
  "defaultWarnPercent": 75,
  "maxCodeLines": 30,
  "supportedExtensions": [".md", ".c", ".h", ".py", ...],
  "skipDirectories": [".git", "node_modules", ...],
  "hook": {
    "type": "command",
    "command": "python .claude/skills/context-compress/scripts/context-check.py --scan-workspace --warn-at-percent 75 --exit-zero"
  }
}
```

脚本原则：

- 只做确定性操作（读取、计算、转换）
- 不依赖外部 LLM API（除非明确配置）
- 输出结构化，便于模型解析

---

## 3. Skill Library 的管理

当 Skill 数量增多时，需要考虑 Skill Library 的整体管理。

### 3.1 Progressive Disclosure

解决大规模 Skill 库的上下文窗口问题：

- 先加载 Skill 的 `name` + `description`（metadata）
- 模型判断需要某个 Skill 时，再展开 `reference.md` 和 `gotchas.md`
- 避免一次性把所有 Skill 全文塞进上下文

### 3.2 生命周期管理

| 阶段 | 动作 |
|------|------|
| 创建 | 从 `.learnings/` 中的重复模式提取 |
| 注册 | 在 `.claude/CLAUDE.md` 登记 |
| 使用 | 通过触发条件被模型调用 |
| 维护 | 根据使用反馈更新 `gotchas.md` 和 `reference.md` |
| 退役 | 过时 Skill 移入 `90_Archive_归档` |

### 3.3 分类组织

按功能分类存放 Skill：

```text
.claude/skills/
├── content/        ← 内容处理（summarize、pdf、mineru）
├── memory/         ← 记忆与学习（self-improving-agent、context-compress）
├── dev/            ← 开发辅助（code-review、simplify、verify）
├── research/       ← 研究（deep-research、autoresearch）
└── external/       ← 外部集成（find-skills）
```

## 4. `gotchas.md` 写法

`gotchas.md` 是 Skill 质量的关键。每条 Gotcha 应包含：

1. **表现**：模型容易犯的错误
2. **后果**：会导致什么问题
3. **正确做法**：应该怎么做

`context-compress` 的示例：

### 过度压缩，丢失任务目标

**表现**：摘要里只有文件列表和代码片段，没有「当前任务」和「用户最终意图」。

**后果**：新会话看到摘要后不知道要做什么。

**正确做法**：始终把「当前任务」和「关键决策」放在 P0 位置。

---

## 5. Skill 与项目指令的协同

Skill 不是孤立的，它需要与项目级指令（`CLAUDE.md`、`AGENTS.md`）协同：

| 层级 | 文件 | 作用 |
|------|------|------|
| 项目规范 | `.claude/CLAUDE.md` | 所有会话都遵循的通用规则 |
| 工作流 | `AGENTS.md` | 多步骤、多 Agent 协作流程 |
| 可复用能力 | `.claude/skills/<name>/` | 特定任务的封装 |
| 持续改进 | `.learnings/` | 错误、纠正、最佳实践 |

新建 Skill 后，必须在 `.claude/CLAUDE.md` 的本地技能表中登记。

---

## 6. Skill 开发 checklist

- [ ] 明确 Skill 解决的具体问题
- [ ] 创建 `.claude/skills/<name>/` 文件夹
- [ ] 编写 `SKILL.md`（含 `name` + `description` frontmatter）
- [ ] 列出触发条件（命令 + 自然语言表达）
- [ ] 定义输出格式与约束
- [ ] 编写 `reference.md`（详细用法 + 配置 + 示例）
- [ ] 编写 `gotchas.md`（至少 3-5 条常见失败模式）
- [ ] 编写 `config.json`（如需要参数）
- [ ] 编写 `scripts/`（如需要确定性操作）
- [ ] 在 `.claude/CLAUDE.md` 中登记
- [ ] 测试触发词能否正确唤起

---

## 7. 从 Learning 到 Skill 的晋升

当某个经验反复出现、具有跨任务通用性时，应该把它从 `.learnings/` 晋升为 Skill。

典型信号：

- 用户在对话中说 "save this as a skill"
- 同一类问题出现 3 次以上
- 解决方案不依赖具体项目，可跨仓库复用

晋升路径：

```text
Learning (.learnings/LEARNINGS.md)
    ↓ 反复验证、跨任务适用
Skill (.claude/skills/<name>/)
    ↓ 成为项目默认能力
Project Convention (.claude/CLAUDE.md)
```

---

## 8. 跨平台 Skill 设计差异

| 平台 | Skill 形式 | 重点 |
|------|-----------|------|
| Claude Code | `.claude/skills/<name>/` 文件夹 | 多文件结构、Hook 集成 |
| OpenClaw | `~/.openclaw/workspace/skills/<name>/` | 工作区级注入、跨会话共享 |
| LangChain | 工具函数 / Tool 类 | Schema 定义、返回值结构化 |
| AutoGPT | Ability / Skill 文件 | 目标驱动、自主调用 |

核心原则不变：**聚焦问题、清晰触发、可执行、可进化**。

---

## 关联笔记

- [[INDEX]] — 本专题总览
- [[Agent_Design_Core_Principles]] — Skill 设计背后的原则
- [[Agent_Architecture_Components]] — Skill 在 Harness 架构中的位置
- [[self-improving-agent]] — 持续学习与 Skill 晋升机制
- [[context-compress]] — 本仓库 Skill 实例
- [论文分析笔记](../50738_Agent_Systems_with_Harne_分析笔记.md)

## 标签

#Agent #Skill #HarnessEngineering #ClaudeCode #OpenClaw #DesignPattern
