#!/usr/bin/env python3
"""
doc_review_on_md_edit.py — PostToolUse hook：Edit/Write 修改 .md 后自动运行 doc-review

设计原则：
- 仅检查仓库内的 .md 笔记；排除附件/Inbox/归档/配置/学习日志等非笔记目录
- 无 issue 时完全静默（exit 0，无输出）
- 有 issue 时通过 hookSpecificOutput.additionalContext 注入检查结果
- 检查器自身故障不阻断工作流（静默退出，不产生噪音）
- 直接 import doc-review.py 复用检查逻辑（单一事实源，避免 subprocess 编码问题）
"""

import importlib.util
import json
import sys
from pathlib import Path

# 不写 .pyc 字节码缓存（import doc-review.py 时避免在 skills 目录生成 __pycache__）
sys.dont_write_bytecode = True

# 非笔记目录（相对路径中包含这些片段即跳过）
EXCLUDED_MARKERS = (
    "/.claude/",
    "/.learnings/",
    "/.obsidian/",
    "/node_modules/",
    "/00_Inbox_临时收集/",
    "/90_Archive_归档/",
    "/99_Attachments_附件/",
)


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0

    tool_input = data.get("tool_input") or {}
    file_path = tool_input.get("file_path") or ""
    if not file_path.lower().endswith(".md"):
        return 0

    repo_root = Path(__file__).resolve().parents[2]
    target = Path(file_path).resolve()

    # 仅检查仓库内文件；排除仓库根目录散落文档（CLAUDE.md、AGENTS.md 等）
    try:
        rel = target.relative_to(repo_root)
    except ValueError:
        return 0
    if len(rel.parts) < 2:
        return 0

    norm = "/" + str(rel).replace("\\", "/")
    if any(marker in norm for marker in EXCLUDED_MARKERS):
        return 0

    script = repo_root / ".claude" / "skills" / "doc-review" / "scripts" / "doc-review.py"
    if not script.exists():
        return 0

    try:
        spec = importlib.util.spec_from_file_location("doc_review", script)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        cfg = mod.load_config()
        result = mod.review_file(target, cfg)
    except Exception:
        return 0  # 检查器故障不阻断工作流

    issues = []
    for category, (status, messages) in result.checks.items():
        if status in ("warn", "fail"):
            for msg in messages:
                issues.append(f"[{status}] {category}: {msg}")

    if not issues:
        return 0

    context = (
        "doc-review 自动检查（PostToolUse hook）发现规范问题。"
        "请在收尾前修复；属合理例外的（如系列笔记模板差异），向用户简要说明保留原因：\n"
        + "\n".join(f"- {line}" for line in issues)
    )
    # ensure_ascii=True（默认）：避免 Windows 控制台编码问题
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": context,
        }
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
