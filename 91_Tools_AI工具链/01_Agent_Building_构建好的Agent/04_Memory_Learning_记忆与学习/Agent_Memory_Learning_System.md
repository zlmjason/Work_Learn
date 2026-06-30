# Agent 记忆与学习系统

> 如何让 Agent 记住经验、避免重复犯错、持续进化。

## 核心问题

Agent 没有真正的长期记忆，如何设计机制让它"越用越聪明"？

## 结论

通过 **短期记忆 + 长期记忆 + 学习-晋升循环** 三层结构，实现 Agent 的持续进化。

---

## 1. 三层记忆结构

```text
短期记忆（当前会话）
    ↓ 压缩/摘要
中期记忆（.learnings/）
    ↓ 验证/沉淀
长期记忆（CLAUDE.md / Skill）
```

## 2. 短期记忆

- 当前对话上下文
- 已执行的操作和结果
- 用户的临时偏好

管理方法：

- 使用 `context-compress` 压缩过长会话
- 使用 `TodoWrite` 跟踪任务状态

## 3. 中期记忆：`.learnings/`

记录：

- 错误与踩坑（`ERRORS.md`）
- 纠正与洞察（`LEARNINGS.md`）
- 功能需求（`FEATURE_REQUESTS.md`）
- 架构决策（`DECISIONS.md`）
- 复发模式（`PATTERNS.md`）

格式要求：每条记录包含 `Logged`、`Priority`、`Status`、`Area`、`Summary`、`Details`、`Suggested Action`、`Metadata`。

## 4. 长期记忆：项目规范与 Skill

当经验具有跨任务通用性时：

- 晋升为 `CLAUDE.md` 规则
- 提取为 `.claude/skills/` 下的 Skill
- 写入个人 `.claude/memory/`（跨项目偏好）

## 5. 学习-晋升循环

```text
触发场景 → 记录 → 定期回顾 → 验证普适性 → 晋升 → 应用 → 再反馈
```

## 关联笔记

- [[Agent_Skill_Development_Guide]] — 从 Learning 到 Skill 的晋升路径
- [[self-improving-agent]] — 本仓库的持续改进 Skill

## 标签

#Agent #Memory #Learning #SelfImprovement
