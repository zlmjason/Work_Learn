# Git 上传推送 — 详细参考

本文件是 `git-upload-push` Skill 的详细参考。快速入口请阅读 [`SKILL.md`](./SKILL.md)。

---

## 1. 命令说明

脚本位置：`.claude/skills/git-upload-push/scripts/git-upload-push.py`

### 1.1 查看状态

```bash
python .claude/skills/git-upload-push/scripts/git-upload-push.py status
```

输出示例：

```
Branch: feature/gtm-tom-pwm (default: main)

=== Status ===
M  Project/AppSw/App/Leon_Gtm/LeonGtm_Tom.c
?? .claude/skills/git-upload-push/
```

### 1.2 生成 commit message 建议

```bash
python .claude/skills/git-upload-push/scripts/git-upload-push.py suggest
```

脚本会根据变更文件类型推断前缀，例如：

- 仅代码文件 → `Update driver code`
- 仅文档 → `Update documentation`
- 仅配置 → `Update configuration`
- 混合 → `Update driver code; update documentation`

### 1.3 执行上传推送

```bash
python .claude/skills/git-upload-push/scripts/git-upload-push.py push "你的提交说明"
```

流程：

1. 检查是否在默认分支，如果是则警告
2. 展示 `git status --short` 摘要
3. 询问是否继续（需要输入 `y`/`yes`）
4. 执行 `git add -A`
5. 执行 `git commit -m "你的提交说明"`
6. 自动追加 `Co-Authored-By: Claude <noreply@anthropic.com>`
7. 执行 `git push` 或 `git push -u origin <branch>`

### 1.4 跳过确认

```bash
python .claude/skills/git-upload-push/scripts/git-upload-push.py push "你的提交说明" --yes
```

> ⚠️ 仅在完全确定变更无误时使用。

---

## 2. 分支策略

### 2.1 默认分支保护

当前项目默认分支为 `main`。根据 `.claude/CLAUDE.md` 约定：

> Commit or push only when the user asks. If on the default branch, branch first.

脚本会检测当前分支是否为默认分支。如果是，会提示建议先创建功能分支：

```bash
git checkout -b feature/your-topic
git push -u origin feature/your-topic
```

### 2.2 功能分支命名建议

| 类型 | 命名 | 示例 |
|------|------|------|
| 新功能 | `feature/简短描述` | `feature/gtm-tom-pwm` |
| Bug 修复 | `fix/简短描述` | `fix/irq-routing-core1` |
| 文档 | `doc/简短描述` | `doc/update-claude-guide` |
| 配置 | `config/简短描述` | `config/add-mcal-cfg` |

---

## 3. Commit Message 规范

### 3.1 基本格式

```
[类型] 简短描述（50 字符以内）

详细说明（可选）

Co-Authored-By: Claude <noreply@anthropic.com>
```

### 3.2 常用类型

| 类型 | 含义 |
|------|------|
| `feat` | 新功能 |
| `fix` | 修复 |
| `docs` | 文档 |
| `refactor` | 重构 |
| `config` | 配置变更 |
| `test` | 测试 |
| `chore` | 其他杂项 |

### 3.3 示例

```
feat: add GTM TOM PWM channel initialization

- Configure TOM[0] CH[0] ~ CH[5] for motor PWM
- Set clock source and period/compare registers

Co-Authored-By: Claude <noreply@anthropic.com>
```

---

## 4. 配置项

`config.json`：

| 字段 | 默认值 | 说明 |
|------|--------|------|
| `defaultCommitPrefix` | `[auto]` | 未提供 message 时的默认前缀 |
| `requireCommitMessage` | `true` | 是否必须提供 commit message |
| `confirmBeforePush` | `true` | 推送前是否确认 |
| `defaultBranchProtection` | `true` | 是否检测默认分支并警告 |

---

## 5. 异常处理

| 场景 | 处理 |
|------|------|
| 没有变更 | 脚本提示 "No changes to commit." 并退出 |
| 在默认分支 | 警告并建议创建分支；加 `--yes` 仍可强制推送 |
| commit message 为空 | 脚本拒绝执行 |
| 推送失败 | 输出 git 错误信息，由用户处理 |
| 无远程仓库 | `git push` 会失败，需先配置 remote |

---

## 6. 替代方案

如果需要更精细控制，可以直接使用 git 命令：

```bash
git status
git add -A
git commit -m "你的提交说明"
git push
```
