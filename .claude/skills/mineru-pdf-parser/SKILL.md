---
name: mineru-pdf-parser
description: Convert PDF, Word, PPT, Excel, and images to structured Markdown via MinerU cloud API. Preserves headings, tables, LaTeX formulas, and multi-column layouts. Trigger when the user mentions "PDF to Markdown", "Word to Markdown", "parse document", "extract document content", "PPT to text", "convert document", or needs document structure preservation. Do NOT use for quick content extraction from webpages or YouTube, or when only a rough summary is needed (use summarize).
metadata:
  requires:
    - python3
    - pip
---

# MinerU 文档解析器

基于 MinerU 云端 API 的文档智能解析工具，支持 PDF、Word、PPT、Excel、图片转换为结构化 Markdown，无需 GPU。

## 触发条件

用户提到以下任一表达时调用本 skill：

- "PDF 转 Markdown" / "PDF转Markdown"
- "Word 转 Markdown" / "Word转Markdown"
- "PPT 转文本" / "PPT转文本"
- "解析文档" / "提取文档内容"
- "把这份文档转成 Markdown"
- 需要保留原文档的标题层级、表格、公式、多栏排版

## 快速参考

| 情况 | 操作 |
|------|------|
| 单文件转换 | `python .claude/skills/mineru-pdf-parser/scripts/doc_to_md.py <文件路径>` |
| 批量转换 | `python .claude/skills/mineru-pdf-parser/scripts/doc_to_md.py --batch <目录>` |
| 输出 HTML/Word | 加上 `-f html` 或 `-f docx` |
| 需要图片 | 脚本会自动提取并更新引用，但 flash 模式不返回图片数据 |
| 缺少 API Token | 设置环境变量 `MINERU_API_TOKEN`，或使用免登录 flash 模式 |

## 支持格式

PDF、Word（`.doc` / `.docx`）、PPT（`.ppt` / `.pptx`）、Excel（`.xls` / `.xlsx`）、图片（`.png` / `.jpg` / `.jpeg` / `.tiff` / `.bmp`）

## 一分钟示例

```bash
# 安装
python3 -m pip install mineru-open-sdk

# 单文件转 Markdown
python .claude/skills/mineru-pdf-parser/scripts/doc_to_md.py 论文.pdf

# 输出带样式的 HTML
python .claude/skills/mineru-pdf-parser/scripts/doc_to_md.py 论文.pdf -f html
```

## 文件结构

```
mineru-pdf-parser/
├── SKILL.md      ← 本文件（入口与触发条件）
├── reference.md  ← 详细安装、用法、图片提取、完整工作流
├── gotchas.md    ← 常见陷阱与失败模式
├── config.json   ← 配置与依赖说明
└── scripts/
    ├── doc_to_md.py  ← 通用文档转换脚本
    └── pdf_to_md.py  ← PDF 专用脚本
```

## 常见陷阱

- `flash_extract()` 不返回图片，必须额外提取
- 扫描件 OCR 效果取决于原图质量
- 大文件/复杂排版需要 API Token
- `config.json` 不再内置 Token，需通过环境变量 `MINERU_API_TOKEN` 提供

详见 [`gotchas.md`](./gotchas.md)。

## 详细用法

安装、Token 配置、Python SDK、批量转换、图片提取、限制与替代方案见 [`reference.md`](./reference.md)。
