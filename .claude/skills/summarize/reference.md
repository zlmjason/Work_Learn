# Summarize — 详细使用指南

本文件是 `summarize` Skill 的详细参考。如果你只想知道触发条件和快速入口，请阅读 [`SKILL.md`](./SKILL.md)。

**重要**：本项目当前**没有第三方 LLM API 密钥**，因此默认使用 `--print-content` 模式：只提取内容，不调用 LLM，然后把内容复制到对话中让 Kimi 总结。

---

## 安装

依赖（必需）：

```bash
pip install requests beautifulsoup4
```

按需安装：

```bash
pip install PyPDF2    # PDF 内容提取
pip install yt-dlp    # YouTube 字幕/描述提取
```

Windows 包装器：`summarize.cmd`（与本脚本同目录）。

---

## 使用方式

### 1. 无 API key 模式（本项目默认）

```bash
python .claude/skills/summarize/summarize.py "https://example.com" --print-content

# 保存到文件
python .claude/skills/summarize/summarize.py "https://example.com" --print-content --output doc.md
```

输出内容可直接复制到对话，交给 Kimi 总结。

### 2. 有 API key 模式

设置环境变量后，可直接生成摘要：

```bash
export GEMINI_API_KEY="your-key"
python .claude/skills/summarize/summarize.py "https://example.com"
```

支持 provider：

| Provider | 环境变量 |
|----------|----------|
| Google/Gemini | `GEMINI_API_KEY`（或 `GOOGLE_GENERATIVE_AI_API_KEY`、`GOOGLE_API_KEY`） |
| OpenAI | `OPENAI_API_KEY` |
| Anthropic | `ANTHROPIC_API_KEY` |
| xAI | `XAI_API_KEY` |

### 3. 本地文件

```bash
# 文本/PDF
python .claude/skills/summarize/summarize.py "/path/to/file.pdf" --print-content

# YouTube
python .claude/skills/summarize/summarize.py "https://youtu.be/xxxxx" --youtube auto --print-content
```

---

## Flag 详解

| Flag | 说明 | 示例 |
|------|------|------|
| `--model` | 指定模型，默认 `google/gemini-3-flash-preview` | `--model openai/gpt-4o` |
| `--length` | 摘要长度：`short`/`medium`/`long`/`xl`/`xxl` 或字符数 | `--length long` |
| `--max-output-tokens` | 最大输出 tokens | `--max-output-tokens 2048` |
| `--extract-only` | 仅提取正文，不总结（URL） | `--extract-only` |
| `--print-content` | 只打印提取的内容，跳过 LLM | `--print-content` |
| `--output` / `-o` | 输出到文件 | `-o doc.md` |
| `--json` | 以 JSON 输出 | `--json` |
| `--youtube` | YouTube 提取模式，需 `yt-dlp` | `--youtube auto` |
| `--firecrawl` | 当前实现中忽略 | — |

---

## 配置文件

可选用户级配置：`~/.summarize/config.json`

```json
{
  "model": "openai/gpt-5.2"
}
```

配置优先级：CLI flag > 配置文件 > 默认模型。

---

## 输入截断

为避免超出模型上下文窗口，输入文本超过 **60,000 字符** 时会自动截断并附加提示：

```
[Content truncated due to length]
```

如需处理超长文档，建议先用 [`pdf`](../pdf/SKILL.md) 或 [`mineru-pdf-parser`](../mineru-pdf-parser/SKILL.md) 拆分/提取关键章节。

---

## JSON 输出格式

```bash
python .claude/skills/summarize/summarize.py "URL" --print-content --json
```

输出示例：

```json
{
  "content": "提取到的正文...",
  "model": "google/gemini-3-flash-preview",
  "length": "medium",
  "input": "https://example.com"
}
```

在有 API key 时，key 名为 `"summary"` 而非 `"content"`。

---

## 与 Kimi 配合使用

推荐工作流：

1. 用 `--print-content` 提取长文内容并保存到文件：
   ```bash
   python .claude/skills/summarize/summarize.py "URL" --print-content --output article.md
   ```

2. 在对话中把 `article.md` 的内容贴给 Kimi，要求总结。

3. 如需结构化分析，可在提示中指定输出格式（表格、要点、章节摘要等）。
