# Git 上传推送 — 陷阱与常见失败模式

本文件记录使用 `git-upload-push` skill 时容易犯的错误和安全提醒。

---

## 1. 在默认分支直接推送

**表现**：用户在 `main` 分支上说 "上传代码"，脚本直接 add/commit/push。

**后果**：污染主分支历史，可能影响团队协作和 CI/CD。

**正确做法**：
- 在默认分支时，先创建功能分支：
  ```bash
  git checkout -b feature/your-topic
  ```
- 然后再调用本 skill 推送。

---

## 2. Commit message 过于笼统

**表现**："修改代码"、"更新"、"提交" 等无意义描述。

**后果**：后续通过 `git log` 无法快速理解变更内容。

**正确做法**：
- 说明变更模块和目的，例如：
  - `feat: add GTM TOM PWM initialization`
  - `fix: correct IRQ routing for Core1 STM handler`
  - `docs: update AGENTS.md with build notes`

---

## 3. 未检查 status 就推送

**表现**：直接调用 push，没注意把不想提交的文件也加入了。

**后果**：编译产物、临时文件、密钥等被误提交。

**正确做法**：
- 推送前先运行 `status` 子命令查看变更：
  ```bash
  python .claude/skills/git-upload-push/scripts/git-upload-push.py status
  ```
- 确认 `.gitignore` 已正确配置（如 `Project/iROM/` 不应被提交）。

---

## 4. Commit message 泄露敏感信息

**表现**：提交信息里写 "add API key: abc123..." 或包含内部服务器地址。

**后果**：敏感信息进入 git 历史，即使后续删除也可能被恢复。

**正确做法**：
- 不要在 commit message 中写密钥、Token、密码、内部 URL。
- 敏感配置应通过环境变量或本地配置文件管理，并加入 `.gitignore`。

---

## 5. 跳过确认导致误操作

**表现**：使用 `--yes` 参数快速推送，未仔细检查变更。

**后果**：错误代码或未完成的修改被推送到远程。

**正确做法**：
- 默认带确认流程，仔细查看 `git status --short` 摘要后再输入 `y`。
- `--yes` 仅在你完全确定变更无误时使用。

---

## 6. 忽略推送失败信息

**表现**：脚本提示 push failed，但没有查看具体错误就重复执行。

**后果**：可能反复失败或造成冲突。

**正确做法**：
- 先阅读 git 错误输出。
- 常见原因：
  - 远程有更新，需要先 `git pull`
  - 没有写权限
  - 网络问题
  - 分支被保护

---

## 7. 跨仓库使用脚本

**表现**：在多仓库工作区中调用脚本，结果操作到了错误的仓库。

**后果**：变更被提交到非目标仓库。

**正确做法**：
- 脚本通过 `git rev-parse --show-toplevel` 自动定位当前工作目录所属的仓库根目录。
- 调用前确认当前工作目录正确。

---

## 8. 大文件未忽略

**表现**：PDF、编译产物、日志文件等被一起 add 并推送。

**后果**：仓库体积膨胀，clone 变慢。

**正确做法**：
- 确保 `.gitignore` 已包含：
  - `Project/iROM/`
  - `*.log`
  - `.vscode/` 等本地 IDE 配置（视项目约定而定）
- 推送前检查 status 中的未跟踪文件。

---

## 9. 自动追加 Co-Authored-By 重复

**表现**：commit message 中已经手动写了 `Co-Authored-By: Claude ...`，脚本又追加一遍。

**后果**：commit message 中出现重复的 Co-Authored-By 行。

**正确做法**：
- 脚本会检测 message 中是否已有 `Co-Authored-By:`，有则不再追加。
- 如果你手动写了不同格式的署名，注意检查最终 message。

---

## 10. 没有配置 Git 用户信息

**表现**：首次在新环境使用，git commit 报错：

```
*** Please tell me who you are.
```

**正确做法**：
- 配置全局 Git 用户信息：
  ```bash
  git config --global user.name "Your Name"
  git config --global user.email "your.email@example.com"
  ```
