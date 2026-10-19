# Learnings

Corrections, insights, and knowledge gaps captured during development.

**Categories**: correction | insight | knowledge_gap | best_practice

> 📑 汇总索引见 [INDEX.md](./INDEX.md)。架构决策见 [DECISIONS.md](./DECISIONS.md)，复发模式见 [PATTERNS.md](./PATTERNS.md)，Skill 注册表见 [SKILL_REGISTRY.md](./SKILL_REGISTRY.md)。

---

## [LRN-20260717-001] correction

**Logged**: 2026-07-17T14:45:00+08:00
**Priority**: high
**Status**: active
**Area**: workflow

### Summary

用户纠正工作方式： prefers 渐进式披露与事前确认。对于任何任务，若存在需要讨论的方案、风险或权衡，必须先与用户确认后再实施；除非用户已明确给出直接改动的指令。目标是实现“一次性成功”，避免事后缝补。

### Details

用户在讨论 OpenAI 提示词指南的启发后，明确反馈：

> “我觉得基本的东西我都能做到，我更喜欢渐进式披露。我要求你做任何任务，如果你有任何觉得需要讨论的方案，都需要和我先确认，然后再开始实施。除非我明确的改动，意思就是我们要多些讨论和相互质疑，我希望的是实施后的一次性成功，而不是缝缝补补。”

这意味着：

- **不要默认直接执行**有多个可行方案、涉及文件重命名/删除、跨目录大规模改动、或可能破坏现有结构的任务。
- **主动抛出选项和利弊**，让用户选择或拍板。
- **接受相互质疑**：用户希望我对方案提出疑问，而不是一味顺从。
- **一次做对优先于速度**：与其快速给出一个 80 分方案再迭代，不如先对齐再做 100 分方案。

### Suggested Action

- 接到任务后，先判断是否存在以下情况：
  - 多方案可选
  - 涉及删除、覆盖、重命名
  - 跨目录/跨文件批量改动
  - 与 CLAUDE.md 规范有模糊地带
  - 可能影响现有链接、索引或 git 历史
- 若存在，先用简短说明列出“我建议怎么做”以及“其他选项”，等待用户确认。
- 实施过程中若发现新的不确定点，立即暂停并反馈，不擅自决定。
- 已持久化到记忆：`memory/discuss-before-implement.md`

### Metadata

- Source: user_feedback
- Related Files: `CLAUDE.md`, `memory/discuss-before-implement.md`
- Tags: workflow, user_preference, progressive_disclosure, confirmation, quality
- Pattern-Key: workflow.discuss_before_implement
- Recurrence-Count: 1
- First-Seen: 2026-07-17
- Last-Seen: 2026-07-17

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



---

## [LRN-20260719-001] best_practice

**Logged**: 2026-07-19T21:22:14+08:00
**Priority**: medium
**Status**: active
**Area**: docs

### Summary

从 google/agents-cli（Google 官方 agent 开发 CLI + skills 套件，5.2k stars）移植四个 skill 工程模式到本知识库：阶段→技能编排层、skill 描述负向触发、反模式表、月度 retro 闭环。

### Details

分析 google/agents-cli 仓库后确认：其 CLI（ADK/GCP 部署）与本知识库无直接关系，不建议安装；但其 workflow/eval 两个 skill 的工程设计是同类规范（SKILL.md + references/）的成熟实现，有四处可借鉴：

1. **阶段→技能编排表 + 用前重读纪律**：context compaction 会丢弃已读 skill 内容，每阶段开始前须重读。→ 已落地为 `kb-workflow` skill（流水线 A 新资料入库 / B Inbox 清理 / C 笔记迭代 / D 持续改进）。
2. **描述中的负向触发**（"Do NOT use for X, use Y"）：消除边界模糊 skill 的误触发。→ 已更新 note-organizer / mcu-note-creator / obsidian-vault / summarize / mineru-pdf-parser。
3. **"Common Shortcuts to Resist" 反模式表**：列出 agent 常用借口及对策。→ 已落地为 CLAUDE.md §5.4。
4. **Quality Flywheel（Analyze→Propose→Confirm→Promote→Verify）**：记录≠改进，需定期把 .learnings/ 转化为实际修订。→ 已落地为 self-improving-agent「月度回顾」+ CLAUDE.md §5.3 第 3 条。

### Suggested Action

已实施完毕。后续在月度 retro 中复盘四个模式的实际效果；若 kb-workflow 流水线与实际工作方式有出入，优先更新该 skill 而非绕过它。

### Metadata

- Source: best_practice
- Related Files: `.claude/skills/kb-workflow/SKILL.md`, `.claude/CLAUDE.md`, `.claude/skills/self-improving-agent/SKILL.md`, `.learnings/SKILL_REGISTRY.md`
- See Also: LRN-20260717-001

---

## [LRN-20260726-001] correction

**Logged**: 2026-07-26T23:26:50+08:00
**Priority**: low
**Status**: active
**Area**: docs

### Summary

用户纠正：将外部内容内化到项目规范文档（如 CLAUDE.md）时，不要在正文或更新记录中标注来源出处（"自 XX 工作区引入"、"内化自 XX 手册"），内容应直接作为本项目自有规则呈现。

### Details

2026-07-26 将外部工作区的协作手册与第一性原理整合进 CLAUDE.md §5.0 时，在小节引言和 §9 更新记录中注明了内容来源。用户反馈：

> "其实你没有必要说这个从哪来的"

已移除 §5.0 引言中的出处说明，§9 更新记录改为只描述变更内容本身。

### Suggested Action

- 内化/吸收外部内容到项目规范文档时，正文不写来源标注，文档应读起来像项目自有规则
- §9 更新记录只写"加了什么"，不写"从哪来的"
- 若来源信息确有追溯价值，记入 `.learnings/` 而非规范文档正文

### Metadata

- Source: user_feedback
- Related Files: `.claude/CLAUDE.md`
- Tags: docs, style, provenance, user_preference
- Pattern-Key: docs.no_provenance_annotation
- Recurrence-Count: 1
- First-Seen: 2026-07-26
- Last-Seen: 2026-07-26

## [LRN-20260806-001] knowledge_gap/attachment-move-link-integrity

**Logged**: 2026-08-06
**Priority**: medium
**Status**: active
**Area**: docs

### Summary

对 `99_Attachments_附件` 做分类移动时发现：`01_Agent_Building_构建好的Agent` 下 10 处指向附件的相对链接深度本就错误（少一级 `../`，移动前即已失效），本次移动附件时一并修正并引入链接解析校验。

### Details

- 深度 3 的笔记（如 `01_Design_Principles_设计原则/xxx.md`）中原链接为 `../99_Attachments_附件/...`，正确应为 `../../../99_Attachments_附件/...`
- 附件目录按主题分为 `AI_Agent/`、`Memory_存储器/`、`IC_Design_芯片设计/` 三类，移动后批量更新了 13 处引用

### Suggested Action

- 移动/重命名 `99_Attachments_附件` 内任何文件前，先 `grep -rn "99_Attachments_附件/<文件名>" --include="*.md"` 找全引用
- 移动后用脚本逐条校验相对链接能否解析到真实文件（os.path.normpath + exists），不要只改不验
- 写新附件链接时注意相对深度：笔记在 `91_Tools_AI工具链/XX/笔记.md`（深度2）用 `../../`，在其子目录（深度3）用 `../../../`

### Metadata

- Source: discovery
- Related Files: `99_Attachments_附件/`, `91_Tools_AI工具链/01_Agent_Building_构建好的Agent/`
- Tags: docs, links, attachments, verification
- Pattern-Key: docs.verify_links_after_attachment_move
- Recurrence-Count: 1
- First-Seen: 2026-08-06
- Last-Seen: 2026-08-06

## [LRN-20260809-001] best_practice/python-reinstall-314

**Logged**: 2026-08-09
**Priority**: high
**Status**: active
**Area**: infra

### Summary

用户误删了系统 Python（Python313 目录被清空），导致所有 PDF/MinerU/summarize 脚本失效。已重装 Python 3.14.7（华为云镜像下载官方安装包），全部文档处理库在新环境装齐。

### Details

- 新 Python 路径：`C:\Users\11064\AppData\Local\Programs\Python\Python314\python.exe`（旧的 Python313 路径已废弃）
- 已装库：pypdf、pdfplumber、reportlab、pandas、openpyxl、pytesseract、pdf2image、requests、beautifulsoup4、mineru-open-sdk（import 名为 `mineru`）、PyMuPDF
- 国内加速：安装包用 `mirrors.huaweicloud.com/python/`，pip 用 `pypi.tuna.tsinghua.edu.cn/simple`；GitHub 直连（uv python install）会卡死
- Git Bash 调 cmd.exe 注意两个坑：`/c` 会被路径转换吃掉（需 `MSYS2_ARG_CONV_EXCL="*"`）；cmd 内执行文件要用 Windows 全路径
- MinerU Token 已通过 setx 持久化到用户环境变量 `MINERU_API_TOKEN`

### Suggested Action

- 后续会话中 Python 调用优先直接用 `python`（PATH 已注册，新终端生效）；若 shell 是旧会话则用 Python314 全路径
- ERR-20260805-001 中的 Python313 全路径 workaround 作废，以本条为准

### Metadata

- Source: user_action + fix
- Related Files: `.claude/skills/mineru-pdf-parser/`, `.claude/skills/summarize/`
- Tags: infra, python, environment, mirror
- Pattern-Key: infra.python314_reinstall
- Recurrence-Count: 1
- First-Seen: 2026-08-09
- Last-Seen: 2026-08-09

## [LRN-20260815-001] correction/output_format

**Logged**: 2026-08-15T00:00:00+08:00
**Priority**: high
**Status**: active
**Area**: workflow

### Summary

用户反馈：VSCode 扩展对话界面不渲染 LaTeX 公式（`$$...$$`）和 Mermaid 图，显示为原始源码。对话内输出必须改用纯文本公式与 ASCII 字符画。

### Details

在 SoC 精读会话中，导读里用了 `$$...$$` LaTeX 公式和 ```mermaid 代码块，用户看不到渲染效果，指出"我看这个公式都没渲染"。

分界规则：

- **对话内输出**（聊天消息）：公式用纯文本（如 `CPU 时间 = IC × CPI × Tclk`），图用 ASCII 字符画、表格、代码块——这些能正常渲染
- **落盘的笔记文件**（.md）：继续用 Mermaid + LaTeX——Obsidian 端能正常渲染，不牺牲笔记质量

### Suggested Action

- 今后对话中一律不用 `$$...$$`、`$...$`、```mermaid 代码块
- 需要画图时用 ASCII 字符画（├─ └─ │ → 等字符）或 Markdown 表格
- 笔记文件不受此限制

### Metadata

- Source: user_feedback
- Related Files: `.claude/CLAUDE.md`
- Tags: output_format, rendering, vscode
- Pattern-Key: workflow.chat_rendering_limits
- Recurrence-Count: 1
- First-Seen: 2026-08-15
- Last-Seen: 2026-08-15

## [LRN-20260830-001] best_practice/ads_build_settings_materialized_in_debug_dir

**Logged**: 2026-08-30
**Priority**: medium
**Status**: open
**Area**: tools

### Summary

ADS（Eclipse + com.infineon.aurix.buildsystem）会把工程内**所有文件夹自动加入 include 路径**，且排除编译（Exclude from Build）的目录会同时从 include 路径自动生成中消失。GUI 设置的真实生效结果物化在 `Debug/TASKING_C_C___Compiler-Include_paths.opt` 与各 `subdir.mk` 中——远程排障时直接读这些文件即可验证用户实际配置，无需猜测 GUI 状态。

### Details

- 实例：TC397 FreeRTOS 工程编译失败 E219，根因是 ADS 自动加入的 `portable/GCC/TC3` 排在 `portable/Tasking/TC3` 之前，`portmacro.h` 被 GCC 版抢先命中（其内 `#include <machine/intrinsics.h>` 为 GNU/newlib 头，TASKING 无此文件）
- 官方 TC375 例程的 .cproject 即以"排除 portable/GCC 目录"方式解决同一问题（其 exclusion 列表含 portable/GCC、heap_2~5）
- FreeRTOS 的 port 选择机制 = 编译期目录选择（哪个 port 目录进 include/编译列表就用哪个），非 #ifdef
- 验证命令：`cat Debug/*Include_paths.opt`；查参与编译的源文件看 `Debug/**/subdir.mk`；查排除是否生效看 `.cproject` 的 `excluding="..."` 列表
- 陷阱：Exclude from Build 必须作用于**源路径**（`OS/...`）；Project Explorer 中 `Debug/` 下的同名目录是构建产物镜像，错排它不生效（已踩：ERR 记录见会话 2026-08-30）
- 直接改 .cproject 时须先关闭 ADS——Eclipse 持有内存副本，GUI 任何设置变更会把旧配置写回覆盖手工修改

### Suggested Action

- SX（HighTec 移植）阶段复用：GCC 工程则反过来排除 portable/Tasking
- 指导 ADS GUI 操作时，给"排除清单"优先于"添加路径"（自动扫描使手动加路径常非必需）

### Metadata

- Related Files: TC397_Platform_Jason/ADS/FreeRTOS（库外工程）
- See Also: FreeRTOS_00_总体学习与实践方案.md S0/SP 阶段
- Pattern-Key: tools.ads_include_autogen

## [LRN-20260831-001] correction/stage_lesson_must_persist_immediately

**Logged**: 2026-08-31
**Priority**: high
**Status**: open
**Area**: workflow

### Summary

学习路线课程在对话里讲完但未落盘笔记，用户指正"这个没有讲吧"。按 purpose-driven-book-study 步骤 6（阶段收尾落盘）与本库规范，**没落盘 = 没完成**。讲授与落盘必须同阶段完成，不能留"只在对话里"的课程。

### Details

- 实例：SP Port 深潜第 1 课（CSA/上下文切换）2026-08-30 对话讲授完毕，未创建阶段笔记；次日用户质疑后补写 `05_Port/01_PortLayer/FreeRTOS_Port_TC3xx_Context_Switch_CSA.md`
- 对话内容随上下文压缩/会话结束丢失，用户无法回看——讲授价值归零
- 根因：任务收尾时优先做了 commit/路线更新，漏了课程笔记这个主产出

### Suggested Action

- 每次讲授类输出（课/阶段）结束前，自问"这课的笔记文件是哪个"，没有就当场写
- 路线文档的进度日志只在对应笔记落盘后才允许记"已讲/完成"

### Metadata

- Related Files: `.claude/skills/purpose-driven-book-study/reference.md`（步骤 6）
- Pattern-Key: workflow.lesson_persistence

## [LRN-20260911-001] best_practice/big_pdf_split_pipeline_scriptified

**Logged**: 2026-09-11
**Priority**: medium
**Status**: active
**Area**: tools

### Summary

把 ERR-20260809-001 的手工「切块 → 逐块解析 → 合并」流程脚本化为 `doc_to_md_split.py`（入 mineru-pdf-parser 技能 scripts/）。首次全量实战：7 本大书、3393 页、20 个切块全部成功，总耗时约 15 分钟。

### Details

- **关键设计**：每个切块用独立 `submit()` 获得独立 batch_id，结果与块一一对应（不依赖服务端返回顺序），同时各块在服务端并行解析——实测 195 页块约 60–175s，5–6 块并行提交后约 3 分钟全部完成
- **断点续跑**：已存在且非空的 `full_partNN.md` 自动跳过；`_parts/` 切块文件复用（首轮 Token 失效中断后，二轮直接复用未重切）
- **原子性**：全部块成功才合并 `full.md`；失败保留中间产物、非零退出，可重跑续传
- **图片**：token 模式 `save_markdown(with_images=True)` 落盘哈希命名图片，多块共用同一 `images/` 无冲突（实测单本最多 930 张）
- **质量抽检法**：真图注（行首 `Figure N-M` 且非正文引用）与「图片引用/表格承载」配对率——TRM 样本 32 图注 = 18 图 + 14 表格 + 0 丢失；另查 `(cid:\d+)` 残留评估 OCR 质量（Yiu 书：0 残留）
- **容错**：401 立即中止不重试（重试无意义）；Windows 注册表回退读取 token（`setx` 后免重启终端/VSCode）
- 本次转换产物统计：full.md 共 ~94k 行、2917 张图（含原 PDF 共 297MB，其中 Yiu 原书 105.8MB 超 GitHub 100MiB 上限已 gitignore，仅本地保留）

### Suggested Action

- 以后所有 >200 页文档直接 `doc_to_md_split.py`，不再手工切块
- 转换完成后的默认抽检：真图注配对率 + cid 残留，两者任一异常再人工细查

### Metadata

- Source: best_practice
- Related Files: `.claude/skills/mineru-pdf-parser/scripts/doc_to_md_split.py`, `.claude/skills/mineru-pdf-parser/gotchas.md`
- See Also: ERR-20260809-001, ERR-20260911-001, ERR-20260911-002
- Pattern-Key: tools.mineru_split_pipeline
- Recurrence-Count: 1
- First-Seen: 2026-09-11

## [LRN-20261014-001] best_practice/dual-guide-sync-hook

**Logged**: 2026-10-14
**Priority**: medium
**Status**: active
**Area**: workflow

### Summary

AGENTS.md 与 .claude/CLAUDE.md 统一为逐字节一致的同一内容（泛化工具名引用），用 `scripts/sync-guides.ps1` + git pre-commit hook 双向同步（较新 mtime 者覆盖较旧者，hook 自动 git add 两份）。消除了 2026-08 以来两份指南独立演化分叉 229 行的问题。

### Details

- 统一关键：两份文件内容必须 100% 相同（措辞泛化，不写工具专属表述），同步才能退化为纯拷贝、双向无损
- hook 源文件同时保存于 `scripts/pre-commit`（`.git/hooks/` 不随仓库分发，克隆后需 `cp scripts/pre-commit .git/hooks/pre-commit` 重装）
- 附带坑：Windows PowerShell 5.1 把无 BOM 的 UTF-8 .ps1 按 ANSI(GBK) 解析，中文注释/字符串直接 ParseError；本机无 pwsh（PS7），hook 实际走 powershell.exe（5.1）

### Suggested Action

- 今后修改任一份指南即可；git 提交时 hook 自动同步另一份。不走 git 的修改手动跑 `scripts/sync-guides.ps1`（`-Check` 仅校验、`-From agents|claude` 强制方向）
- 仓库内 .ps1 脚本保持纯 ASCII；必须含中文时保存为带 BOM 的 UTF-8

### Metadata

- Source: best_practice
- Related Files: `AGENTS.md`, `.claude/CLAUDE.md`, `scripts/sync-guides.ps1`, `scripts/pre-commit`
- Pattern-Key: workflow.dual_guide_sync
- Recurrence-Count: 1
- First-Seen: 2026-10-14
