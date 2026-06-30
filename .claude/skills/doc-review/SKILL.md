---
name: doc-review
description: Review Markdown notes against project conventions. Trigger when the user asks "检查这篇笔记", "review这个文档", "格式对吗", "文件名规范吗", "这篇笔记符合规范吗".
metadata:
---

# Doc Review

检查仓库中的 Markdown 笔记是否符合项目规范。

## 触发条件

用户提到以下任一表达时调用本 skill：

- "检查这篇笔记"
- "review 这个文档"
- "格式对吗"
- "文件名规范吗"
- "这篇笔记符合规范吗"
- "帮我审一下这篇 Markdown"

## 快速参考

| 检查项 | 说明 |
|--------|------|
| 文件名 | 无空格、正确前缀、英文缩写大写 |
| 标题结构 | 有 `#` 标题、`##` 章节正确 |
| 必要章节 | 9 段式模板中的关键章节是否存在 |
| 代码块 | 是否标注语言类型 |
| 技术术语 | 是否保留英文（抽样检查） |
| 目录放置 | 文件是否放在正确层次 |
| TODO/FIXME | 是否残留未处理标记 |

## 一分钟示例

```bash
# 检查单个文件
python .claude/skills/doc-review/scripts/doc-review.py "01_Hardware_硬件层/05_Peripherals/01_Communication/01_SPI/HW_Periph_Comm_SPI_Specification.md"

# 检查整个目录
python .claude/skills/doc-review/scripts/doc-review.py "01_Hardware_硬件层/05_Peripherals"
```

## 文件结构

```
doc-review/
├── SKILL.md              ← 本文件（入口与触发条件）
├── reference.md          ← 详细检查规则与判定标准
├── gotchas.md            ← 常见误报与陷阱
├── config.json           ← 检查类别、必要章节、缩写列表
└── scripts/
    └── doc-review.py     ← 检查脚本
```

## 常见陷阱

- Obsidian 双链 `[[...]]` 是合法格式
- 中文标点在某些代码块中可能故意存在
- 复杂 Mermaid 图容易误报（首版未深入校验）
- 旧归档文件可能不完全符合当前规范

详见 [`gotchas.md`](./gotchas.md)。

## 详细检查规则

完整规则、判定标准、脚本用法见 [`reference.md`](./reference.md)。
