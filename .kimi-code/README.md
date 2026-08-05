# .kimi-code/ 目录说明

本目录为 `MarkDown_Learn` 知识库项目的 **Kimi Code 项目级配置区**，由 Kimi Code 在会话启动时自动扫描加载。

## 当前内容

### agents/ — 自定义子代理

主 Agent 可按任务需要委派（独立上下文执行，结果回传主会话）：

| 子代理 | 用途 | 工具权限 |
|--------|------|----------|
| `note-organizer` | 批量整理 Inbox / 未归档笔记（移动 + 重命名） | Read, Write, Edit, Glob, Grep, Bash |
| `kb-reviewer` | 只读合规审查，输出分级报告 | Read, Grep, Glob |

### skills/ — 项目技能（17 个）

由 `.claude/skills/` 复制适配而来（`CLAUDE.md` 引用已统一改为 `AGENTS.md`）。可用 `/skill:<名称>` 手动调用，或由模型按 description 自动触发。完整清单与触发时机见根目录 `AGENTS.md` §4.1。

## 与 .claude/ 的关系

| 目录 | 归属 | 说明 |
|------|------|------|
| `.kimi-code/` | Kimi Code | 本目录，agents + skills |
| `.claude/skills/` | Claude Code | 技能的源副本，两边内容应保持一致 |
| `.claude/references/knowledge-base/` | 共享 | 车规 MCU 参考资料，两套工具共同按路径引用，未复制 |
| `.claude/memory/` | 共享 | 记忆索引与文件分类速查表，未复制 |

## 维护约定

- 新增/修改技能时，优先改 `.claude/skills/` 后同步到 `.kimi-code/skills/`（或反之），保持两边一致。
- 项目工作指南在根目录 `AGENTS.md`（Kimi Code）；`.claude/CLAUDE.md` 为 Claude Code 的对应版本。
- 本目录不含密钥等敏感信息，可随仓库提交。
