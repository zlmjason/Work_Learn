# Context Compress — 详细使用指南

本文件是 `context-compress` Skill 的详细参考。如果你只想知道何时触发以及输出格式，请阅读 [`SKILL.md`](./SKILL.md)。

---

## 触发方式

### 1. 手动触发（推荐）

用户输入以下任意一种表达时调用本 skill：

- `/context-compress`
- "上下文太多了，压缩一下"
- "快满了，帮我总结一下"
- "session 太长了，整理一下关键信息"
- "把前面的内容压缩一下"

### 2. 自动触发（需配置 hook）

Claude Code 本身无法直接感知自身上下文占用量，需要通过 `.claude/settings.json` 中的 hook 调用辅助脚本 [`scripts/context-check.py`](./scripts/context-check.py) 进行估算和提醒。

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

脚本会估算当前工作区中常见源文件/文档的总体 token 占用，并在接近阈值时输出警告。**注意：该脚本无法直接读取 Claude Code 内部对话状态**，它只能基于文件大小给出参考提醒。真正的上下文压缩仍需手动调用 `/context-compress`。

---

## 压缩策略详解

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

**决策逻辑**：
- P0 必须保留：失去这些，新会话就无法理解「现在在做什么」和「已经定了什么」。
- P1 选择性保留：给出足够继续工作的上下文，但避免把全文搬进去。
- P2 约束性保留：不会直接影响当前任务理解，但能防止模型走回头路或违反用户偏好。

---

## 输出格式规范

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

### 字段说明

| 字段 | 说明 |
|------|------|
| 当前任务 | 用一句话概括用户最终意图，避免罗列中间探索 |
| 关键决策 | 只保留仍然有效的决策，已推翻的不要写 |
| 已修改文件 | 文件路径 + 改动原因，不贴完整 diff |
| 关键代码/配置 | ≤ 30 行，超过必须用 `// ...` 省略 |
| 未完成事项 | 使用 `[ ]` 复选框格式，便于后续 TodoWrite 继续跟踪 |
| 约束与偏好 | 用户的硬性规则、命名规范、禁用方案等 |
| 继续指令 | 用户原话或下一步建议，降低上下文切换成本 |

---

## 使用示例

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

---

## 与 self-improving-agent 的协作

`context-compress` 解决的是「对话上下文过长」问题，但压缩出来的关键决策如果具有长期价值，应该进一步沉淀到项目记忆中。

典型工作流：

1. 会话过长 → 调用 `/context-compress`
2. 摘要中发现重要决策、踩坑经验、用户纠正 → 使用 [`self-improving-agent`](../self-improving-agent/SKILL.md) 记录到 `.learnings/`
3. 高频出现的模式 → 晋升（promote）到 `.claude/CLAUDE.md`

例如：
- 用户在 SPI 初始化话题中纠正了 "CPHA 应该是 0 不是 1" → 记录为 `LRN-YYYYMMDD-XXX` correction
- 发现 "AURIX 的 DMA 通道号必须从 1 开始数" → 记录为 `LRN-YYYYMMDD-XXX` knowledge_gap
- 多次出现 "命名规范里禁止空格" 被违反 → 晋升到 `CLAUDE.md`

---

## context-check.py 脚本参数

位置：[`scripts/context-check.py`](./scripts/context-check.py)

### 常用命令

```bash
# 估算单个文件
python .claude/skills/context-compress/scripts/context-check.py path/to/file.md

# 估算多个文件并在超过阈值时报警
python .claude/skills/context-compress/scripts/context-check.py --warn-at-percent 75 file1.md file2.c

# 扫描工作区常见文件
python .claude/skills/context-compress/scripts/context-check.py --scan-workspace --warn-at-percent 75

# 输出 JSON（便于 Hook 或脚本解析）
python .claude/skills/context-compress/scripts/context-check.py --scan-workspace --json

# 始终返回 0（适合 Hook 场景，避免阻断用户输入）
python .claude/skills/context-compress/scripts/context-check.py --scan-workspace --warn-at-percent 75 --exit-zero
```

### 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `inputs` | 文件或目录路径列表 | 空（从 stdin 读取） |
| `--scan-workspace` | 扫描当前工作区常见源文件/文档 | `False` |
| `--warn-at-percent` | 超过上下文窗口百分比时报警 | `75` |
| `--context-limit` | 上下文窗口大小（tokens） | `200000` |
| `--top-n` | 扫描时显示最大的 N 个文件 | `20` |
| `--json` | 以 JSON 格式输出 | `False` |
| `--exit-zero` | 即使超过阈值也返回 0 | `False` |

### 估算方法

脚本优先使用 `tiktoken` 的 `cl100k_base` 编码器；未安装时回退到启发式估算：
- 连续 ASCII 字符按 4 字符/token
- CJK 字符按 1.5 字符/token

---

## 配置说明

默认配置见 [`config.json`](./config.json)。当前 `context-check.py` 仍以内置默认值为权威源，`config.json` 用于文档化和未来统一读取。

如需调整阈值，建议同步修改 `config.json` 和脚本中的常量，保持一致。

---

## 常见陷阱

详见 [`gotchas.md`](./gotchas.md)。
