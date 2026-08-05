---
name: docx-cn
description: "Create, read, and edit Word (.docx) documents. Trigger when the user mentions Word, docx, document creation, document editing, tracked changes, comments, tables, or images in Word documents. 触发词：Word、文档、docx."
metadata:
  openclaw:
    emoji: 📄
    fork-of: "https://github.com/anthropics/skills"
---

# DOCX creation, editing, and analysis

Word (.docx) 文档处理指南：读取、新建、编辑。

## 触发条件

用户提到以下任一表达时调用本 skill：

- "Word 文档" / "docx"
- "创建 Word 文档"
- "编辑 Word 文档"
- "文档里加表格/图片"
- "修订模式" / "批注"
- "把 Word 转成 Markdown/PDF"
- "doc 转 docx"

## 快速参考

| 任务 | 方式 |
|------|------|
| 读取/分析内容 | `pandoc --track-changes=all doc.docx -o out.md` |
| 查看原始 XML | `python scripts/office/unpack.py doc.docx unpacked/` |
| 新建文档 | `npm install -g docx`，用 `docx-js` 生成 |
| 编辑已有文档 | 解压 → 编辑 XML → `pack.py` 重新打包 |
| 接受所有修订 | `python scripts/accept_changes.py in.docx out.docx` |
| `.doc` 转 `.docx` | `python scripts/office/soffice.py --convert-to docx file.doc` |
| 验证生成文件 | `python scripts/office/validate.py doc.docx` |

## 文件结构

```
docx-cn/
├── SKILL.md       ← 本文件（入口与触发条件）
├── reference.md   ← docx-js 用法、XML 编辑、XML 参考、依赖
├── gotchas.md     ← 15 条常见陷阱（A4 默认、表格宽度、ImageRun type 等）
├── config.json    ← 依赖、脚本命令、关键规则清单
├── LICENSE.txt
└── scripts/
    ├── accept_changes.py
    ├── comment.py
    └── office/      ← unpack.py, pack.py, validate.py, soffice.py 等
```

## 核心规则

- `.docx` 是 ZIP + XML
- `docx-js` 默认 A4，需要显式设置页面尺寸
- 列表用 `LevelFormat.BULLET`，不要手动插 `•`
- 表格用 `WidthType.DXA`，同时设 `columnWidths` 和 cell `width`
- `ImageRun` 必须传 `type`
- 编辑 XML 时保留 `<w:rPr>`，修订作者用 "Claude"

详见 [`gotchas.md`](./gotchas.md)。

## 详细用法

docx-js 完整示例、XML 编辑流程、XML 参考、依赖说明见 [`reference.md`](./reference.md)。
