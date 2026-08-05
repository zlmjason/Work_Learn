#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
context-check.py — 上下文 token 占用估算与阈值提醒

配置来源：.claude/skills/context-compress/config.json
（当前脚本仍以内置默认值为权威源，config.json 用于文档化和未来统一读取。）

用法示例：
  # 估算单个文件
  python context-check.py path/to/file.md

  # 估算多个文件并在超过阈值时报警
  python context-check.py --warn-at-percent 75 file1.md file2.c

  # 扫描工作区常见文件
  python context-check.py --scan-workspace --warn-at-percent 75

  # 从 stdin 读取文本
  echo "some long text" | python context-check.py
"""

import argparse
import json
import os
import sys
from pathlib import Path


DEFAULT_CONTEXT_LIMIT = 200_000  # Claude 3.5 Sonnet / Claude 4 系列约 200K
DEFAULT_WARN_PERCENT = 75

# 工作区中常见会被读入上下文的文件扩展名
WORKSPACE_EXTENSIONS = {
    ".md", ".txt", ".c", ".h", ".cpp", ".hpp",
    ".py", ".js", ".ts", ".json", ".yaml", ".yml",
    ".xml", ".toml", ".ini", ".cfg", ".s", ".S",
    ".rs", ".go", ".java", ".kt", ".swift",
}

# 默认跳过的目录
SKIP_DIRS = {
    ".git", ".svn", ".hg", "node_modules", "__pycache__",
    ".venv", "venv", "dist", "build", ".claude", ".obsidian",
    "target", ".idea", ".vscode", "out", "bin", "obj",
}


def try_tiktoken_encode(text: str):
    """尝试使用 tiktoken 的 cl100k_base 编码器估算 token 数。"""
    try:
        import tiktoken
        enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(text))
    except Exception:
        return None


def heuristic_token_count(text: str) -> int:
    """
    启发式 token 估算：
    - 连续 ASCII 字符按 4 字符/token 估算
    - CJK 字符按 1.5 字符/token 估算
    """
    ascii_chars = 0
    cjk_chars = 0
    for ch in text:
        code = ord(ch)
        if 0x4E00 <= code <= 0x9FFF or 0x3400 <= code <= 0x4DBF or 0x3040 <= code <= 0x30FF or 0xAC00 <= code <= 0xD7AF:
            cjk_chars += 1
        else:
            ascii_chars += 1
    return max(1, ascii_chars // 4 + int(cjk_chars / 1.5))


def estimate_tokens(text: str) -> tuple[int, str]:
    """返回 (token_count, method_used)。"""
    tiktoken_count = try_tiktoken_encode(text)
    if tiktoken_count is not None:
        return tiktoken_count, "tiktoken"
    return heuristic_token_count(text), "heuristic"


def read_text(path: Path) -> str:
    """安全读取文本文件，失败返回空字符串。"""
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def scan_workspace(root: Path, extensions: set[str], skip_dirs: set[str]) -> list[Path]:
    """扫描工作区中可能进入上下文的文件。"""
    files = []
    for dirpath, dirnames, filenames in os.walk(root):
        # 过滤目录
        dirnames[:] = [d for d in dirnames if d not in skip_dirs]
        for name in filenames:
            ext = Path(name).suffix.lower()
            if ext in extensions:
                files.append(Path(dirpath) / name)
    return files


def format_size(tokens: int) -> str:
    if tokens >= 1_000_000:
        return f"{tokens / 1_000_000:.2f}M"
    if tokens >= 1_000:
        return f"{tokens / 1_000:.1f}K"
    return str(tokens)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Estimate token usage and warn when approaching context limit."
    )
    parser.add_argument(
        "inputs", nargs="*",
        help="Files or directories to estimate. If empty, reads from stdin."
    )
    parser.add_argument(
        "--warn-at-percent", type=int, default=DEFAULT_WARN_PERCENT,
        help=f"Warn when token usage exceeds this percentage of context limit (default: {DEFAULT_WARN_PERCENT})."
    )
    parser.add_argument(
        "--context-limit", type=int, default=DEFAULT_CONTEXT_LIMIT,
        help=f"Context window size in tokens (default: {DEFAULT_CONTEXT_LIMIT})."
    )
    parser.add_argument(
        "--scan-workspace", action="store_true",
        help="Scan the current working directory for common source/document files."
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Output results as JSON."
    )
    parser.add_argument(
        "--top-n", type=int, default=20,
        help="When scanning workspace, show top N largest files (default: 20)."
    )
    parser.add_argument(
        "--exit-zero", action="store_true",
        help="Always exit with code 0, even when warning threshold is exceeded."
    )

    args = parser.parse_args()
    warn_threshold = int(args.context_limit * (args.warn_at_percent / 100.0))

    # 收集要估算的内容
    file_records = []  # (path, tokens, method)

    if args.scan_workspace:
        root = Path.cwd()
        files = scan_workspace(root, WORKSPACE_EXTENSIONS, SKIP_DIRS)
        for f in files:
            text = read_text(f)
            if not text:
                continue
            tokens, method = estimate_tokens(text)
            file_records.append((str(f.relative_to(root)), tokens, method))
    elif args.inputs:
        for inp in args.inputs:
            p = Path(inp)
            if p.is_dir():
                files = scan_workspace(p, WORKSPACE_EXTENSIONS, SKIP_DIRS)
                for f in files:
                    text = read_text(f)
                    if not text:
                        continue
                    tokens, method = estimate_tokens(text)
                    rel = str(f.relative_to(p))
                    file_records.append((rel, tokens, method))
            elif p.is_file():
                text = read_text(p)
                tokens, method = estimate_tokens(text)
                file_records.append((str(p), tokens, method))
            else:
                print(f"Warning: {inp} not found", file=sys.stderr)
    else:
        # 从 stdin 读取
        text = sys.stdin.read()
        tokens, method = estimate_tokens(text)
        file_records.append(("(stdin)", tokens, method))

    total_tokens = sum(r[1] for r in file_records)
    percent = (total_tokens / args.context_limit) * 100
    largest = sorted(file_records, key=lambda x: x[1], reverse=True)[:args.top_n]

    result = {
        "total_tokens": total_tokens,
        "context_limit": args.context_limit,
        "used_percent": round(percent, 2),
        "warn_threshold_tokens": warn_threshold,
        "warn_at_percent": args.warn_at_percent,
        "method": "mixed",
        "largest_files": [
            {"path": r[0], "tokens": r[1], "method": r[2]} for r in largest
        ],
        "warn": total_tokens >= warn_threshold,
    }

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"Estimated tokens: {format_size(total_tokens)} / {format_size(args.context_limit)} ({percent:.1f}%)")
        print(f"Warning threshold: {format_size(warn_threshold)} ({args.warn_at_percent}%)")
        if file_records and file_records[0][0] != "(stdin)":
            print(f"Top {len(largest)} largest files:")
            for path, tokens, method in largest:
                print(f"  {format_size(tokens):>6} [{method[:3]}] {path}")
        if total_tokens >= warn_threshold:
            print(
                f"\n⚠️  WARNING: Context usage is at {percent:.1f}% of the limit. "
                f"Consider running `/context-compress` to summarize the session.",
                file=sys.stderr,
            )

    return 1 if (total_tokens >= warn_threshold and not args.exit_zero) else 0


if __name__ == "__main__":
    sys.exit(main())
