---
name: kb-workflow
description: Orchestration layer for this knowledge base — phase-to-skill pipeline tables for recurring workflows (new material intake, Inbox cleanup, note iteration, continuous improvement) plus a re-read-before-use discipline. Trigger when the user asks "工作流", "流程是什么", "接下来用哪个 skill", "新资料怎么处理", "入库流程", or starts a multi-step knowledge-base task. Do NOT use for the concrete operation of each step — load the referenced skill for that.
metadata:
---

# KB Workflow — 知识库工作流编排层

本 skill 是**编排层**：不替代任何具体 skill，只回答"当前阶段该用哪个 skill、做到什么程度算完"。各阶段的具体用法以被引用 skill 的 SKILL.md 为准。

> 本 skill 刻意保持单文件轻量结构（区别于 CLAUDE.md §4.1 的多文件约定）——所有细节都住在被引用的 skill 里，编排层只做路由。

## 用前重读纪律（硬性要求）

**context compaction 可能已丢弃本会话之前读过的 skill 内容。每个阶段开始前，必须重读该阶段对应 skill 的 SKILL.md，而不是凭记忆操作。** 长会话经 `context-compress` 压缩后同理。

---

## 流水线 A：新资料入库（PDF / Word / 网页 / 视频 → 归档笔记）

| 阶段 | Skill | 何时加载 | Exit criteria |
|------|-------|----------|---------------|
| A0 明确意图 | — | 无需 skill | 用户确认产出形式：单篇笔记 / 多篇拆分 / 仅存档；放哪个层次 |
| A1 解析提取 | `mineru-pdf-parser`（PDF/Word/PPT/Excel/图片，需保留结构）<br>`summarize`（网页/YouTube/快速提取）<br>`pdf` / `docx-cn`（本地处理） | 动手解析**前** | 内容提取完成，临时落盘到 `00_Inbox_临时收集/` 或临时目录 |
| A2 建笔记 | `mcu-note-creator` | 写笔记前 | 符合 9 段式模板（§8.2）、命名规范（§2.2）、目录层次正确 |
| A3 规范检查 | `doc-review` | 笔记写完后 | 检查通过，无格式/命名/章节残留问题 |
| A4 归档 | `note-organizer` | 移动文件前 | 文件位于正确层次目录，文件名符合前缀规范 |
| A5 提交 | `git-upload-push` | 推送前 | 已推送 master（用户偏好：不建功能分支） |

## 流水线 B：Inbox 清理 / 批量整理

| 阶段 | Skill | Exit criteria |
|------|-------|---------------|
| B0 盘点 | — | 列出 `00_Inbox_临时收集/` 全部文件与建议去向；**用户确认计划后才动手**（§8.3 第 1 条） |
| B1 归档 | `note-organizer` | 每篇到位、命名规范 |
| B2 复查 | `doc-review` | 目录级检查通过 |
| B3 提交 | `git-upload-push` | 已推送 |

## 流水线 C：笔记内容迭代（已有笔记深化 / 修正）

| 阶段 | Skill | Exit criteria |
|------|-------|---------------|
| C0 定位 | Grep/Glob；按双链/索引查找时用 `obsidian-vault` | 找到目标笔记及关联笔记 |
| C1 修改 | — | 遵守 §8.1 第 3 条（保留原文、下方新增整理版）；方案经用户确认（LRN-20260717-001） |
| C2 检查 | `doc-review` | 通过 |
| C3 提交 | `git-upload-push` | 已推送 |

## 流水线 D：持续改进闭环

| 阶段 | Skill | Exit criteria |
|------|-------|---------------|
| D1 实时记录 | `self-improving-agent` | 错误/纠正/需求当场记入 `.learnings/`（CLAUDE.md §5.2） |
| D2 月度 retro | `self-improving-agent`（见该 skill「月度回顾」节） | 聚类复发问题 → 产出修订建议 → 用户确认 → 晋升并销账 |
| D3 能力沉淀 | `skillify` 或手动建 skill | 新 skill 登记到 `.learnings/SKILL_REGISTRY.md` 与 CLAUDE.md §4.1 |

## 长会话

上下文接近上限时调用 `context-compress`；压缩完成后**立即重读**当前阶段对应 skill（见「用前重读纪律」）。

---

## 编排层反模式

通用反模式见 CLAUDE.md §5.4。编排层特有：

| 借口 | 为什么错 |
|------|---------|
| "这个 skill 上次读过，凭记忆用" | 上下文压缩后内容可能已丢失，用前重读是硬性要求 |
| "跳过 A3/B2 检查直接归档" | `doc-review` 一分钟的事；归档后返工要动 git 历史，成本翻倍 |
| "A0 不用问，直接开始解析" | 产出形式（单篇/拆分/存档）决定后续所有阶段，猜错即全部返工 |
