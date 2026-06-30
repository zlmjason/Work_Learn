# Agent 工具与 MCP 集成

> 如何通过工具调用和 MCP 扩展 Agent 的能力边界。

## 核心问题

Agent 本身只有语言模型能力，如何安全、有效地使用外部工具？

## 结论

工具集成应遵循 **显式声明、结构化输入输出、权限控制、失败兜底** 的原则。

---

## 1. 工具类型

| 类型 | 说明 | 示例 |
|------|------|------|
| 本地脚本 | 仓库内的可执行脚本 | `.claude/skills/*/scripts/*.py` |
| 系统命令 | Bash 等系统工具 | `git`、`python`、`npm` |
| MCP Server | 标准化外部服务 | 文件系统、数据库、搜索 |
| 第三方 API | 网络服务 | GitHub、MinerU、搜索 API |

## 2. Claude Code 中的工具使用

Claude Code 原生支持：

- `Bash` — 执行命令
- `Read` / `Write` / `Edit` — 文件操作
- `Glob` / `Grep` — 搜索
- `Agent` — 委派子 Agent
- `Skill` — 调用已注册 Skill

## 3. MCP 集成

MCP（Model Context Protocol）是 Anthropic 推出的标准协议，用于连接模型与外部数据源/工具。

关键概念：

- MCP Server：提供工具、资源、提示的服务端
- MCP Client：Claude Code 等客户端
- Tool Schema：工具名称、描述、参数定义

## 4. 安全原则

- 危险操作前确认用户
- 不自动执行不可逆命令
- 不传播密钥和敏感信息
- 工具失败时提供清晰错误信息

## 5. Skill 与工具的关系

Skill 是**面向任务**的封装，工具是**面向操作**的封装。

```text
Skill = 触发条件 + 流程 + 工具组合 + 陷阱提示
Tool  = 单一可执行能力
```

## 关联笔记

- [[Agent_Skill_Development_Guide]] — 如何封装 Skill
- [[Agent_Architecture_Components]] — 工具层在架构中的位置

## 标签

#Agent #Tools #MCP #ClaudeCode
