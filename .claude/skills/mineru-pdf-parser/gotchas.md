# MinerU 文档解析器 — 陷阱与常见失败模式

本文件记录使用 `mineru-pdf-parser` 时容易犯的错误（Gotchas）。

---

## 1. `flash_extract()` 不返回图片

**表现**：转换后 Markdown 里有 `![](images/xxxx.png)`，但 `images/` 目录为空或图片不存在。

**原因**：MinerU 的 `flash_extract()` 免登录模式只返回文本结构，不返回图片二进制数据。

**正确做法**：转换后必须调用备用图片提取逻辑（见 [`reference.md`](./reference.md) 的「图片提取」章节）。PDF 用 PyMuPDF，docx 用 python-docx 或 zipfile。

---

## 2. `config.json` 不再内置 Token

**表现**：脚本运行提示缺少 Token 或解析失败。

**原因**：旧版 `config.json` 包含硬编码 JWT，已删除。现在必须通过环境变量 `MINERU_API_TOKEN` 或显式传入。

**正确做法**：

```bash
export MINERU_API_TOKEN="your-token"
python doc_to_md.py 论文.pdf
```

或在 Python 中显式：

```python
from mineru import MinerU
client = MinerU("your-token")
```

---

## 3. 混淆免登录模式与 Token 模式

**表现**：用户期望复杂排版、扫描件、大文件都能用免登录模式完美解析。

**后果**：排版错乱、公式丢失、表格识别失败。

**正确做法**：
- 普通文档、可编辑 PDF/Word → `flash_extract()`（免登录）
- 复杂排版、扫描件、大文件（>100MB）→ `extract()`（需 Token）

---

## 4. 扫描件 OCR 效果不可控

**表现**：扫描版 PDF 转出的 Markdown 全是乱码或大量错字。

**原因**：MinerU 云端 OCR 效果取决于原图分辨率、清晰度、字体。低质量扫描件无法保证准确率。

**正确做法**：
- 优先使用原生可编辑 PDF/Word
- 扫描件先检查分辨率（建议 ≥ 300 DPI）
- 对 OCR 结果必须人工校对

---

## 5. 缺少可选依赖导致格式输出失败

**表现**：指定 `-f html` 或 `-f docx` 后报错。

**原因**：
- HTML 输出需要 `markdown` 库
- DOCX 输出需要 `python-docx` 库
- PDF 图片提取需要 `PyMuPDF` 库

**正确做法**：按需安装，脚本会在缺失时给出明确提示。

---

## 6. 批量模式图片命名冲突

**表现**：批量转换多个 PDF 后，某些图片被覆盖或引用混乱。

**原因**：默认把所有输出图片放进同一个 `images/` 目录，不同文档的图片可能重名。

**正确做法**：为每个文档单独创建子目录存放图片，或在转换后检查 `images/` 内容。

---

## 7. 图片引用正则匹配失败

**表现**：提取图片后，Markdown 中的图片引用仍是 MinerU 生成的哈希路径，未替换为实际文件名。

**原因**：`update_image_refs()` 使用正则 `images/[a-f0-9]+\.\w+` 匹配，如果 MinerU 未来改变图片命名规则，正则会失效。

**正确做法**：转换后人工检查图片引用；如发现匹配失败，更新正则或手动替换。

---

## 8. 未处理网络异常

**表现**：云端 API 超时或返回错误，脚本直接退出。

**原因**：MinerU 依赖网络连接，超时、限流、Token 失效都会导致失败。

**正确做法**：
- 检查网络连接
- 检查 Token 是否过期
- 对批量任务增加重试逻辑

---

## 9. 把 MinerU 当作通用 OCR 工具

**表现**：用 MinerU 处理单张低质量图片，期望得到完美文本。

**原因**：MinerU 强项是文档级版面分析，不是单张图片 OCR。

**正确做法**：单张图片 OCR 优先考虑 `pytesseract` 或专用 OCR 服务；MinerU 更适合多页文档。

---

## 10. 忽略本地部署替代方案

**表现**：网络不稳定或数据敏感时仍坚持用云端 API。

**正确做法**：敏感数据或频繁调用场景，考虑本地部署 `magic-pdf`（需 GPU）。详见 [`reference.md`](./reference.md)「替代方案」。

---

## 11. 超过 200 页的 PDF 被 API 直接拒绝

**表现**：提交后任务报 `number of pages exceeds limit (200 pages), please split the file and try again`。

**原因**：MinerU 云端 API 单文件上限 200 页，与文件体积无关。

**正确做法**：用 `doc_to_md_split.py` 自动完成「切块 → 逐块精准模式解析 → 合并 `full.md` → 清理中间产物」，图片哈希命名多块共用一个 `images/` 无冲突：

```bash
py -3 scripts/doc_to_md_split.py 大书.pdf --check   # 预演：只看切块计划，不调 API
py -3 scripts/doc_to_md_split.py 大书.pdf           # 正式转换（断点续跑：已完成的块自动跳过）
```

若中途失败，重跑同一命令即可续传；全部块成功后才合并 `full.md`，不会产出半成品。
