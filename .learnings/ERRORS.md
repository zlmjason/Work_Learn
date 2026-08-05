# Errors

Command failures and integration errors.

> 📑 汇总索引见 [INDEX.md](./INDEX.md)。架构决策见 [DECISIONS.md](./DECISIONS.md)，复发模式见 [PATTERNS.md](./PATTERNS.md)，Skill 注册表见 [SKILL_REGISTRY.md](./SKILL_REGISTRY.md)。

---

## [ERR-20260805-001] git_bash_minimal_path_python_grep_missing

**Logged**: 2026-08-05T16:00:00+08:00
**Priority**: low
**Status**: resolved
**Area**: infra

### Summary
Claude Code Bash 工具的 Git Bash 环境 PATH 不完整：`python` 及基础 Unix 工具（`grep`、`tail`）均 command not found（exit 127），但脚本内部调用的 `git` 可用。

### Error
```
/usr/bin/bash: line 1: python: command not found
/usr/bin/bash: line 1: grep: command not found
/usr/bin/bash: line 1: tail: command not found
```

### Context
- Command: `python .claude/skills/git-upload-push/scripts/git-upload-push.py status`；`grep -n ... | tail -5`
- Environment: Windows 11, Claude Code VSCode 扩展内嵌 Bash 工具
- Expected: python 在 PATH 中（CLAUDE.md §7 声明 Python 已安装）
- Actual: exit 127。Python 实际位于 `C:\Users\11064\AppData\Local\Programs\Python\Python313\python.exe`，未加入该 shell 的 PATH

### Suggested Fix
1. **Python 调用一律用全路径**：`/c/Users/11064/AppData/Local/Programs/Python/Python313/python <script>`（已验证可用）
2. **文本搜索/读取用 Claude Code 内置工具**（Grep / Read / Glob），不要在 Bash 里调 grep/tail/sed
3. 长期方案：将 Python313 目录加入用户 PATH 环境变量（需重启终端生效）

### Metadata
- 复发关联：与 [ERR-20260709-006]（PDF 库缺失，同一 Python 环境）同源，均为本地 Python 环境未规范化
- 首次触发场景：git-upload-push skill 执行

---

## [ERR-20260804-001] git_push_github_connection_timeout

**Logged**: 2026-08-04T12:00:00+08:00
**Priority**: medium
**Status**: open
**Area**: infra

### Summary
`git push` 到 GitHub 时连接超时/被重置，无法完成远程推送。

### Error
```
fatal: unable to access 'https://github.com/zlmjason/Work_Learn.git/':
Failed to connect to github.com port 443 after 21060 ms: Timed out

fatal: unable to access 'https://github.com/zlmjason/Work_Learn.git/':
OpenSSL SSL_read: Connection was reset, errno 10054

# 另一次重试时 Git Bash 自身崩溃
0 [main] bash (29040) ...: *** fatal error - add_item ("\??\C:\Program Files\Git", "/", ...) failed, errno 1
```

### Context
- Command: `git push`
- Environment: Windows 10 Pro, Git Bash, 无代理
- Expected: 本地 commit 推送到 origin/master
- Actual: 
  - 连接建立失败，21 秒后超时
  - 重试时被服务器重置（errno 10054）
  - 某次重试时 Git Bash 进程自身崩溃，未到达网络层

### Suggested Fix
1. 等待网络恢复后重试 `git push`
2. 检查本地网络或 DNS 是否能解析 github.com
3. 尝试重启 Git Bash / VS Code 窗口，排除 shell 状态异常
4. 如有可用代理，配置 Git 代理：
   ```bash
   git config --global http.proxy http://proxy:port
   git config --global https.proxy http://proxy:port
   ```

### Metadata
- Reproducible: yes (under current network conditions)
- Related Files: `.claude/skills/git-upload-push/scripts/git-upload-push.py`
- See Also: ERR-20260630-004

---

## [ERR-20260804-002] git_upload_push_chinese_commit_message_garbled

**Logged**: 2026-08-04T12:00:00+08:00
**Priority**: medium
**Status**: open
**Area**: tools

### Summary
`git-upload-push` skill 脚本在 Windows 下处理中文 commit message 时仍出现乱码，疑似 ERR-20260711-001 的修复未完全覆盖当前场景。

### Error
```
[master 41733b8] docs: �鵵 Loop Engineering IEEE ����������Ŀ¼
```
commit message 中的中文字符被替换为乱码方块。

### Context
- Command: `python .claude/skills/git-upload-push/scripts/git-upload-push.py push "docs: 归档 Loop Engineering IEEE 论文至附件目录" --yes`
- Environment: Windows 10 Pro, Git Bash, Python 3.13
- Expected: commit message 正确显示中文
- Actual: 中文字符编码损坏，显示为乱码

### Suggested Fix
1. 临时方案：commit message 使用纯 ASCII/英文，避免中文编码问题
2. 修复脚本：检查 `subprocess.run` 的 `encoding` 参数是否同时覆盖 `stdin` 写入路径；必要时对 commit message 先 encode 为 UTF-8 再传入
3. 在 Windows 上设置环境变量 `PYTHONIOENCODING=utf-8` 后再调用脚本
4. 验证：用中文 commit message 重跑脚本，确认 `git log` 输出正确

### Metadata
- Reproducible: yes
- Related Files: `.claude/skills/git-upload-push/scripts/git-upload-push.py`
- See Also: ERR-20260711-001

---

## [ERR-20260711-001] git_upload_push_windows_encoding

**Logged**: 2026-07-11T10:10:00+08:00
**Priority**: medium
**Status**: resolved
**Area**: tools

### Summary
`git-upload-push` skill 脚本在 Windows 中文路径仓库中执行 `git commit` 时因编码问题崩溃，无法完成自动推送。

### Error
```
UnicodeDecodeError: 'gbk' codec can't decode byte 0xac in position 47: illegal multibyte sequence
...
File "...git-upload-push.py", line 33, in run
    return result.stdout.strip()
           ^^^^^^^^^^^^^^^^^^^
AttributeError: 'NoneType' object has no attribute 'strip'
```

### Context
- Command: `python .claude/skills/git-upload-push/scripts/git-upload-push.py push "..." --yes`
- Environment: Windows 11, Git Bash, Python 3.13, 仓库路径含中文目录名
- Expected: 自动完成 `git add -A` → `git commit` → `git push`
- Actual: 脚本在读取 `git commit` 输出时因 GBK 解码失败而崩溃，commit 可能已执行但 push 未完成

### Suggested Fix
1. 临时方案：手动执行 `git add -A && git commit -m "..." && git push origin master`
2. 修复脚本：在 `subprocess.run` 中显式指定 `encoding='utf-8'` 和 `errors='replace'`，避免依赖系统默认编码
3. 同时处理 `master` 默认分支警告：即使 `--yes` 也应允许在默认分支推送，或增加 `--allow-master` 参数

### Metadata
- Reproducible: yes
- Related Files: `.claude/skills/git-upload-push/scripts/git-upload-push.py`
- See Also: LRN-20260711-001

### Resolution
- **Resolved**: 2026-07-19
- **Commit**: fa7fc06
- **Notes**: 按 Suggested Fix 第 2 条修复——`subprocess.run` 显式指定 `encoding="utf-8", errors="replace"`；已用中文 commit message 实测推送成功，GBK 崩溃不再出现。第 3 条（master 警告）确认现有逻辑已满足：`--yes` 时仅警告不阻断，符合用户直推 master 的偏好。

---

## [ERR-20260511-001] pip_install_summarize

**Logged**: 2026-05-11T09:26:17+08:00
**Priority**: medium
**Status**: resolved
**Area**: infra

### Summary
`pip install summarize-cli` failed with "No matching distribution found".

### Error
```
ERROR: Could not find a version that satisfies the requirement summarize-cli
ERROR: No matching distribution found for summarize-cli
```

### Context
- Command: `pip install summarize-cli`
- Environment: Windows PowerShell, Python 3.12.3
- Expected: Install the summarize CLI tool referenced in skills/summarize/SKILL.md
- Actual: PyPI has no package named `summarize-cli`

### Suggested Fix
The correct `summarize` binary is a Go/Rust CLI distributed via Homebrew (`steipete/tap/summarize`), not PyPI. On Windows, either:
1. Install via WSL2 + brew
2. Use direct LLM API calls for URL/file summarization
3. Build from source if repository is available

### Metadata
- Reproducible: yes
- Related Files: skills/summarize/SKILL.md
- See Also: LRN-20260511-002

---

## [ERR-20260511-003] winget_install_tesseract_poppler

**Logged**: 2026-05-11T14:52:00+08:00
**Priority**: medium
**Status**: wont_fix

### Resolution
- **Resolved**: 2026-05-11T14:55:00+08:00
- **Reason**: User decided these features (OCR scanned PDFs, PDF-to-image) are not currently needed. Can be installed manually later if required.
- **Notes**: Basic PDF operations (text/table extraction, merge/split, creation) are fully functional without these dependencies.
**Area**: infra

### Summary
winget installation of Tesseract-OCR and Poppler failed due to network/download issues on Windows.

### Error
```
# Tesseract: timed out after 600s, download stalled at ~7MB / 20.3MB
# Poppler: InternetReadFile() failed. 0x80072ee2 : unknown error
```

### Context
- Commands:
  - `winget install tesseract-ocr.tesseract --silent`
  - `winget install oschwartz10612.Poppler --silent`
- Environment: Windows 11, winget v1.x
- Expected: Install system-level dependencies required by pytesseract and pdf2image Python libraries
- Actual: Downloads failed repeatedly; Tesseract stalled, Poppler returned network error

### Suggested Fix
Install manually when network is stable:
1. **Tesseract-OCR**: Download from https://github.com/tesseract-ocr/tesseract/releases (tesseract-ocr-w64-setup-*.exe)
2. **Poppler**: Download from https://github.com/oschwartz10612/poppler-windows/releases
3. Alternative: Use Scoop or Chocolatey if available (`choco install tesseract poppler`)
4. Note: These are only needed for OCR scanned PDFs and PDF-to-image conversion; basic PDF operations (text/table extraction, merge/split, creation) work without them.

### Metadata
- Reproducible: yes (under current network conditions)
- Related Files: skills/pdf/SKILL.md, AGENTS.md
- See Also: —

---

## [ERR-20260630-004] npx_skills_install_github_timeout

**Logged**: 2026-06-30T00:00:00+08:00
**Priority**: medium
**Status**: resolved
**Area**: infra

### Resolution
- **Resolved**: 2026-06-30T13:08:00+08:00
- **Reason**: GitHub connectivity recovered. Retried installation of the same four skills; three succeeded globally (obsidian-vault, autoresearch, impeccable). One failed due to mismatched skill name in the repository (see ERR-20260630-005).
- **Notes**: The `PromptScript does not support global skill installation` warning appears for PromptScript-based agents but does not prevent Claude Code from loading the skill.

### Summary
`npx skills add <owner/repo@skill>` failed to clone GitHub repositories due to connection timeout on `github.com:443`.

### Error
```
Failed to clone https://github.com/mattpocock/skills.git: ...
fatal: unable to access 'https://github.com/mattpocock/skills.git/':
Failed to connect to github.com port 443 after 21113 ms: Could not connect to server

Failed to clone https://github.com/github/awesome-copilot.git: ...
error: RPC failed; curl 28 Recv failure: Connection was reset

Failed to clone https://github.com/fredrikaverpil/dotfiles.git: ...
fatal: unable to access 'https://github.com/fredrikaverpil/dotfiles.git/':
Failed to connect to github.com port 443 after 21086 ms: Could not connect to server

Failed to clone https://github.com/pbakaus/impeccable.git: ...
fatal: unable to access 'https://github.com/pbakaus/impeccable.git/':
Failed to connect to github.com port 443 after 21089 ms: Could not connect to server
```

### Context
- Commands:
  - `npx skills add mattpocock/skills@obsidian-vault -g -y`
  - `npx skills add github/awesome-copilot@autoresearch -g -y`
  - `npx skills add fredrikaverpil/dotfiles@skill-creator -g -y`
  - `npx skills add pbakaus/impeccable@impeccable -g -y`
- Environment: Windows 11 Home China, Git Bash / MSYS2 shell
- Expected: Install external skills from skills.sh / GitHub
- Actual: All four installations failed at the repository clone step due to GitHub connectivity issues

### Suggested Fix
1. Retry when GitHub connectivity is stable (transient network issue).
2. Configure Git to use an available HTTPS proxy if one is set up in the environment:
   ```bash
   git config --global http.proxy http://proxy:port
   git config --global https.proxy http://proxy:port
   ```
3. Alternatively, clone the skill repositories manually via a working channel and install from local path:
   ```bash
   git clone https://github.com/mattpocock/skills.git
   npx skills add ./skills@obsidian-vault -g -y
   ```
4. For skills.sh packages, check if a mirror or alternate source is available.

### Metadata
- Reproducible: yes (under current network conditions)
- Related Files: .claude/skills/find-skills/SKILL.md
- See Also: ERR-20260511-003

---

## [ERR-20260709-006] missing_pdf_libraries_claude_md_mismatch

**Logged**: 2026-07-09T22:10:00+08:00
**Priority**: medium
**Status**: resolved
**Area**: infra

### Resolution
- **Resolved**: 2026-07-09T22:18:00+08:00
- **Reason**: 通过 `python -m pip install pypdf` 安装 `pypdf` 后，成功提取 `Loop-Engineering-IEEE.pdf` 并完成学习笔记整理。
- **Notes**: 已记录本次依赖缺失；`CLAUDE.md` 环境依赖表仍需同步更新，避免后续会话再次假设 PDF 库已预装。

### Summary
`CLAUDE.md` 声称已安装 `pypdf`、`pdfplumber`、`PyPDF2`，但当前 Python 环境中全部缺失，导致无法本地提取 PDF 文本。

### Error
```
ModuleNotFoundError: No module named 'pdfplumber'
ModuleNotFoundError: No module named 'pypdf'
ModuleNotFoundError: No module named 'PyPDF2'
```

### Context
- 命令：尝试用 `pdfplumber`、`pypdf`、`PyPDF2` 读取 `Loop-Engineering-IEEE.pdf`
- 环境：Windows 11, Python 3.13.3 (`/c/Users/11064/AppData/Local/Programs/Python/Python313/python`)
- 预期：按 `CLAUDE.md` 第 6 节环境依赖，PDF 库应已安装
- 实际：`pip list | grep -i pdf` 无输出

### Suggested Fix
1. 安装 `pypdf`（现代 PyPDF2 继任者，推荐）或 `PyPDF2` 以兼容现有 `summarize.py`
2. 同步更新 `CLAUDE.md` 环境依赖表，移除过时声明或添加安装命令
3. 对于本项目（文档知识库），基本 PDF 文本提取能力即可满足需求

### Metadata
- Reproducible: yes
- Related Files: `CLAUDE.md`, `.claude/skills/summarize/summarize.py`, `.claude/skills/pdf/SKILL.md`
- See Also: LRN-20260511-005 (summarize.py Windows 替代实现)

---

## [ERR-20260630-005] npx_skills_skill_name_not_found

**Logged**: 2026-06-30T13:08:00+08:00
**Priority**: low
**Status**: resolved
**Area**: skills

### Resolution
- **Resolved**: 2026-06-30T21:16:00+08:00
- **Reason**: The intended skill was actually named `skillify` in the same repository. Installed successfully with `npx skills add fredrikaverpil/dotfiles@skillify -g -y` and copied to the project local `.claude/skills/` directory.
- **Notes**: The search result for `skill-creator` matched the repository but not the exact skill name inside it.

### Summary
`npx skills add fredrikaverpil/dotfiles@skill-creator` failed because the repository does not contain a skill named `skill-creator`.

### Error
```
No matching skills found for: skill-creator

Available skills:
  - aip
  - codebase-audit
  - gh-cli
  - gh-pr
  - git-commit
  - golang-style
  - neovim
  - nvim-config
  - nvim-plugin
  - obsidian
  - plan-interview
  - proof
  - self-review
  - skillify
```

### Context
- Command: `npx skills add fredrikaverpil/dotfiles@skill-creator -g -y`
- Environment: Windows 11 Home China, Git Bash / MSYS2 shell
- Expected: Install a skill named `skill-creator`
- Actual: The repository `fredrikaverpil/dotfiles` only exposes a skill named `skillify`

### Suggested Fix
Install the correct skill name from the same repository:

```bash
npx skills add fredrikaverpil/dotfiles@skillify -g -y
```

Or search for another skill creator helper if `skillify` is not the intended one.

### Metadata
- Reproducible: yes
- Related Files: .claude/skills/find-skills/SKILL.md
- See Also: ERR-20260630-004

---


---

## [ERR-20260719-001] bash_heredoc_backtick_substitution

**Logged**: 2026-07-19
**Priority**: medium
**Status**: resolved
**Area**: tools

### Summary
向 Markdown 文件追加内容时，未加引号的 heredoc（`<< EOF`）导致文中反引号路径被 bash 当作命令替换执行，内容被吞并产生大量 "command not found" 噪音。

### Error
```
.claude/CLAUDE.md: line 5: ---: command not found
.claude/skills/autoresearch/SKILL.md: line 2: name:: command not found
...
```
写入结果的 `**文件**: ` 一行中 4 个反引号路径全部消失，变成空逗号列表。

### Context
- Command: `cat >> file << EOF`（heredoc 含 `$TS` 变量与多个反引号包裹的路径）
- Environment: Windows 11 Git Bash
- 原因：未加引号的 heredoc 会同时展开 `$变量` **和**反引号命令替换；被"执行"的是 Markdown 文档，逐行报错但无副作用

### Suggested Fix
含 Markdown 反引号的内容一律用带引号的定界符 `<< 'EOF'`（全不展开）；如确需变量展开，先对反引号转义 `\``，或改用 Write/Edit 工具写文件。

### Metadata
- Reproducible: yes
- Related Files: 本次追加操作（Work 仓库 `.learnings/LEARNINGS.md` 已手动修复）

### Resolution
- **Resolved**: 2026-07-19
- **Notes**: 当场发现并用 Edit 修复被吞行；本条用 `<< 'EOF'` 写入验证通过。

---

## [ERR-20260726-001] github_push_network_blocked

**Logged**: 2026-07-26T23:35:00+08:00
**Priority**: medium
**Status**: resolved
**Area**: infra

### Resolution
- **Resolved**: 2026-07-31
- **Notes**: 网络自行恢复后 SSH 推送一次成功（`989f514..d996bc9 master -> master`），与 ERR-20260630-004 同模式：GFW 干扰为间歇性，无需改配置，等待恢复后重试即可。

### Summary
git push 到 GitHub 全面失败：SSH 22 端口超时、SSH 443 端口连接重置、HTTPS 推送反复被重置（TLS EOF / HTTP2 framing / connect timeout），本机无代理可用。提交已安全保存在本地 master，待网络恢复后补推。

### Error
```
ssh: connect to host github.com port 22: Connection timed out
ssh -p 443 git@ssh.github.com → Connection reset by 20.205.243.160 port 443
git push https://... → Recv failure: Connection was reset
                     → TLS connect error: unexpected eof while reading
                     → Failed to connect to github.com port 443 after 21078 ms
                     → Error in the HTTP2 framing layer
git -c http.version=HTTP/1.1 push → SSL_read: unexpected eof while reading
```

### Context
- Command: `git push`（SSH 远程与一次性 HTTPS URL 均试过，共 6 次尝试，含强制 HTTP/1.1）
- Environment: Windows 11, Git Bash, 国内网络；本机 7890/7897/10809/1080/10808/8889 端口均无代理监听
- 对比现象：`curl -sI https://github.com` 曾返回 200——主页可达但 git 推送（POST 大数据）被针对性重置，符合 GFW 间歇性/按流量特征干扰
- 本地提交 `f67ce4c` 已在 master，内容未丢失

### Suggested Fix
1. 网络恢复后直接 `git push origin master`（参照 ERR-20260630-004，同类问题曾自行恢复）
2. 若用户有可用的系统代理/VPN，启动后用 `git -c http.proxy=http://127.0.0.1:<port> push origin master` 推送
3. 不建议通过第三方 GitHub 镜像站推送（凭据需经镜像中转，有泄露风险）

### Metadata
- Reproducible: yes (under current network conditions)
- Related Files: 无（网络层问题）
- See Also: ERR-20260630-004
- Pattern-Key: network.github_unreachable
- Recurrence-Count: 2
