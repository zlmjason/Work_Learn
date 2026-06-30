# Decisions

架构决策记录（ADR）。记录对项目有长期影响的选择、原因和后果。

> 新增决策请使用 `ADR-YYYYMMDD-XXX` 编号。决策状态包括：`proposed`、`accepted`、`deprecated`、`superseded`。

---

## [ADR-20260511-001] 不安装 WSL2

**Date**: 2026-05-11
**Status**: accepted
**Area**: infra

### Context

部分 Skill（如原版 `summarize` CLI）依赖 Homebrew / Unix 环境。Windows 上可选择安装 WSL2 来运行这些工具。

### Decision

不安装 WSL2。所有 Skill 改为 Windows 原生适配或 Python 替代实现。

### Consequences

- ✅ 减少系统复杂性和环境依赖
- ✅ 避免 WSL2 与 Windows 文件系统的性能/路径问题
- ⚠️ 需要为部分 Skill 编写 Windows 原生替代脚本（如 `summarize.py`）
- ⚠️ 某些仅 Homebrew 分发的工具无法直接使用

### Alternatives Considered

- 安装 WSL2 + Homebrew：可行，但增加环境复杂度，且与 Obsidian/Windows 工作流不够无缝。

---

## [ADR-20260511-002] Kimi-Only 工作流

**Date**: 2026-05-11
**Status**: accepted
**Area**: workflow

### Context

用户没有 Gemini/OpenAI/Anthropic/xAI 等第三方 LLM API 密钥，仅通过 Kimi2.6 访问 AI 能力。

### Decision

所有需要 LLM 的 Skill 设计为两阶段：
1. 本地提取/处理（Python 脚本）
2. 将中间结果交给 Kimi 进行总结/分析

### Consequences

- ✅ 无需 API Key 即可使用大部分功能
- ✅ 本地脚本负责确定性操作，Kimi 负责自然语言理解与生成
- ⚠️ 用户需要手动将提取内容复制到对话
- ⚠️ 端到端自动化程度降低

### Alternatives Considered

- 申请并配置 API Key：用户当前不打算申请，未来如需可无缝切换（脚本保留 LLM 后端支持）。

---

## [ADR-20260628-001] Claude Code Skills 采用多文件结构

**Date**: 2026-06-28
**Status**: accepted
**Area**: tooling

### Context

早期 Skill 都是单文件 `SKILL.md`，内容冗长，模型难以按需读取。Anthropic 内部方法论建议将 Skill 组织为文件夹工程。

### Decision

所有本地 Skill 遵循统一结构：
- `SKILL.md`：入口与触发条件
- `reference.md`：详细用法
- `gotchas.md`：陷阱与失败模式
- `config.json`：配置
- `scripts/`：可执行脚本

### Consequences

- ✅ 模型按需读取，减少上下文开销
- ✅ 触发词和陷阱区更清晰
- ✅ 便于迭代和维护
- ⚠️ 文件数量增加，需要统一的目录约定

### Alternatives Considered

- 保持单文件：简单但难以扩展，已被 Anthropic 方法论否定。

---

## 模板

```markdown
## [ADR-YYYYMMDD-XXX] 标题

**Date**: YYYY-MM-DD
**Status**: proposed | accepted | deprecated | superseded
**Area**: frontend | backend | infra | tests | docs | config

### Context
[决策背景]

### Decision
[做了什么决定]

### Consequences
- ✅ 正面影响
- ⚠️ 负面影响或风险

### Alternatives Considered
[考虑过哪些替代方案]
```
