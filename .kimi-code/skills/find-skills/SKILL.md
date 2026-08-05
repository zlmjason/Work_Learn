---
name: find-skills
description: Discover and install agent skills from the open skills ecosystem. Trigger when the user asks "how do I do X", "find a skill for X", "is there a skill that can...", "can you do X" for specialized capabilities, or expresses interest in extending agent capabilities.
metadata:
---

# Find Skills

帮助用户从开放 Agent Skills 生态中发现和安装 Skill。

## 触发条件

用户提到以下任一表达时调用本 skill：

- "how do I do X"（X 可能是常见任务）
- "find a skill for X" / "is there a skill that can..."
- "can you do X"（X 是专业化能力）
- 想扩展 Agent 能力
- 想搜索工具、模板、工作流
- 希望某个特定领域有 Skill 帮助（如 design、testing、deployment）

## 快速参考

| 情况 | 操作 |
|------|------|
| 想找 Skill | `npx skills find [query]` |
| 找到后安装 | `npx skills add <owner/repo@skill> -g -y` |
| 检查更新 | `npx skills check` |
| 更新所有 | `npx skills update` |
| 找不到 | 直接用通用能力帮助，或建议 `npx skills init` 自建 |

## 一分钟示例

```bash
# 搜索 React 性能优化相关 Skill
npx skills find react performance

# 安装找到的 Skill
npx skills add vercel-labs/agent-skills@vercel-react-best-practices -g -y
```

## 文件结构

```
find-skills/
├── SKILL.md       ← 本文件（入口与触发条件）
├── reference.md   ← Skills CLI 详细用法、搜索技巧、常见类别
├── gotchas.md     ← 常见陷阱（搜索词太宽、未确认安装等）
├── config.json    ← CLI 命令与热门来源
└── _meta.json
```

## 常见陷阱

- 把简单通用问题误判为需要 Skill
- 搜索词太宽泛导致结果不相关
- 未向用户确认就直接安装
- 安装后未验证 Skill 是否可用
- 忽略本地 `.claude/skills/` 已有 Skill

详见 [`gotchas.md`](./gotchas.md)。

## 详细用法

完整搜索流程、安装示例、常见类别、搜索技巧见 [`reference.md`](./reference.md)。
