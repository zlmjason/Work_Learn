---
name: mineru-pdf-parser
description: >-
  基于 MinerU 云端 API 的文档智能解析工具。支持 PDF、Word、PPT、Excel、图片 等多种格式转换为结构化 Markdown，
  保留标题层级、表格结构、LaTeX 公式、多栏排版。支持单文件和批量处理。
  触发条件：用户提到"PDF转Markdown"、"Word转Markdown"、"解析文档"、"提取文档内容"、"PPT转文本"。
metadata:
  requires:
    - python3
    - pip
---

# MinerU 文档解析器

MinerU 是上海人工智能实验室开源的高精度文档解析工具，云端版本无需 GPU、无需本地模型，一条命令即可使用。

**支持格式**：PDF、Word (.doc/.docx)、PPT (.ppt/.pptx)、Excel (.xls/.xlsx)、图片 (.png/.jpg/.jpeg/.tiff/.bmp)

## 安装

### 方案 A：Python SDK（推荐，跨平台）

```bash
python3 -m pip install mineru-open-sdk
```

### 方案 B：Windows CLI

```powershell
irm https://cdn-mineru.openxlab.org.cn/open-api-cli/install.ps1 | iex
```

验证：
```bash
mineru-open-api version
```

## 使用方式

### 单文件转换（Python SDK）

```python
from mineru import MinerU

# 免登录快速模式（适合普通文档）
client = MinerU()
result = client.flash_extract("论文.pdf")
result.save_markdown("输出.md")

# 精准模式（适合复杂排版、大文件）
# 先在 https://mineru.net/apiManage/token 免费申请 Token
client = MinerU("your-api-token")
result = client.extract("论文.pdf")
result.save_markdown("输出.md")
```

### 排版格式控制（1.5倍行距 + 两端对齐）

脚本支持输出三种格式，通过 `-f` / `--format` 参数指定：

| 格式 | 命令 | 说明 |
|------|------|------|
| `md` | `python doc_to_md.py 报告.pdf` | 默认，纯 Markdown |
| `html` | `python doc_to_md.py 报告.pdf -f html` | 带 CSS 样式的网页，1.5倍行距+两端对齐+首行缩进 |
| `docx` | `python doc_to_md.py 报告.pdf -f docx` | Word 文档，1.5倍行距+两端对齐+首行缩进 |

**安装依赖**（按需）：
```bash
# HTML 输出需要
python3 -m pip install markdown

# Word 输出需要
python3 -m pip install python-docx
```

### 批量转换

```python
import os
from mineru import MinerU

client = MinerU()
input_dir = "./docs"
output_dir = "./markdowns"
os.makedirs(output_dir, exist_ok=True)

supported = (".pdf", ".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx",
             ".png", ".jpg", ".jpeg", ".tiff", ".bmp")

for fname in os.listdir(input_dir):
    if fname.lower().endswith(supported):
        fpath = os.path.join(input_dir, fname)
        try:
            result = client.flash_extract(fpath)
            out_path = os.path.join(output_dir, os.path.splitext(fname)[0] + ".md")
            result.save_markdown(out_path)
            print(f"✅ {fname}")
        except Exception as e:
            print(f"❌ {fname}: {e}")
```

### 封装脚本 CLI（推荐，含图片提取 + 格式控制）

```bash
# 单文件转换
cd .claude/skills/mineru-pdf-parser/scripts
python doc_to_md.py 报告.docx                    # 输出 md
python doc_to_md.py 报告.docx -f html             # 输出带样式的 HTML
python doc_to_md.py 报告.docx -f docx             # 输出 Word 文档
python pdf_to_md.py 论文.pdf -f html              # PDF 专用脚本

# 批量转换
python doc_to_md.py --batch ./docs -f html
python pdf_to_md.py --batch ./pdfs -f docx
```

### 官方 CLI 方式

```bash
# 单文件（自动识别格式）
mineru-open-api convert 论文.pdf -o 输出.md
mineru-open-api convert 报告.docx -o 输出.md
mineru-open-api convert 演示.pptx -o 输出.md

# 批量
mineru-open-api convert ./docs/* -o ./markdowns/
```

## 图片提取（必须步骤）

**⚠️ 重要：转换文档时必须同时提取图片，确保 Markdown 中的图片引用完整。**

MinerU `flash_extract()` 免登录模式**不返回图片数据**。转换完成后必须使用备用方案提取图片：

### docx 文件图片提取

```python
import os
from docx import Document

def extract_docx_images(docx_path, img_dir):
    os.makedirs(img_dir, exist_ok=True)
    doc = Document(docx_path)
    count = 0
    for rel in doc.part.rels.values():
        if 'image' in rel.reltype:
            image = rel.target_part
            ext = image.content_type.split('/')[-1]
            if ext == 'jpeg':
                ext = 'jpg'
            count += 1
            img_path = os.path.join(img_dir, f'image_{count:02d}.{ext}')
            with open(img_path, 'wb') as f:
                f.write(image.blob)
    return count
```

### pdf 文件图片提取

```python
import fitz  # PyMuPDF

def extract_pdf_images(pdf_path, img_dir):
    os.makedirs(img_dir, exist_ok=True)
    doc = fitz.open(pdf_path)
    count = 0
    for page_num in range(len(doc)):
        page = doc[page_num]
        images = page.get_images(full=True)
        for img_index, img in enumerate(images, start=1):
            xref = img[0]
            pix = fitz.Pixmap(doc, xref)
            if pix.n > 4:
                pix = fitz.Pixmap(fitz.csRGB, pix)
            count += 1
            img_path = os.path.join(img_dir, f'image_{count:02d}.png')
            pix.save(img_path)
            pix = None
    return count
```

### 图片引用路径更新

提取图片后，更新 Markdown 中的引用路径：

```python
import re

def update_image_refs(md_path, img_dir):
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()

    old_images = re.findall(r'!\[\]\(images/[a-f0-9]+\.\w+\)', content)
    extracted = sorted([f for f in os.listdir(img_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))])

    for i, old in enumerate(old_images):
        if i < len(extracted):
            new = f'![](images/{extracted[i]})'
            content = content.replace(old, new, 1)

    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(content)
```

## 完整转换流程（含图片提取）

```python
import os
from mineru import MinerU
from docx import Document
import re

def convert_with_images(file_path, output_dir=None):
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    if not output_dir:
        output_dir = os.path.dirname(file_path) or '.'

    md_path = os.path.join(output_dir, f'{base_name}.md')
    img_dir = os.path.join(output_dir, 'images')

    # 1. 文本转换
    client = MinerU()
    result = client.flash_extract(file_path)
    result.save_markdown(md_path)

    # 2. 图片提取
    ext = os.path.splitext(file_path)[1].lower()
    if ext == '.docx':
        extract_docx_images(file_path, img_dir)
    elif ext == '.pdf':
        extract_pdf_images(file_path, img_dir)

    # 3. 更新引用路径
    update_image_refs(md_path, img_dir)

    print(f'完成: {md_path}')
    print(f'图片: {img_dir}/')
```

## 输出内容

转换后的 Markdown 包含：
- **标题层级**：原文档的章节结构
- **表格**：Markdown 表格格式
- **公式**：LaTeX 格式（如 `$E=mc^2$`）
- **图片**：提取为单独文件，Markdown 中引用
- **多栏排版**：自动识别并正确顺序输出

## 关键参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `flash_extract()` | 免登录快速模式 | 无 Token 要求 |
| `extract()` | 精准模式（需 Token） | 大文件/复杂排版 |
| `save_markdown(path)` | 保存为 Markdown 文件 | - |
| `save_all(dir)` | 保存 md + 图片 + JSON（需 Token） | - |

## 适用场景

- 学术论文入库、知识库构建
- 财报/研报转 Markdown 做分析
- Word/PPT 技术文档转为可编辑格式
- Excel 表格内容提取为 Markdown
- 图片中的文字 OCR 并结构化
- RAG（检索增强生成）的文档预处理

## 限制

- 云端 API 需要网络连接
- 大文件（>100MB）建议使用精准模式（需 Token）
- 扫描件（纯图片 PDF）的 OCR 效果取决于原文质量
- `flash_extract()` 不返回图片，必须配合备用提取方案

## 替代方案

如果网络不可用或数据敏感需本地处理：
- 本地部署：`pip install magic-pdf`（需 Python 3.10-3.12 + 8GB 显存）
- 详见：[MinerU GitHub](https://github.com/opendatalab/MinerU)
