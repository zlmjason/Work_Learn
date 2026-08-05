# PDF Processing — 陷阱与常见失败模式

本文件记录处理 PDF 时容易犯的错误（Gotchas）。

---

## 1. `pypdf.extract_text()` 对复杂 PDF 返回乱码

**表现**：提取的文本顺序错乱、字符缺失或全是乱码。

**原因**：PDF 内部结构不一定按阅读顺序存储文本；复杂排版、嵌入字体子集、缺少 ToUnicode 映射都会导致提取失败。

**正确做法**：
- 简单文档用 `pypdf`
- 需要保留布局时用 `pdfplumber` 或 `pdftotext -layout`
- 扫描件必须 OCR

---

## 2. 误以为安装了 `pytesseract` 就能 OCR

**表现**：运行 OCR 代码时报错 "tesseract not found"。

**原因**：`pytesseract` 只是 Python 包装器，必须单独安装 Tesseract-OCR 引擎。`pdf2image` 也需要 poppler 的 `pdftoppm`。

**正确做法**：
- Windows：安装 [Tesseract-OCR](https://github.com/UB-Mannheim/tesseract/wiki) 和 [poppler](https://github.com/oschwartz10612/poppler-windows/releases)
- 本项目当前状态：Tesseract-OCR 引擎和 poppler **暂缓安装**，OCR 扫描件暂不支持

---

## 3. `pdfplumber` 表格提取漏掉合并单元格

**表现**：表格少列、少行或把合并单元格拆成多个空单元格。

**原因**：`pdfplumber` 基于线条和文本位置推断表格结构，非标准边框、无边框表格、合并单元格容易识别失败。

**正确做法**：
- 对关键表格做人工复核
- 结合 `page.extract_text()` 做交叉验证
- 复杂表格考虑用 Camelot 等专用工具

---

## 4. 用 `reportlab` 时 Platypus 流式对象顺序错误

**表现**：生成的 PDF 内容缺失、顺序错乱或抛出异常。

**原因**：`reportlab.platypus` 的 `Story` 列表必须按顺序添加 `Paragraph`、`Table`、`Image` 等 Flowable，且某些对象不能嵌套。

**正确做法**：严格按文档顺序构建 `story`，复杂布局先用小例子验证。

---

## 5. `pdftotext` / `pdfimages` 等命令在 Windows 上不可用

**表现**：命令行提示 "pdftotext 不是内部或外部命令"。

**原因**：这些工具属于 poppler-utils，Windows 默认不带，本项目也未安装 poppler。

**正确做法**：优先使用 Python 库（`pypdf`、`pdfplumber`），避免依赖外部 poppler 命令。

---

## 6. 合并/拆分 PDF 后丢失书签或表单

**表现**：合并后的 PDF 没有原书签，或表单字段失效。

**原因**：`pypdf` 默认只复制页面，不复制文档级元数据、书签、交互式表单。

**正确做法**：如需保留书签，使用 `writer.clone_reader_document_root(reader)` 或 `append_pages_from_reader` 的附加选项；复杂表单建议用 `pdftk` 或 `qpdf`。

---

## 7. OCR 时不指定语言导致中文识别失败

**表现**：中文 PDF OCR 后全是英文或乱码。

**原因**：Tesseract 默认语言包是英文，中文需要安装 `chi_sim` 或 `chi_tra` 语言包并在 `image_to_string()` 中指定 `lang='chi_sim'`。

**正确做法**：

```python
pytesseract.image_to_string(image, lang='chi_sim+eng')
```

---

## 8. 加密 PDF 未解密直接操作

**表现**：读取加密 PDF 时抛出 `PdfReadError` 或元数据为空。

**正确做法**：先解密：

```python
reader = PdfReader("encrypted.pdf")
if reader.is_encrypted:
    reader.decrypt("password")
```

---

## 9. 图片提取后格式/raw 数据需要二次处理

**表现**：`pdfimages` 提取出 `.ppm` 或 `.raw` 文件，无法直接使用。

**正确做法**：使用 `-j`（JPEG）、`-png` 等参数指定输出格式，或改用 Python 的 `pymupdf`/`pdf2image` 提取。
