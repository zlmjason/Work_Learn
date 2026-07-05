# Agent 记忆与学习系统

> 如何让 Agent 记住经验、避免重复犯错、持续进化。本文基于论文 *Agent Systems with Harness Engineering* 中的 **Memory Systems** 组件。

## 核心问题

Agent 没有真正的长期记忆，如何设计机制让它"越用越聪明"？

## 结论

通过 **工作记忆 → 短期记忆 → 长期记忆** 的分层生命周期管理，加上 **学习-晋升循环**，实现 Agent 的持续进化。

---

## 1. 记忆分层

```text
工作记忆（当前任务上下文）
    ↓ 摘要/压缩
短期记忆（当前会话）
    ↓ 筛选/结构化
中期记忆（.learnings/）
    ↓ 验证/沉淀
长期记忆（CLAUDE.md / Skill / 用户画像）
```

| 类型 | 时间尺度 | 形式 | 管理方法 |
|------|----------|------|----------|
| 工作记忆 | 当前任务 | 上下文中的关键变量、待办 | `TodoWrite`、临时变量 |
| 短期记忆 | 当前会话 | 完整对话历史 | `context-compress` 压缩 |
| 中期记忆 | 跨会话 | 结构化日志 | `.learnings/*.md` |
| 长期记忆 | 长期 | 项目规范、Skill、用户画像 | `CLAUDE.md`、`.claude/skills/`、`.claude/memory/` |

## 2. 工作记忆

当前任务中的临时状态。

- 当前步骤的目标
- 已完成的子任务
- 待确认的决策

## 3. 短期记忆

当前会话的上下文。

- 对话历史
- 已执行的操作和结果
- 用户的临时偏好

管理方法：

- 使用 `context-compress` 压缩过长会话
- 使用 `TodoWrite` 跟踪任务状态

## 4. 中期记忆：`.learnings/`

记录：

- 错误与踩坑（`ERRORS.md`）
- 纠正与洞察（`LEARNINGS.md`）
- 功能需求（`FEATURE_REQUESTS.md`）
- 架构决策（`DECISIONS.md`）
- 复发模式（`PATTERNS.md`）

格式要求：每条记录包含 `Logged`、`Priority`、`Status`、`Area`、`Summary`、`Details`、`Suggested Action`、`Metadata`。

## 5. 长期记忆：项目规范与 Skill

当经验具有跨任务通用性时：

- 晋升为 `CLAUDE.md` 规则
- 提取为 `.claude/skills/` 下的 Skill
- 写入个人 `.claude/memory/`（跨项目偏好）

## 6. 结构化 vs 非结构化记忆

| 类型 | 特点 | 示例 |
|------|------|------|
| 结构化 | 便于检索、更新 | `.learnings/` 条目、Skill frontmatter |
| 非结构化 | 保留完整上下文 | 会话摘要、用户笔记 |
| 外部记忆 | 通过 RAG 检索 | 知识库、文档库 |

## 7. 学习-晋升循环

```text
触发场景 → 记录 → 定期回顾 → 验证普适性 → 晋升 → 应用 → 再反馈
```

## 关联笔记

- [[Agent_Skill_Development_Guide]] — 从 Learning 到 Skill 的晋升路径
- [[self-improving-agent]] — 本仓库的持续改进 Skill
- [[context-compress]] — 短期记忆压缩工具
- [论文分析笔记](../99_Attachments_附件/50738_Agent_Systems_with_Harne/50738_Agent_Systems_with_Harne_分析笔记.md)

## 标签

#Agent #Memory #Learning #HarnessEngineering #SelfImprovement
