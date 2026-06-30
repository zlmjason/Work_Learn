# Learnings Index

本文件由 `update-index.py` 自动生成，汇总 `.learnings/` 目录下的学习记录、错误、功能请求、决策和模式。

## 使用说明

1. 每条记录使用统一格式：`## [ID-YYYYMMDD-XXX] category/title`。
2. 状态包括：`pending`（待处理）、`in_progress`（进行中）、`resolved`（已解决）、`wont_fix`（不修复）、`promoted`（已晋升）。
3. 高价值、复发性的学习应晋升到 `.claude/CLAUDE.md` 或提取为 `.claude/skills/` 下的 Skill。
4. 运行 `python .claude/skills/self-improving-agent/scripts/update-index.py` 可重新生成本文件。

## 统计概览

- **总条目数**: 11
- **按状态**: accepted: 3, candidate: 3, pending: 2, proposed: 1, resolved: 5, wont_fix: 1

## 各文件汇总

| 文件 | 条目数 | 状态分布 |
|------|--------|----------|
| [LEARNINGS.md](./LEARNINGS.md) | 3 | pending: 2, resolved: 3 |
| [ERRORS.md](./ERRORS.md) | 2 | resolved: 1, wont_fix: 1 |
| [FEATURE_REQUESTS.md](./FEATURE_REQUESTS.md) | 0 | — |
| [DECISIONS.md](./DECISIONS.md) | 3 | accepted: 3, proposed: 1 |
| [PATTERNS.md](./PATTERNS.md) | 3 | candidate: 3, resolved: 1 |

## 按文件索引

### LEARNINGS.md

- [LRN-20260511-005] best_practice
- [LRN-20260511-002] knowledge_gap
- [LRN-20260511-003] insight

### ERRORS.md

- [ERR-20260511-001] pip_install_summarize
- [ERR-20260511-003] winget_install_tesseract_poppler

### DECISIONS.md

- [ADR-20260511-001] 不安装 WSL2
- [ADR-20260511-002] Kimi-Only 工作流
- [ADR-20260628-001] Claude Code Skills 采用多文件结构

### PATTERNS.md

- [PAT-install-cross-platform] 跨平台安装脚本需要 Windows 适配
- [PAT-workflow-llm-fallback] 无 API Key 时 LLM 工作流降级
- [PAT-skill-folder-structure] Skill 单文件膨胀

---

_Generated at: 2026-06-30T20:54:15.863614+08:00_
