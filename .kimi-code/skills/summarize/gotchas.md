# Summarize — 陷阱与常见失败模式

本文件记录使用 `summarize` 时容易犯的错误（Gotchas）。

---

## 1. 无 API key 时不会自动调用 LLM

**表现**：运行 `summarize.py "URL"` 后没有摘要，只输出原文。

**原因**：本项目没有配置第三方 LLM API 密钥。脚本检测到无 key 时自动回退到 `--print-content` 模式。

**正确做法**：
- 无 key 时显式使用 `--print-content`，把输出复制到对话让 Kimi 总结
- 有 key 时设置对应环境变量

---

## 2. `--print-content` 输出不会自动进入 Kimi 上下文

**表现**：以为脚本已经把内容传给 Kimi。

**原因**：`summarize.py` 是独立 CLI 工具，不会与当前 Claude Code / Kimi 会话通信。

**正确做法**：将 `--print-content` 输出复制粘贴到对话中，或先用 `--output` 保存到文件再让 Kimi 读取。

---

## 3. 输入超过 60K 字符被自动截断

**表现**：长文档的摘要后半部分丢失。

**原因**：脚本硬编码了 60,000 字符截断，防止超出 LLM 上下文窗口。

**正确做法**：
- 对超长文档先拆分章节
- 使用 [`pdf`](../pdf/SKILL.md) 或 [`mineru-pdf-parser`](../mineru-pdf-parser/SKILL.md) 提取关键部分
- 多次分段总结后再合并

---

## 4. `--firecrawl` 当前被忽略

**表现**：设置 `--firecrawl auto` 后行为没有变化。

**原因**：当前实现未集成 Firecrawl 服务。

**正确做法**：如需处理被屏蔽网站，先用其他工具获取内容，再本地保存后用 `--print-content` 提取。

---

## 5. YouTube 提取依赖 `yt-dlp`

**表现**：YouTube 链接只返回标题和描述，没有字幕。

**原因**：`yt-dlp` 未安装或视频没有字幕。

**正确做法**：

```bash
pip install yt-dlp
```

并确保目标视频有可访问字幕。

---

## 6. PDF 提取依赖 `PyPDF2`

**表现**：PDF 文件报错 "PyPDF2 is required"。

**原因**：可选依赖未安装。

**正确做法**：

```bash
pip install PyPDF2
```

复杂 PDF 建议先用 [`pdf`](../pdf/SKILL.md) 或 [`mineru-pdf-parser`](../mineru-pdf-parser/SKILL.md) 处理。

---

## 7. 环境变量名容易写错

**表现**：明明设了 key，脚本仍提示找不到。

**原因**：Google 支持多个别名，但其他 provider 只认一个。例如 OpenAI 必须是 `OPENAI_API_KEY`，不是 `OPEN_API_KEY`。

**正确做法**：对照 [`reference.md`](./reference.md) 的 provider 表格设置。

---

## 8. JSON 输出 key 会变化

**表现**：解析 `--json` 输出时有时 key 是 `summary`，有时是 `content`。

**原因**：有 API key 且非 `--print-content` 模式时 key 为 `summary`；无 key 或 `--print-content` 时 key 为 `content`。

**正确做法**：处理 JSON 时同时兼容两个 key，或始终使用 `--print-content` 保持 `content`。

---

## 9. Windows 包装器路径问题

**表现**：直接双击 `summarize.cmd` 或在非脚本目录调用时找不到 `summarize.py`。

**原因**：包装器使用相对路径引用同目录下的 Python 脚本。

**正确做法**：在 Git Bash / MSYS2 中使用绝对路径或确保 `.cmd` 与 `.py` 在同一目录。

---

## 10. 默认模型与实际调用模型不一致

**表现**：CLI 默认显示 `google/gemini-3-flash-preview`，但代码中 `call_gemini()` 硬编码了 `gemini-2.0-flash`。

**原因**：当前实现为兼容旧版 API 端点，模型 ID 在调用处固定。

**正确做法**：如需指定其他 Gemini 模型，注意当前端点可能不支持，建议用 `--print-content` 后交给 Kimi。
