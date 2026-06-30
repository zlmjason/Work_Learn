#!/usr/bin/env python3
"""
update-index.py — 重新生成 .learnings/INDEX.md

用法:
    python .claude/skills/self-improving-agent/scripts/update-index.py
"""

import json
import re
from datetime import datetime, timezone
from pathlib import Path

LEARNINGS_DIR = Path(".learnings")
SOURCE_FILES = ["LEARNINGS.md", "ERRORS.md", "FEATURE_REQUESTS.md", "DECISIONS.md", "PATTERNS.md"]


def parse_entries(path: Path):
    """解析 markdown 文件中的条目，返回列表。跳过模板占位条目。"""
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8", errors="ignore")
    # 匹配 ## [ID-...] 或 ## [LRN-...] 等标题
    entries = []
    for m in re.finditer(r"^##\s+\[([^\]]+)\]\s+(.*)$", text, re.MULTILINE):
        entry_id = m.group(1).strip()
        title = m.group(2).strip()
        # 跳过模板占位
        if "YYYYMMDD-XXX" in entry_id or title in ("标题", "模式名称", "Title", "Pattern Name"):
            continue
        if "KEY" in entry_id and "模式名称" in title:
            continue
        entries.append({"id": entry_id, "title": title})
    return entries


def count_by_status(path: Path) -> dict[str, int]:
    """统计条目的 Status 字段。"""
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8", errors="ignore")
    statuses = {}
    for m in re.finditer(r"\*\*Status\*\*:\s*(\w+)", text):
        status = m.group(1)
        statuses[status] = statuses.get(status, 0) + 1
    return statuses


def main():
    lines = [
        "# Learnings Index",
        "",
        "本文件由 `update-index.py` 自动生成，汇总 `.learnings/` 目录下的学习记录、错误、功能请求、决策和模式。",
        "",
        "## 使用说明",
        "",
        "1. 每条记录使用统一格式：`## [ID-YYYYMMDD-XXX] category/title`。",
        "2. 状态包括：`pending`（待处理）、`in_progress`（进行中）、`resolved`（已解决）、`wont_fix`（不修复）、`promoted`（已晋升）。",
        "3. 高价值、复发性的学习应晋升到 `.claude/CLAUDE.md` 或提取为 `.claude/skills/` 下的 Skill。",
        "4. 运行 `python .claude/skills/self-improving-agent/scripts/update-index.py` 可重新生成本文件。",
        "",
        "## 统计概览",
        "",
    ]

    total_entries = 0
    all_statuses: dict[str, int] = {}
    file_summaries = []

    for fname in SOURCE_FILES:
        path = LEARNINGS_DIR / fname
        entries = parse_entries(path)
        statuses = count_by_status(path)
        total_entries += len(entries)

        for status, count in statuses.items():
            all_statuses[status] = all_statuses.get(status, 0) + count

        file_summaries.append({
            "file": fname,
            "count": len(entries),
            "statuses": statuses,
            "entries": entries,
        })

    lines.append(f"- **总条目数**: {total_entries}")
    lines.append(f"- **按状态**: " + ", ".join(f"{s}: {c}" for s, c in sorted(all_statuses.items())))
    lines.append("")

    lines.append("## 各文件汇总")
    lines.append("")
    lines.append("| 文件 | 条目数 | 状态分布 |")
    lines.append("|------|--------|----------|")
    for summary in file_summaries:
        status_str = ", ".join(f"{s}: {c}" for s, c in sorted(summary["statuses"].items())) or "—"
        lines.append(f"| [{summary['file']}](./{summary['file']}) | {summary['count']} | {status_str} |")
    lines.append("")

    lines.append("## 按文件索引")
    lines.append("")

    for summary in file_summaries:
        if not summary["entries"]:
            continue
        lines.append(f"### {summary['file']}")
        lines.append("")
        for entry in summary["entries"]:
            lines.append(f"- [{entry['id']}] {entry['title']}")
        lines.append("")

    # 元数据
    now = datetime.now(timezone.utc).astimezone().isoformat()
    lines.append("---")
    lines.append("")
    lines.append(f"_Generated at: {now}_")
    lines.append("")

    output_path = LEARNINGS_DIR / "INDEX.md"
    output_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"已生成: {output_path}")


if __name__ == "__main__":
    main()
