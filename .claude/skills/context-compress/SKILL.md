---
name: context-compress
description: Compress conversation context when approaching the model's context window limit. Use when the session grows long, responses slow down, or the user explicitly asks to compress/summarize the conversation. Can be triggered manually via /context-compress or wired into settings.json hooks for automatic warnings.
metadata:
---

# Context Compress

一个用于在上下文接近模型窗口上限时压缩/摘要对话历史的 Claude Code 本地 skill。

## 触发条件

用户输入以下任意一种表达时调用本 skill：

- `/context-compress`
- "上下文太多了，压缩一下"
- "快满了，帮我总结一下"
- "session 太长了，整理一下关键信息"
- "把前面的内容压缩一下"

## 快速参考

| 情况 | 操作 |
|------|------|
| 用户手动请求压缩 | 执行压缩，输出结构化摘要 |
| Hook 报警提示接近上限 | 提醒用户运行 `/context-compress`，不要假设已自动压缩 |
| 压缩后需要长期保存决策/踩坑 | 使用 `self-improving-agent` 记录到 `.learnings/` |
| 不确定该保留什么 | 优先保留「当前任务」和「关键决策」，丢弃已推翻的旧方案 |

**常见陷阱**：详见 [`gotchas.md`](./gotchas.md)。

**详细用法**：触发方式、Hook 配置、压缩策略、脚本参数、Skill 联动见 [`reference.md`](./reference.md)。

## 输出格式

压缩后输出一段结构化的 "上下文摘要"，可直接作为新会话的起始提示：

```markdown
## 上下文摘要（Compressed Context）

### 当前任务
[一句话描述当前正在做什么]

### 关键决策
1. [决策 1：背景 → 选择 → 原因]
2. [决策 2：...]

### 已修改文件
- `[文件路径]`：[改动原因/内容摘要]

### 关键代码/配置
```c
// 不超过 30 行的核心片段
```

### 未完成事项
- [ ] [待办 1]
- [ ] [待办 2]

### 约束与偏好
- [必须遵守的规则 1]
- [用户偏好 2]

### 继续指令
[下一步建议或用户原话]
```

## 文件结构

```
context-compress/
├── SKILL.md      ← 本文件（入口与触发条件）
├── reference.md  ← 详细用法、Hook 配置、示例、脚本参数
├── gotchas.md    ← 常见陷阱与失败模式
├── config.json   ← 默认阈值与配置
└── scripts/
    └── context-check.py  ← Token 估算脚本
```

## 相关技能

- [`self-improving-agent`](../self-improving-agent/SKILL.md)：将压缩摘要中的重要决策、错误、知识盲区沉淀到 `.learnings/`
