# Skill Registry

本仓库所有 Claude Code Skill 的注册表，记录 Skill 与来源学习项的对应关系。

> 新增 Skill 时请在此登记；从 Learning 提取为 Skill 时，请在原 Learning 中更新 `Status: promoted_to_skill` 并填写 `Skill-Path`。

---

## 本地 Skill 清单

| Skill | 路径 | 用途 | 来源 Learning | 状态 |
|-------|------|------|---------------|------|
| context-compress | `.claude/skills/context-compress/` | 上下文压缩与摘要 | — | active |
| docx-cn | `.claude/skills/docx-cn/` | Word 文档处理 | — | active |
| doc-review | `.claude/skills/doc-review/` | Markdown 规范检查 | PAT-skill-folder-structure | active |
| find-skills | `.claude/skills/find-skills/` | 搜索/安装外部技能 | — | active |
| mcu-note-creator | `.claude/skills/mcu-note-creator/` | 按规范创建 MCU 笔记 | — | active |
| mineru-pdf-parser | `.claude/skills/mineru-pdf-parser/` | PDF/Word/PPT/Excel 转 Markdown | — | active |
| pdf | `.claude/skills/pdf/` | PDF 处理指南 | — | active |
| safespi-evaluator | `.claude/skills/safespi-evaluator/` | SafeSPI 支持性评估 | — | active |
| self-improving-agent | `.claude/skills/self-improving-agent/` | 持续改进日志 | — | active |
| summarize | `.claude/skills/summarize/` | 内容提取/摘要 | LRN-20260511-005 | active |

---

## 来源 Learning 追踪

| Learning ID | Skill | 说明 |
|-------------|-------|------|
| LRN-20260511-005 | summarize | 无 API Key 时内容提取与 LLM 摘要解耦 |
| PAT-skill-folder-structure | doc-review 等 | Skill 单文件膨胀，重构为多文件结构 |

---

## 新增 Skill 流程

1. 在 `.claude/skills/<skill-name>/` 创建多文件结构
2. 在 `SKILL.md` 中写入触发条件和快速参考
3. 如来源于某条 Learning，更新该 Learning 的 `Status: promoted_to_skill`
4. 在本注册表中添加一行
5. 运行 `python .claude/skills/self-improving-agent/scripts/update-index.py` 更新索引
