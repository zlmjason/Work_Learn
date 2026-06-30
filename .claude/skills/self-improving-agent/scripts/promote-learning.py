#!/usr/bin/env python3
"""
promote-learning.py — 将 .learnings/ 中的条目晋升到项目文档

用法:
    python .claude/skills/self-improving-agent/scripts/promote-learning.py <ID> <目标文件> [--dry-run]

示例:
    python .claude/skills/self-improving-agent/scripts/promote-learning.py LRN-20260511-005 .claude/CLAUDE.md
    python .claude/skills/self-improving-agent/scripts/promote-learning.py LRN-20260511-005 .claude/CLAUDE.md --dry-run
"""

import argparse
import re
import sys
from pathlib import Path

LEARNINGS_DIR = Path(".learnings")
TARGET_FILES = {
    "CLAUDE.md": Path(".claude/CLAUDE.md"),
    "AGENTS.md": Path("AGENTS.md"),
    "copilot": Path(".github/copilot-instructions.md"),
}


def find_entry(entry_id: str) -> tuple[Path, str] | None:
    """在所有 .learnings/*.md 中查找条目。"""
    for md_file in sorted(LEARNINGS_DIR.glob("*.md")):
        text = md_file.read_text(encoding="utf-8", errors="ignore")
        pattern = re.compile(rf"^##\s+\[{re.escape(entry_id)}\].*?\n---", re.MULTILINE | re.DOTALL)
        m = pattern.search(text)
        if m:
            return md_file, m.group(0)
    return None


def update_entry_status(entry_id: str, source_file: Path, target: str, dry_run: bool):
    """将原条目的 Status 改为 promoted，并添加 Promoted 字段。"""
    text = source_file.read_text(encoding="utf-8")
    old_status = re.search(rf"(##\s+\[{re.escape(entry_id)}\].*?\*\*Status\*\*:\s*)(\w+)", text, re.DOTALL)
    if not old_status:
        print(f"[警告] 未在 {source_file} 中找到条目 {entry_id} 的 Status 字段", file=sys.stderr)
        return

    old_status_str = old_status.group(2)
    if old_status_str == "promoted":
        print(f"[信息] 条目 {entry_id} 已经是 promoted 状态")
        return

    new_text = re.sub(
        rf"(##\s+\[{re.escape(entry_id)}\].*?\*\*Status\*\*:\s*){old_status_str}",
        rf"\1promoted",
        text,
        count=1,
        flags=re.DOTALL,
    )

    # 在 Metadata 后添加 Promoted 字段
    promoted_note = f"\n- **Promoted**: {target}"
    # 找到该条目的 Metadata 块末尾（以 --- 结束）
    entry_pattern = re.compile(rf"(##\s+\[{{re.escape(entry_id)}}\].*?)(\n---\n)", re.DOTALL)
    # 更精确：在 Metadata 最后一行后插入
    new_text = re.sub(
        rf"(##\s+\[{re.escape(entry_id)}\].*?)(\n---\n)",
        rf"\1{promoted_note}\2",
        new_text,
        count=1,
        flags=re.DOTALL,
    )

    if dry_run:
        print(f"[dry-run] 将更新 {source_file} 中 {entry_id} 的状态为 promoted")
    else:
        source_file.write_text(new_text, encoding="utf-8")
        print(f"已更新 {source_file} 中 {entry_id} 的状态为 promoted，目标: {target}")


def main():
    parser = argparse.ArgumentParser(description="Promote a learning entry to project documentation")
    parser.add_argument("entry_id", help="Learning entry ID, e.g., LRN-20260511-005")
    parser.add_argument("target", help="Target file path or alias (CLAUDE.md, AGENTS.md, copilot)")
    parser.add_argument("--dry-run", action="store_true", help="Print what would happen without making changes")
    args = parser.parse_args()

    # 解析目标文件
    target_path = TARGET_FILES.get(args.target, Path(args.target))
    if isinstance(target_path, str):
        target_path = Path(target_path)

    if not target_path.exists():
        print(f"[错误] 目标文件不存在: {target_path}", file=sys.stderr)
        sys.exit(1)

    found = find_entry(args.entry_id)
    if not found:
        print(f"[错误] 未在 .learnings/ 中找到条目: {args.entry_id}", file=sys.stderr)
        sys.exit(1)

    source_file, entry_text = found
    print(f"找到条目 {args.entry_id} 于 {source_file}")
    print("---")
    print(entry_text[:500] + ("..." if len(entry_text) > 500 else ""))
    print("---")
    print(f"目标文件: {target_path}")

    if args.dry_run:
        print("\n[dry-run] 不会写入任何文件")
        print("建议操作：")
        print(f"1. 将上述条目内容精炼后追加到 {target_path}")
        print(f"2. 运行本脚本不带 --dry-run 以更新原条目状态为 promoted")
        return

    print("\n请将要晋升的内容复制到目标文件，然后按回车继续，或 Ctrl+C 取消。")
    try:
        input()
    except KeyboardInterrupt:
        print("\n已取消")
        sys.exit(0)

    update_entry_status(args.entry_id, source_file, str(target_path), args.dry_run)
    print(f"\n请手动确保 {target_path} 中已添加晋升后的规则/事实。")


if __name__ == "__main__":
    main()
