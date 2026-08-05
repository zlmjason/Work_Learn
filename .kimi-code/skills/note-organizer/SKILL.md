---
name: note-organizer
description: Organize Markdown notes into the correct directory and rename them according to the project's AGENTS.md conventions. Use when the user drops a new .md file in the workspace root or Inbox and wants it placed under the proper layer with a canonical filename. Do NOT use for creating new notes from scratch (use mcu-note-creator), for content/format compliance review (use doc-review), or for Obsidian wikilink and index-note management (use obsidian-vault).
metadata:
---

# Note Organizer

把车规 MCU 知识库中未归档的 Markdown 笔记，按照 `AGENTS.md` 的目录层次和文件命名规范，自动移动到正确位置并重命名。

## 触发条件

用户输入以下任意一种表达时调用本 skill：

- "把这个 md 放到合适位置"
- "整理这个文件"
- "命名规范一下"
- "放到对应目录"
- "同理"（在已有同类操作上下文后）
- "把这篇笔记归档"
- "这个文件该放哪"

## 快速参考

| 情况 | 操作 |
|------|------|
| 新笔记在根目录或 `00_Inbox_临时收集/` | 读取内容 → 判断主题层次 → 选择目录 → 按命名规则重命名 → `mv` → `git status` 确认 |
| 文件名已比较规范但位置不对 | 只移动目录，必要时微调文件名 |
| 同名文件已存在 | 提示用户，不要覆盖 |
| 无法判断层次 | 移动到 `00_Inbox_临时收集/` 并说明原因 |
| 用户要求提交 | 按 `git-upload-push` skill 或标准 git flow 提交 |

**常见陷阱**：详见 [`gotchas.md`](./gotchas.md)。

**详细用法**：目录判断逻辑、命名前缀对照表、示例见 [`reference.md`](./reference.md)。

## 输出格式

执行后向用户说明：

```markdown
已将文件整理到规范位置：

- **原文件**：`原路径.md`
- **新位置**：`目标目录/规范文件名.md`
- **命名依据**：根据 AGENTS.md 第 2.2 节「文件命名规则」中的 `{前缀}` 规则

当前 git 状态：

```text
?? 目标目录/规范文件名.md
```
```

## 文件结构

```
note-organizer/
├── SKILL.md      ← 本文件（入口与触发条件）
├── reference.md  ← 目录映射、命名规则、示例
├── gotchas.md    ← 常见陷阱与失败模式
└── config.json   ← 目录与前缀映射表
```

## 相关技能

- [`obsidian-vault`](./../obsidian-vault/SKILL.md) — Obsidian 知识库整理
- [`self-improving-agent`](./../self-improving-agent/SKILL.md) — 记录整理过程中的踩坑与改进
- [`git-upload-push`](./../git-upload-push/SKILL.md) — 整理后一键提交推送
