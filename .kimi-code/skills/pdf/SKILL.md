---
name: pdf
description: Process, extract, create, merge, split, or OCR PDF documents programmatically. Trigger when the user mentions PDF text extraction, table extraction, merging/splitting PDFs, creating PDFs, filling forms, or OCR on scanned documents.
license: Proprietary. LICENSE.txt has complete terms
---

# PDF Processing Guide

本项目 PDF 处理指南，覆盖 Python 库（`pypdf`、`pdfplumber`、`reportlab`）和命令行工具（`qpdf`、`pdftotext`、`pdftk`）。

## 触发条件

用户提到以下任一需求时调用本 skill：

- "提取 PDF 文字/表格"
- "合并/拆分 PDF"
- "创建/生成 PDF"
- "PDF 转图片/图片转 PDF"
- "PDF 加水印/加密/解密"
- "扫描件 OCR"
- "填写 PDF 表单"

## 快速参考

| 任务 | 推荐工具 | 一句话操作 |
|------|----------|-----------|
| 合并 PDF | `pypdf` | `PdfWriter.add_page()` 循环添加 |
| 拆分 PDF | `pypdf` | 逐页创建新的 `PdfWriter` |
| 提取文本 | `pdfplumber` | `page.extract_text()` |
| 提取表格 | `pdfplumber` + `pandas` | `page.extract_tables()` 后转 DataFrame |
| 创建 PDF | `reportlab` | `Canvas` 或 `SimpleDocTemplate` |
| 命令行合并 | `qpdf` | `qpdf --empty --pages ...` |
| OCR 扫描件 | `pytesseract` + `pdf2image` | 先转图片再 OCR |
| 填表单 | `pypdf` / `pdf-lib` | 见 `forms.md` |

## 一分钟示例

```python
from pypdf import PdfReader

reader = PdfReader("document.pdf")
print(f"Pages: {len(reader.pages)}")

text = ""
for page in reader.pages:
    text += page.extract_text()
```

## 文件结构

```
pdf/
├── SKILL.md       ← 本文件（入口与触发条件）
├── reference.md   ← Python 库/命令行/常见任务详细示例
├── gotchas.md     ← 常见陷阱（OCR 依赖、表格提取、加密等）
├── config.json    ← 已安装库与缺失系统依赖说明
└── LICENSE.txt
```

## 常见陷阱

- `pytesseract` 需要系统级 Tesseract-OCR 引擎，仅装 Python 库不够
- `pdf2image` 需要 poppler，本项目暂缓安装
- 扫描件 OCR 中文需指定 `lang='chi_sim'`
- `pdfplumber` 对合并单元格/无边框表格容易漏识别
- `pypdf` 合并 PDF 默认不保留书签和表单

详见 [`gotchas.md`](./gotchas.md)。

## 详细用法

Python 库完整示例、命令行工具、常见任务见 [`reference.md`](./reference.md)。
