---
name: git-upload-push
description: One-click git add, commit, and push for the current repository. Trigger when the user says "上传", "推送", "git push", "提交代码", "commit and push", or similar upload/push intents.
metadata:
---

# Git 上传推送

一键完成当前 git 仓库的 `git add -A` → `git commit` → `git push` 流程。适用于快速提交本地变更到远程仓库。

## 触发条件

用户提到以下任一表达时调用本 skill：

- "上传代码"
- "推送"
- "git push"
- "提交代码"
- "commit and push"
- "保存到远程"
- "推一下"

## 快速参考

| 情况 | 操作 |
|------|------|
| 查看当前状态 | `python .claude/skills/git-upload-push/scripts/git-upload-push.py status` |
| 获取 commit message 建议 | `python .claude/skills/git-upload-push/scripts/git-upload-push.py suggest` |
| 一键 add/commit/push（带确认） | `python .claude/skills/git-upload-push/scripts/git-upload-push.py push "你的提交说明"` |
| 跳过确认直接推送 | `python .claude/skills/git-upload-push/scripts/git-upload-push.py push "你的提交说明" --yes` |

## 工作流程

1. **检查当前分支**：如果在默认分支（如 `main`），会提示建议先创建功能分支。
2. **查看变更摘要**：展示 `git status --short` 结果。
3. **确认或生成 commit message**：用户可提供说明，或由脚本根据变更文件类型生成建议。
4. **执行提交**：自动在 commit message 末尾追加 `Co-Authored-By: Claude <noreply@anthropic.com>`。
5. **推送到远程**：如果分支无上游，自动执行 `git push -u origin <branch>`。

## 一分钟示例

**用户**："上传代码，提交信息：适配 .claude 工作区"

**Claude**：
1. 运行 `status` 查看当前分支和变更
2. 运行 `push "适配 .claude 工作区"`
3. 推送完成

## 文件结构

```
git-upload-push/
├── SKILL.md              ← 本文件（入口与触发条件）
├── reference.md          ← 详细用法、分支策略、commit 规范
├── gotchas.md            ← 常见陷阱与安全提醒
├── config.json           ← 默认配置
└── scripts/
    └── git-upload-push.py ← 辅助脚本
```

## 注意事项

- 本 skill 会执行 outward-facing 操作（推送到远程），默认会要求确认。
- 不建议在默认分支直接推送；如有需要，脚本会警告并建议创建分支。
- 不要在 commit message 中包含密钥、Token、密码等敏感信息。

详见 [`reference.md`](./reference.md) 和 [`gotchas.md`](./gotchas.md)。
