# Agent 案例分析

> 收集和分析典型 Agent 设计案例，从中提炼可复用的模式。重点基于论文 *Agent Systems with Harness Engineering* 中的 Table 1 系统对比。

## 核心问题

优秀 Agent 是怎么设计的？有哪些值得借鉴的做法和教训？

## 结论

不同部署场景需要不同的 Harness 设计权衡。Claude Code、OpenClaw、Hermes Agent 在同样的四大组件上做出了不同选择。

---

## 1. 三个工业级系统对比

| 系统 | 核心优化目标 | Workflow | Memory | Skills | Multi-Agent | 适用场景 |
|------|-------------|----------|--------|--------|-------------|----------|
| **Claude Code** | Human-in-the-loop safety | 感知-规划-执行循环 + 用户确认 | 会话级 + 项目指令 | `.claude/skills/` 多文件结构 | 子 Agent 委派 | 开发者辅助、代码编辑 |
| **OpenClaw** | Composable extensibility | 声明式上下文、多通道路由 | 工作区级持久记忆 | Workspace-level skill 注入 | 会话间共享、跨会话通信 | 平台级 Agent 编排 |
| **Hermes Agent** | Autonomous self-governance | 自主规划 + 自我监控 | 用户画像 + 自适应记忆 | 自适应 Skill 选择 | 预算控制、安全过滤 | 自主终端、长期任务 |

### 1.1 Claude Code

- **设计哲学**：安全优先的开发者助手
- **关键机制**：
  - 分层权限（L0-L3）
  - 项目指令约束（`CLAUDE.md`）
  - 多文件 Skill 结构
  - 危险操作前确认
- **可借鉴点**：人机协作的安全设计、Skill 工程化

### 1.2 OpenClaw

- **设计哲学**：可组合、可扩展的 Agent 平台
- **关键机制**：
  - 工作区级上下文注入
  - Skill 跨会话共享
  - 多通道路由
- **可借鉴点**：Workspace 级记忆、Skill 的生态化管理

### 1.3 Hermes Agent

- **设计哲学**：自主治理的终端 Agent
- **关键机制**：
  - 预算控制
  - 安全过滤
  - 自适应提示
- **可借鉴点**：自主任务的资源与安全管理

## 2. 其他典型案例

| 案例 | 场景 | 关键设计 | 可复用点 |
|------|------|----------|----------|
| AutoGPT | 自主任务 | 目标驱动 + 工具链 | ReAct 模式 |
| Devin | 端到端开发 | 长时规划 + 环境隔离 | Plan-and-Execute |
| GitHub Copilot | 代码补全 | 上下文感知 + 快速响应 | 低延迟工具调用 |

## 3. 本仓库案例

### 3.1 context-compress

- **解决的问题**：会话上下文过长
- **Harness 设计**：
  - Skill 多文件结构
  - 压缩策略（P0/P1/P2 优先级）
  - Hook 自动提醒
- **可借鉴点**：如何把经验封装为可复用 Skill

### 3.2 self-improving-agent

- **解决的问题**：持续学习与错误沉淀
- **Harness 设计**：
  - `.learnings/` 结构化日志
  - Learning → Skill → CLAUDE.md 晋升路径
- **可借鉴点**：Agent 的可进化机制

## 4. 案例对比框架

当分析一个新的 Agent 系统时，可以从以下维度入手：

1. **目标场景**：解决什么问题？面向谁？
2. **Harness 层级**：Layer 1 / 2 / 3？
3. **四大组件**：Workflow、Memory、Skills、Multi-Agent 如何设计？
4. **模型适配**：Context Engineering 还是 Agentic Training？
5. **人机边界**：自主程度如何？什么时候求助于人？
6. **评估重点**：正确性、效率、安全性、过程质量？

## 关联笔记

- [[Agent_Skill_Development_Guide]] — Skill 设计方法
- [[Agent_Memory_Learning_System]] — 持续学习机制
- [[Agent_Evaluation_Metrics]] — 评估维度
- [论文分析笔记](../50738_Agent_Systems_with_Harne_分析笔记.md)

## 标签

#Agent #CaseStudy #Pattern #ClaudeCode #OpenClaw #Hermes
