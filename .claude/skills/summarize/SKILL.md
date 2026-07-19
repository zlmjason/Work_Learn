---
name: summarize
description: Extract and summarize content from URLs, local files, PDFs, and YouTube videos. Trigger when the user asks to summarize a webpage, article, PDF, video, or any document; or mentions 'TL;DR', 'summary', 'extract content'. This project has no third-party LLM API key, so default to --print-content mode and let Kimi summarize. Do NOT use for high-fidelity conversion of PDF/Word/PPT/Excel where tables, formulas, and layout must be preserved (use mineru-pdf-parser).
metadata:
---

# Summarize

Windows-native CLI 替代工具，用于提取 URL、本地文件、PDF、YouTube 视频的内容。本项目**默认无第三方 LLM API 密钥**，所以通常使用 `--print-content` 模式：只提取内容，然后交给 Kimi 总结。

## 触发条件

用户提到以下任一表达时调用本 skill：

- "总结一下这篇文章"
- "提取这个 PDF 的内容"
- "这个视频讲了什么"
- "TL;DR"
- "summary"
- "extract content"
- "把网页内容抓下来"

## 快速参考

| 情况 | 操作 |
|------|------|
| 无 API key（默认） | `python .claude/skills/summarize/summarize.py "URL" --print-content` |
| 保存到文件 | 加上 `--output doc.md` |
| 本地 PDF | `python .claude/skills/summarize/summarize.py "file.pdf" --print-content` |
| YouTube | `python .claude/skills/summarize/summarize.py "URL" --youtube auto --print-content` |
| 有 API key | 设置对应环境变量后直接运行 |

## 一分钟示例

```bash
# 提取网页内容并保存
python .claude/skills/summarize/summarize.py "https://example.com" --print-content --output article.md

# 提取 PDF 内容
python .claude/skills/summarize/summarize.py "report.pdf" --print-content
```

## 文件结构

```
summarize/
├── SKILL.md          ← 本文件（入口与触发条件）
├── reference.md      ← 详细用法、flag 说明、环境变量、JSON 输出
├── gotchas.md        ← 常见陷阱（无 key 回退、60K 截断、依赖等）
├── config.json       ← 默认模型、环境变量映射、依赖说明
├── summarize.py      ← Windows-native Python 脚本
└── summarize.cmd     ← Windows 包装器
```

## 常见陷阱

- 无 API key 时自动回退到 `--print-content`
- `--print-content` 输出不会自动进入 Kimi 上下文，需要手动复制
- 输入超过 60,000 字符会自动截断
- `--firecrawl` 在当前实现中被忽略
- YouTube/PDF 分别依赖可选的 `yt-dlp` 和 `PyPDF2`

详见 [`gotchas.md`](./gotchas.md)。

## 详细用法

环境变量、全部 flag、JSON 输出、与 Kimi 配合工作流见 [`reference.md`](./reference.md)。
