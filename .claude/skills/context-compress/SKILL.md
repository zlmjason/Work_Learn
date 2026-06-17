---
name: context-compress
description: Compress conversation context when approaching the model's context window limit. Use when the session grows long, responses slow down, or the user explicitly asks to compress/summarize the conversation. Can be triggered manually via /context-compress or wired into settings.json hooks for automatic warnings.
metadata:
---

# Context Compress

一个用于在上下文接近模型窗口上限时自动压缩/摘要对话历史的 Claude Code 本地 skill。

## 触发方式

### 1. 手动触发（推荐）

用户输入以下任意一种表达时调用本 skill：

- `/context-compress`
- "上下文太多了，压缩一下"
- "快满了，帮我总结一下"
- "session 太长了，整理一下关键信息"
- "把前面的内容压缩一下"

### 2. 自动触发（需配置 hook）

Claude Code 本身无法直接感知自身上下文占用量，需要通过 `.claude/settings.json` 中的 hook 调用辅助脚本 `scripts/context-check.py` 进行估算和提醒。

## 压缩策略

当触发压缩时，按以下优先级保留信息：

| 优先级 | 保留内容 | 丢弃/精简内容 |
|--------|----------|---------------|
| P0 | 当前任务目标与用户最终意图 | 中间探索性提问 |
| P0 | 已达成的重要决策和约定 | 已推翻的旧方案 |
| P1 | 已修改/创建的文件清单及变更原因 | 未改动的文件全文 |
| P1 | 关键代码/配置片段（≤ 30 行） | 大段未修改代码 |
| P1 | 未完成的待办事项（Todo） | 已完成的详细步骤 |
| P2 | 用户的硬性约束（命名规范、禁用方案等） | 一般性讨论 |
| P2 | 出现过的关键错误及其根因 | 已解决错误的完整日志 |

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

## Hook 自动提醒配置

在 `.claude/settings.json` 中添加以下配置，可在每次提交用户提示前运行检查脚本：

```json
{
  "hooks": {
    "UserPromptSubmit": [{
      "matcher": "",
      "hooks": [{
        "type": "command",
        "command": "python .claude/skills/context-compress/scripts/context-check.py --scan-workspace --warn-at-percent 75 --exit-zero"
      }]
    }]
  }
}
```

脚本会估算当前工作区中常见源文件/文档的总体 token 占用，并在接近阈值时输出警告。注意：该脚本**无法直接读取 Claude Code 内部对话状态**，它只能基于文件大小给出参考提醒。真正的上下文压缩仍需手动调用 `/context-compress`。

## 手动使用示例

**用户**：`/context-compress`

**Claude**：
> 已压缩当前会话上下文。以下是摘要：
>
> ## 上下文摘要（Compressed Context）
> ### 当前任务
> 为 AURIX TC3xx 编写 SPI 主控制器初始化代码...
> ### 关键决策
> 1. 使用 QSPI0 通道 0，CPOL=0/CPHA=0...
> ### 已修改文件
> - `01_Hardware_硬件层/.../HW_Periph_Comm_SPI_Init.md`：补充初始化流程
> ### 未完成事项
> - [ ] 完成 DMA 传输配置
> - [ ] 补充错误处理分支
> ### 继续指令
> 继续编写 SPI 初始化函数并验证时序。

用户可以将这段摘要复制到新会话开头，继续工作而不丢失关键信息。

## 注意事项

1. **Claude Code 无法主动知道上下文窗口还剩多少**。自动触发依赖 hook 脚本的外部估算，仅作提醒。
2. 压缩会丢失细节，重要代码片段应单独保存到文件而非仅留在对话中。
3. 如果对话涉及大量文件修改，优先将状态写入 `.learnings/` 或项目文档，而不是依赖对话上下文。
4. 当前 skill 主要面向中文工作区，输出保持中文，技术术语保留英文。
