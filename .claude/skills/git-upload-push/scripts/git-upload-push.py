#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
git-upload-push.py — Git 上传推送辅助脚本

用法：
  python git-upload-push.py status              # 查看当前仓库状态
  python git-upload-push.py suggest             # 生成 commit message 建议
  python git-upload-push.py push "msg"          # 执行 add/commit/push（需 message）
  python git-upload-push.py push "msg" --yes    # 跳过确认（谨慎使用）
"""

import argparse
import os
import subprocess
import sys
from datetime import datetime, timezone


def run(cmd, cwd=None, check=True):
    """执行 shell 命令并返回输出。"""
    result = subprocess.run(
        cmd,
        cwd=cwd,
        shell=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
    )
    if check and result.returncode != 0:
        print(f"Error running: {cmd}", file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        sys.exit(result.returncode)
    return result.stdout.strip()


def get_default_branch(repo_root):
    """获取远程默认分支名。"""
    try:
        sym_ref = run("git symbolic-ref refs/remotes/origin/HEAD", cwd=repo_root)
        return sym_ref.split("/")[-1] if sym_ref else "main"
    except SystemExit:
        return "main"


def get_current_branch(repo_root):
    """获取当前分支名。"""
    return run("git rev-parse --abbrev-ref HEAD", cwd=repo_root)


def has_changes(repo_root):
    """检查是否有未提交或未跟踪的变更。"""
    status = run("git status --porcelain", cwd=repo_root)
    return bool(status.strip())


def get_status_summary(repo_root):
    """获取 git status 摘要。"""
    return run("git status --short", cwd=repo_root)


def suggest_commit_message(repo_root):
    """基于变更文件生成 commit message 建议。"""
    status_lines = get_status_summary(repo_root).splitlines()
    if not status_lines:
        return None

    # 简单规则：根据变更文件类型推断前缀
    has_code = any(l.strip().endswith((".c", ".h", ".cpp", ".hpp", ".s", ".S")) for l in status_lines)
    has_doc = any(l.strip().endswith((".md", ".txt", ".pdf")) for l in status_lines)
    has_config = any(l.strip().endswith((".json", ".xml", ".cfg", ".ld")) for l in status_lines)

    parts = []
    if has_code:
        parts.append("update driver code")
    if has_doc:
        parts.append("update documentation")
    if has_config:
        parts.append("update configuration")
    if not parts:
        parts.append("update files")

    msg = "; ".join(parts)
    # 首字母大写
    msg = msg[0].upper() + msg[1:]
    return msg


def get_repo_root():
    """获取当前 git 仓库根目录。"""
    return run("git rev-parse --show-toplevel")


def do_push(repo_root, message, skip_confirm=False):
    """执行 add → commit → push。"""
    if not has_changes(repo_root):
        print("No changes to commit.")
        return 0

    current = get_current_branch(repo_root)
    default = get_default_branch(repo_root)

    if current == default:
        print(f"WARNING: Currently on default branch '{default}'.", file=sys.stderr)
        print("It is recommended to create a feature branch before pushing.", file=sys.stderr)
        if not skip_confirm:
            return 1

    # 自动添加 Co-Authored-By
    if "Co-Authored-By:" not in message:
        message += "\n\nCo-Authored-By: Claude <noreply@anthropic.com>"

    if not skip_confirm:
        print("\n=== Git Status ===")
        print(get_status_summary(repo_root))
        print(f"\nBranch: {current}")
        print(f"Commit message:\n{message}\n")
        confirm = input("Proceed with add/commit/push? [y/N] ")
        if confirm.lower() not in ("y", "yes"):
            print("Aborted.")
            return 1

    # 执行 git 操作
    print(run("git add -A", cwd=repo_root))
    print(run(f'git commit -m "{message}"', cwd=repo_root))

    # 检查上游分支
    upstream = run(f"git rev-parse --abbrev-ref --symbolic-full-name {current}@{{u}}", cwd=repo_root, check=False)
    if not upstream:
        print(run(f"git push -u origin {current}", cwd=repo_root))
    else:
        print(run("git push", cwd=repo_root))

    print("Push completed.")
    return 0


def main():
    parser = argparse.ArgumentParser(description="Git upload/push helper")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("status", help="Show repository status summary")
    subparsers.add_parser("suggest", help="Suggest a commit message")

    push_parser = subparsers.add_parser("push", help="Add, commit, and push")
    push_parser.add_argument("message", help="Commit message")
    push_parser.add_argument("--yes", action="store_true", help="Skip confirmation")

    args = parser.parse_args()
    repo_root = get_repo_root()

    if args.command == "status":
        current = get_current_branch(repo_root)
        default = get_default_branch(repo_root)
        print(f"Branch: {current} (default: {default})")
        print("\n=== Status ===")
        print(get_status_summary(repo_root) or "No changes.")
        return 0

    if args.command == "suggest":
        msg = suggest_commit_message(repo_root)
        if msg:
            print(msg)
        else:
            print("No changes to suggest a message for.")
        return 0

    if args.command == "push":
        return do_push(repo_root, args.message, skip_confirm=args.yes)


if __name__ == "__main__":
    sys.exit(main())
