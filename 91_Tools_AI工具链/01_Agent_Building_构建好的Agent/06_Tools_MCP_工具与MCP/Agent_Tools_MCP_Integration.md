# Agent 工具与 MCP 集成

> 如何通过工具调用和 MCP 扩展 Agent 的能力边界。本文基于论文 *Agent Systems with Harness Engineering* 中的 **Action Interface / Workflow Infrastructure** 层。

## 核心问题

Agent 本身只有语言模型能力，如何安全、有效地使用外部工具？

## 结论

工具集成应遵循 **显式声明、结构化输入输出、权限控制、失败兜底** 的原则。Harness 的 Action Interface 是模型与环境的桥梁。

---

## 1. 工具类型

| 类型 | 说明 | 示例 |
|------|------|------|
| 本地脚本 | 仓库内的可执行脚本 | `.claude/skills/*/scripts/*.py` |
| 系统命令 | Bash 等系统工具 | `git`、`python`、`npm` |
| MCP Server | 标准化外部服务 | 文件系统、数据库、搜索 |
| 第三方 API | 网络服务 | GitHub、MinerU、搜索 API |

## 2. Action Interface 的三层演化

| 层级 | 能力 | 示例 |
|------|------|------|
| Layer 1 | 单次工具调用 | 查询天气、读取文件 |
| Layer 2 | 多步骤、有状态的工具组合 | Coding Agent、自动化测试 |
| Layer 3 | 跨会话、个性化的工具使用 | 个人助手记住常用工具链 |

## 3. Claude Code 中的工具使用

Claude Code 原生支持：

- `Bash` — 执行命令
- `Read` / `Write` / `Edit` — 文件操作
- `Glob` / `Grep` — 搜索
- `Agent` — 委派子 Agent
- `Skill` — 调用已注册 Skill

## 4. MCP 集成

MCP（Model Context Protocol）是 Anthropic 推出的标准协议，用于连接模型与外部数据源/工具。

关键概念：

- MCP Server：提供工具、资源、提示的服务端
- MCP Client：Claude Code 等客户端
- Tool Schema：工具名称、描述、参数定义

## 5. 工具粒度设计

| 粒度 | 特点 | 适用场景 |
|------|------|----------|
| 粗粒度 | 一个工具完成多件事 | 减少调用次数，但灵活性低 |
| 细粒度 | 一个工具只做一件事 | 灵活组合，但调用链长 |
| 中等粒度 | 按常见任务封装 | 平衡灵活性与效率 |

## 6. 安全原则

- 危险操作前确认用户
- 不自动执行不可逆命令
- 不传播密钥和敏感信息
- 工具失败时提供清晰错误信息

## 7. Skill 与工具的关系

Skill 是**面向任务**的封装，工具是**面向操作**的封装。

```text
Skill = 触发条件 + 流程 + 工具组合 + 陷阱提示
Tool  = 单一可执行能力
```

## 关联笔记

- [[Agent_Skill_Development_Guide]] — 如何封装 Skill
- [[Agent_Architecture_Components]] — 工具层在 Harness 架构中的位置
- [论文分析笔记](../99_Attachments_附件/50738_Agent_Systems_with_Harne/50738_Agent_Systems_with_Harne_分析笔记.md)

## 标签

#Agent #Tools #MCP #HarnessEngineering #ClaudeCode
