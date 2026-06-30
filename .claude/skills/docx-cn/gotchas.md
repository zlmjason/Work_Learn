# DOCX Processing — 陷阱与常见失败模式

本文件记录处理 Word 文档时容易犯的错误（Gotchas）。

---

## 1. docx-js 默认页面是 A4，不是 US Letter

**表现**：生成的文档在不同电脑上打开时页面尺寸不一致。

**正确做法**：始终显式设置 `page.size` 为 `12240 x 15840`（US Letter）或目标纸张尺寸。

---

## 2. 手动插入 Unicode 项目符号

**表现**：列表项写成 `"• Item"` 或 `"• Item"`。

**后果**：不是真正的 Word 列表，编辑时无法调整缩进或样式。

**正确做法**：使用 `LevelFormat.BULLET` 配置 numbering。

---

## 3. 表格只设 columnWidths 没设 cell width

**表现**：表格在某些平台（如 Google Docs）渲染错位。

**正确做法**：同时设置 `table.columnWidths` 和每个 `TableCell.width`，且数值对应。

---

## 4. 使用 `WidthType.PERCENTAGE`

**表现**：表格宽度用百分比。

**后果**：Google Docs 等在线工具可能无法正确渲染。

**正确做法**：始终使用 `WidthType.DXA`。

---

## 5. 表格 shading 用 `ShadingType.SOLID`

**表现**：表格背景变成黑色。

**正确做法**：使用 `ShadingType.CLEAR`。

---

## 6. `ImageRun` 未传 `type`

**表现**：图片无法显示或生成失败。

**正确做法**：必须传 `type: "png"` / `"jpg"` 等。

---

## 7. `PageBreak` 未放入 `Paragraph`

**表现**：生成无效 XML，Word 打开报错。

**正确做法**：`new Paragraph({ children: [new PageBreak()] })`。

## 8. 在文本中用 `\n`

**表现**：docx-js 不支持 `
` 换行，输出异常。

**正确做法**：用多个 `Paragraph` 元素分段。

---

## 9. 标题使用自定义样式而不是 `HeadingLevel`

**表现**：目录（TOC）无法识别标题。

**正确做法**：段落使用 `heading: HeadingLevel.HEADING_1`，样式 ID 用 `"Heading1"` 等覆盖内置样式。

---

## 10. 编辑 XML 时未保留 `<w:rPr>`

**表现**：添加修订后，文字变回默认格式（丢失加粗、字号等）。

**正确做法**：复制原始 run 的 `<w:rPr>` 到新的 `<w:del>` / `<w:ins>` 中。

---

## 11. 批注范围标记放错位置

**表现**：`<w:commentRangeStart>` / `<w:commentRangeEnd>` 放在 `<w:r>` 内部。

**正确做法**：它们是 `<w:p>` 的直接子元素，与 `<w:r>` 同级。

---

## 12. 新增内容使用普通引号而不是 XML 实体

**表现**：Word 中引号/撇号显示为直引号，或 XML 解析失败。

**正确做法**：使用智能引号实体：`&#x2018;`、`&#x2019;`、`&#x201C;`、`&#x201D;`。

---

## 13. 直接用 Python 脚本做批量 XML 编辑

**表现**：用复杂脚本生成 XML，结果难以调试。

**正确做法**：先用 `unpack.py` 解压，再用 Edit 工具做精确字符串替换，最后用 `pack.py` 打包。

---

## 14. 解压后忘记运行 `pack.py`

**表现**：手动改了 XML 但没有重新打包。

**正确做法**：编辑后必须运行 `pack.py` 生成新的 `.docx`。

---

## 15. 验证失败时忽略 auto-repair 范围

**表现**：`pack.py` 修复了部分问题但还有 schema 错误，未进一步检查。

**正确做法**：`pack.py` 只能修复 `durableId` 和 `xml:space`，XML 结构错误必须手工修正。
