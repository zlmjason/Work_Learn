# Learnings

Corrections, insights, and knowledge gaps captured during development.

**Categories**: correction | insight | knowledge_gap | best_practice

> 📑 汇总索引见 [INDEX.md](./INDEX.md)。架构决策见 [DECISIONS.md](./DECISIONS.md)，复发模式见 [PATTERNS.md](./PATTERNS.md)，Skill 注册表见 [SKILL_REGISTRY.md](./SKILL_REGISTRY.md)。

---

## [LRN-20260711-002] correction

**Logged**: 2026-07-11T10:15:00+08:00
**Priority**: high
**Status**: active
**Area**: workflow

### Summary
用户纠正：对于本仓库，"上传" / "推送" 默认直接推送到 `master` 分支，不需要创建功能分支或额外确认。

### Details
在调用 `git-upload-push` skill 时，脚本警告当前在默认分支 `master` 并建议创建功能分支。用户明确反馈：

> "记住规则 除非我特别说明 上传都是master分支"

这属于项目级约定：个人知识库项目，直接在 master 上迭代更轻量。

### Suggested Action
- 用户触发上传/推送意图时，直接执行 `git add -A && git commit -m "..." && git push origin master`
- 不再主动建议创建功能分支
- 若默认分支不是 master，需先确认用户意图
- 已持久化到记忆：`memory/default-push-master.md`

### Metadata
- Source: user_feedback
- Related Files: `.claude/skills/git-upload-push/scripts/git-upload-push.py`, `memory/default-push-master.md`
- Tags: git, push, master, workflow, user_preference
- Pattern-Key: workflow.push_to_master
- Recurrence-Count: 1
- First-Seen: 2026-07-11
- Last-Seen: 2026-07-11

---

## [LRN-20260711-001] best_practice

**Logged**: 2026-07-11T10:00:00+08:00
**Priority**: medium
**Status**: active
**Area**: tools

### Summary
在国内网络环境下，Python 包安装需根据包的镜像可用性灵活选择 PyPI 源：`markitdown[all]` 用清华镜像下载快且稳定，而 `mineru-open-sdk` 在清华镜像上无分发，需回退到官方 PyPI。

### Details
安装 MarkItDown 全量版时，首次使用默认 PyPI 源下载 `speechrecognition`（32.9 MB）超时失败。切换到清华镜像源后，所有依赖（包括 `magika`、`onnxruntime`、`azure-*` 等）均快速下载完成。

但安装 MinerU SDK 时，清华镜像源报 `No matching distribution found for mineru-open-sdk`。改用默认 PyPI 源后立即成功（`mineru_open_sdk-0.2.5`）。

### Suggested Action
- 大包/依赖多且镜像上有分发 → 用清华镜像：`-i https://pypi.tuna.tsinghua.edu.cn/simple`
- 镜像找不到包 → 去掉 `-i` 回退官方 PyPI
- 批量安装前可先单独查询包的可用性，避免中途切换

### Metadata
- Source: best_practice
- Related Files: `.claude/skills/mineru-pdf-parser/`, `.claude/skills/pdf/`
- Tags: pip, mirror, markitdown, mineru, network, pypi
- Pattern-Key: tools.pip_mirror_fallback
- Recurrence-Count: 1
- First-Seen: 2026-07-11
- Last-Seen: 2026-07-11

---

## [LRN-20260511-005] best_practice

**Logged**: 2026-05-11T10:20:00+08:00
**Priority**: high
**Status**: resolved
**Area**: infra

### Summary
用户无第三方 LLM API Key，仅通过 Kimi2.6 访问 AI 能力。需调整 summarize 工作流，将"内容提取"与"LLM 摘要"解耦。

### Details
原版 summarize CLI 是端到端工具：输入 → 提取 → LLM API → 摘要输出。但用户只有 Kimi2.6，无 Gemini/OpenAI 等 API Key。

解决方案：将 summarize.py 拆分为两阶段：
1. **内容提取阶段**（summarize.py 负责）：
   - URL 抓取 → HTML → 纯文本
   - PDF 提取 → 纯文本
   - YouTube 提取 → 标题/描述/字幕
   - 输出：清洗后的纯文本

2. **LLM 摘要阶段**（Kimi2.6 负责）：
   - 用户将提取的文本发给 Kimi
   - Kimi 直接生成摘要

实现改动：
- 新增 `--print-content` 参数：只提取内容，不调用 LLM
- 新增 `--output FILE` 参数：将内容保存到文件
- 无 API Key 时自动降级到 `--print-content` 模式，并提示用户
- 保留完整 LLM 后端支持，未来用户获取 API Key 后可无缝切换

### Suggested Action
- 无 API Key 时：`summarize "url"` 自动提取内容 → 复制文本 → 在对话中发送给 Kimi 摘要
- 有 API Key 后：同一脚本直接调用 LLM，无需更换工具
- 对于长文档，建议 `--output doc.md` 保存后，在对话中引用文件路径

### Resolution
- **Resolved**: 2026-05-11T10:25:00+08:00
- **Files**: `skills/summarize/summarize.py` (updated with --print-content, --output, auto-fallback)

### Metadata
- Source: user_feedback | best_practice
- Related Files: skills/summarize/summarize.py
- Tags: summarize, kimi, llm, api_key, content_extraction, decoupling
- Pattern-Key: workflow.llm_fallback
- Recurrence-Count: 1
- First-Seen: 2026-05-11
- Last-Seen: 2026-05-11

---


**Logged**: 2026-05-11T10:08:30+08:00
**Priority**: high
**Status**: resolved
**Area**: infra

### Summary
已实现 Windows 原生 `summarize.py` 替代脚本，完全替代 Homebrew 分发的 `summarize` 二进制。

### Details
原版 `summarize` 是 Go/Rust CLI，仅通过 Homebrew 分发，Windows 无原生支持。替代方案：

1. **summarize.py** (`skills/summarize/summarize.py`):
   - 支持 URL 抓取（requests + BeautifulSoup 文本提取）
   - 支持本地文件（文本、PDF 通过 PyPDF2）
   - 支持 YouTube（yt-dlp 提取标题/描述/字幕）
   - 支持多 LLM 后端：Google Gemini、OpenAI、Anthropic、xAI
   - 兼容原版参数：`--model`, `--length`, `--max-output-tokens`, `--extract-only`, `--json`, `--firecrawl`, `--youtube`
   - 自动读取 `~/.summarize/config.json`
   - 自动解析环境变量 API Key（GEMINI_API_KEY, OPENAI_API_KEY 等）
   - 输入超长时自动截断至 60K 字符

2. **Windows wrapper** (`%USERPROFILE%\.local\bin\summarize.cmd`):
   - 调用 `python skills/summarize/summarize.py`
   - 与原版命令行接口一致

3. **依赖安装**：
   - `pip install requests beautifulsoup4`（必需）
   - `pip install PyPDF2`（PDF 支持，可选）
   - `pip install yt-dlp`（YouTube 支持，可选）

### Suggested Action
- 在 Windows 环境下优先使用 `summarize.py` 替代 Homebrew 版本
- 如需 PDF/YouTube 支持，补装对应可选依赖
- 后续若 yt-dlp 不可用，可接入 YouTube Transcript API 作为降级方案

### Resolution
- **Resolved**: 2026-05-11T10:15:00+08:00
- **Files**: `skills/summarize/summarize.py`, `skills/summarize/summarize.cmd`, `%USERPROFILE%\.local\bin\summarize.cmd`

### Metadata
- Source: user_feedback | best_practice
- Related Files: skills/summarize/SKILL.md, skills/summarize/summarize.py
- Tags: windows, summarize, python, llm, alternative, homebrew
- Pattern-Key: install.python_alternative
- Recurrence-Count: 1
- First-Seen: 2026-05-11
- Last-Seen: 2026-05-11

---


**Logged**: 2026-05-11T09:26:17+08:00
**Priority**: medium
**Status**: pending
**Area**: config

### Summary
Skillhub bash install script requires manual adaptation on Windows (PowerShell) environments.

### Details
The official Skillhub install script (`install.sh`) is a bash script that assumes a Unix-like environment with `bash`, `tar`, `curl`, and standard `$HOME` paths. On Windows PowerShell:
- `curl -fsSL` fails because PowerShell's `Invoke-WebRequest` does not support `-fsSL` flags
- `bash` may not be in PATH
- File paths use backslashes and `$env:USERPROFILE` instead of `$HOME`

The correct Windows adaptation is:
1. Download the outer script via `Invoke-WebRequest`
2. Parse the inner `KIT_URL` and download `latest.tar.gz`
3. Extract with `tar -xzf` (Windows 10+ built-in tar)
4. Copy CLI Python files to `$env:USERPROFILE\.skillhub\`
5. Create `.cmd` wrapper scripts in `$env:USERPROFILE\.local\bin\`
6. Create `config.json` with `self_update_url` and `install_workspace_skills`
7. Copy workspace skills to `$env:USERPROFILE\.openclaw\workspace\skills\`

### Suggested Action
- Document Windows install path or provide a PowerShell install script upstream
- Add `$env:USERPROFILE\.local\bin` to PATH for global `skillhub` command access

### Metadata
- Source: error | user_feedback
- Related Files: skills_store_cli.py, install.sh
- Tags: windows, skillhub, powershell, cli
- Pattern-Key: install.cross_platform
- Recurrence-Count: 1
- First-Seen: 2026-05-11
- Last-Seen: 2026-05-11

---

## [LRN-20260511-002] knowledge_gap

**Logged**: 2026-05-11T09:26:17+08:00
**Priority**: medium
**Status**: pending
**Area**: infra

### Summary
Summarize CLI (`summarize.sh`) is distributed via Homebrew only; no native Windows/pip distribution exists.

### Details
The `summarize` skill depends on the `summarize` binary from `steipete/tap/summarize`. On Windows:
- `brew` is not natively available
- No PyPI package `summarize-cli` exists
- The tool requires API keys (OPENAI_API_KEY, GEMINI_API_KEY, etc.) for LLM-based summarization

Workarounds:
1. Use WSL2 + Homebrew to run `summarize`
2. Use Python alternatives like `newspaper3k` + direct LLM API calls
3. Request upstream Windows release or pip distribution

### Suggested Action
- On Windows, skip `summarize` CLI and use direct API calls or alternative extractors
- If WSL2 is available, install via `brew install steipete/tap/summarize`

### Metadata
- Source: error
- Related Files: skills/summarize/SKILL.md
- Tags: windows, summarize, brew, cli, missing_dependency
- Pattern-Key: install.missing_binary
- Recurrence-Count: 1
- First-Seen: 2026-05-11
- Last-Seen: 2026-05-11

---

## [LRN-20260511-003] insight

**Logged**: 2026-05-11T09:30:37+08:00
**Priority**: high
**Status**: resolved
**Area**: infra

### Summary
用户决定不安装 WSL2，需评估所有 skill 在 Windows 原生环境下的可用性及替代方案。

### Details
| Skill | 依赖 WSL2？ | Windows 原生状态 | 替代方案 |
|-------|-----------|-----------------|---------|
| self-improving-agent | ❌ 不需要 | ✅ 完全可用 | `.learnings/` 已初始化 |
| find-skills | ❌ 不需要 | ✅ 可用 | skillhub CLI (Python) 已可用 |
| summarize | ⚠️ 二进制依赖 | ⚠️ 需适配 | Python + LLM API 替代实现 |

### Suggested Action
- self-improving-agent：正常使用，hook 脚本（bash）可选
- find-skills：使用 skillhub search/install 替代 npx skills
- summarize：编写 Python 替代脚本，封装 LLM 调用

### Resolution
- **Resolved**: 2026-05-11T09:54:51+08:00
- **Decision**: 不安装 WSL2，所有 skill 改为 Windows 原生适配

### Metadata
- Source: user_feedback
- Related Files: skills/summarize/SKILL.md
- Tags: windows, skill, summarize, wsl2, alternative
- Pattern-Key: install.wsl2_homebrew
- Recurrence-Count: 1
- First-Seen: 2026-05-11
- Last-Seen: 2026-05-11

---


