# Agent 人机协作模式

> 如何设计 Agent 与人类的协作方式，使其既高效又不越界。Claude Code 在该维度上优化 **human-in-the-loop safety**。

## 核心问题

Agent 应该在什么程度上自主？什么时候必须征求人类意见？

## 结论

人机协作应遵循 **分层授权** 原则：越危险、越不可逆、越涉及偏好的操作，越需要人类确认。

---

## 1. 授权层级

| 层级 | 操作类型 | 是否需要确认 |
|------|----------|--------------|
| L0 自动 | 只读、搜索、分析 | 否 |
| L1 低风险 | 创建草稿、本地修改 | 否，但需告知 |
| L2 中风险 | 修改配置文件、重命名文件 | 建议确认 |
| L3 高风险 | 删除、提交、推送、部署 | 必须确认 |

## 2. 有效确认的方式

- 明确说明要做什么
- 说明可能的影响
- 提供"是/否/修改"选项
- 不要假设默认同意

## 3. 保持人类在循环中的场景

- 涉及安全的功能安全相关代码
- 用户明确禁止过的操作
- 结果不可逆的动作
- 需要创意或价值判断的决策

## 4. 减少干扰的场景

- 信息查询
- 草稿生成
- 本地非破坏性修改
- 已授权的常规任务

## 5. Claude Code 的人机协作设计

论文 *Agent Systems with Harness Engineering* 将 Claude Code 归类为 **optimizes for human-in-the-loop safety** 的系统：

- 分层权限模型
- 危险操作前主动确认
- 项目指令（`CLAUDE.md`）约束行为边界
- 用户可随时介入和纠正

## 关联笔记

- [[Agent_Design_Core_Principles]] — 边界明确原则
- [[Agent_Evaluation_Metrics]] — 协作体验评估
- [论文分析笔记](../50738_Agent_Systems_with_Harne_分析笔记.md)

## 标签

#Agent #HumanInTheLoop #Collaboration #UX #Safety
