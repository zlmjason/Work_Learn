# Patterns

复发性模式跟踪。记录反复出现的问题、最佳实践候选、以及适合晋升到 `.claude/CLAUDE.md` 或提取为 Skill 的模式。

> 新增模式请使用 `PAT-KEY` 编号，例如 `PAT-install-cross-platform`。
> 当 `Recurrence-Count >= 3` 且跨至少 2 个不同任务出现时，应考虑晋升。

---

## 晋升规则

一个模式满足以下全部条件时应晋升：

1. `Recurrence-Count >= 3`
2. 在至少 2 个不同任务/场景中出现过
3. 发生在 30 天窗口内

晋升目标：

| 模式类型 | 晋升目标 |
|----------|----------|
| 项目规范/事实 | `.claude/CLAUDE.md` |
| 工作流/自动化 | `AGENTS.md` 或 `.claude/CLAUDE.md` |
| 可复用能力 | `.claude/skills/` 下的新 Skill |
| 个人偏好/跨项目 | `.claude/memory/` |

---

## [PAT-install-cross-platform] 跨平台安装脚本需要 Windows 适配

**Category**: harden
**Description**: 官方 Skill/工具安装脚本多为 bash（Homebrew/curl），Windows 下需要 PowerShell 适配或 Python 替代实现。
**First Seen**: 2026-05-11
**Last Seen**: 2026-05-11
**Recurrence Count**: 1
**Affected Files/Areas**: skills/summarize, skillhub CLI
**Status**: candidate
**Promoted To**: —

---

## [PAT-workflow-llm-fallback] 无 API Key 时 LLM 工作流降级

**Category**: simplify
**Description**: 当没有第三方 LLM API Key 时，将"本地提取"与"Kimi 总结"解耦，避免工具因缺少 Key 而无法使用。
**First Seen**: 2026-05-11
**Last Seen**: 2026-05-11
**Recurrence Count**: 1
**Affected Files/Areas**: skills/summarize
**Status**: candidate
**Promoted To**: —

---

## [PAT-skill-folder-structure] Skill 单文件膨胀

**Category**: simplify
**Description**: Skill 内容不断增长后，单文件 SKILL.md 导致模型上下文负担重、触发信号被淹没。应拆分为多文件结构。
**First Seen**: 2026-06-28
**Last Seen**: 2026-06-28
**Recurrence Count**: 1
**Affected Files/Areas**: .claude/skills/*
**Status**: resolved
**Promoted To**: `.claude/CLAUDE.md` 技能结构约定 + 所有本地 Skill 已重构

---

## 模板

```markdown
## [PAT-KEY] 模式名称

**Category**: simplify | harden
**Description**: [模式描述]
**First Seen**: YYYY-MM-DD
**Last Seen**: YYYY-MM-DD
**Recurrence Count**: N
**Affected Files/Areas**: [文件或领域]
**Status**: candidate | promoted | resolved
**Promoted To**: [文件路径，如未晋升则填 —]
```
