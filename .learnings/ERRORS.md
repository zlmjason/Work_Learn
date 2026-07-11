# Errors

Command failures and integration errors.

> 📑 汇总索引见 [INDEX.md](./INDEX.md)。架构决策见 [DECISIONS.md](./DECISIONS.md)，复发模式见 [PATTERNS.md](./PATTERNS.md)，Skill 注册表见 [SKILL_REGISTRY.md](./SKILL_REGISTRY.md)。

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

