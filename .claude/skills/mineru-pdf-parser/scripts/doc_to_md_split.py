#!/usr/bin/env python3
"""大 PDF（超 MinerU 200 页上限）切块转换脚本 —— doc_to_md.py 的补充

MinerU 云端 API 单文件上限 200 页（ERR-20260809-001）。本脚本自动完成：
    切块 -> 逐块精准模式解析（token）-> 按序合并 full.md -> 清理中间产物

用法:
    py -3 doc_to_md_split.py <pdf路径> [--outdir 目录] [--max-pages 195]
    py -3 doc_to_md_split.py <pdf路径> --check          # 只打印切块计划，不调 API
    py -3 doc_to_md_split.py <pdf路径> --merge-only     # 只合并已存在的 full_partNN.md
    py -3 doc_to_md_split.py <pdf路径> --keep-parts     # 保留 _parts/ 与 full_partNN.md

行为:
    1. 页数 <= max-pages: 直接解析 -> <outdir>/full.md（+ images/）
    2. 页数 >  max-pages: 切块到 <outdir>/_parts/part_NN.pdf，逐块解析
       -> <outdir>/full_partNN.md（图片哈希命名，共用 <outdir>/images/）
       -> 全部成功后按序合并为 full.md，删除中间产物
    3. 断点续跑: 已存在且非空的 full_partNN.md 会被跳过
    4. 失败处理: 打印失败清单并保留中间产物，非零退出，可重跑

依赖: pypdf, mineru-open-sdk; 环境变量 MINERU_API_TOKEN（或 MINERU_TOKEN）
"""

import argparse
import os
import re
import sys
import time
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def _read_token() -> str:
    """读取 token：环境变量优先，Windows 上回退读注册表（setx 后无需重启终端）"""
    token = os.environ.get("MINERU_API_TOKEN", "").strip() or os.environ.get("MINERU_TOKEN", "").strip()
    if token:
        return token
    if os.name == "nt":
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as key:
                token = str(winreg.QueryValueEx(key, "MINERU_API_TOKEN")[0]).strip()
        except OSError:
            token = ""
    return token


def is_auth_error(exc: Exception) -> bool:
    return "401" in str(exc) or "Unauthorized" in str(exc)


def auth_hint() -> None:
    log("提示: Token 缺失或已过期。登录 https://mineru.net/apiManage/token 生成新 token 后执行:")
    log('      setx MINERU_API_TOKEN "<新token>"  （本脚本会自动从注册表读取，无需重启终端）')


def get_client():
    token = _read_token()
    if not token:
        log("错误: 未设置 MINERU_API_TOKEN / MINERU_TOKEN，精准模式无法使用")
        auth_hint()
        sys.exit(2)
    from mineru import MinerU
    return MinerU(token)


def page_count(pdf_path: Path) -> int:
    from pypdf import PdfReader
    return len(PdfReader(str(pdf_path)).pages)


def split_pdf(pdf_path: Path, parts_dir: Path, max_pages: int) -> list[Path]:
    """按 max_pages 切块，返回 part 文件路径列表（已存在的 part 不重复切）"""
    from pypdf import PdfReader, PdfWriter
    reader = PdfReader(str(pdf_path))
    total = len(reader.pages)
    parts_dir.mkdir(parents=True, exist_ok=True)
    parts: list[Path] = []
    for start in range(0, total, max_pages):
        end = min(start + max_pages, total)
        part_path = parts_dir / f"part_{len(parts) + 1:02d}.pdf"
        parts.append(part_path)
        if part_path.exists():
            log(f"  切块已存在，跳过: {part_path.name} (页 {start + 1}-{end})")
            continue
        writer = PdfWriter()
        for i in range(start, end):
            writer.add_page(reader.pages[i])
        with open(part_path, "wb") as f:
            writer.write(f)
        log(f"  切块 {part_path.name}: 页 {start + 1}-{end} ({end - start} 页)")
    return parts


def convert_parts(client, parts: list[Path], outdir: Path, timeout: int) -> dict[int, str]:
    """逐块提交并轮询，返回 {part序号: 状态}。已成功的跳过（断点续跑）。"""
    status: dict[int, str] = {}
    pending: list[tuple[int, Path, str, float]] = []  # (序号, 路径, batch_id, 提交时刻)

    for idx, part in enumerate(parts, start=1):
        part_md = outdir / f"full_part{idx:02d}.md"
        if part_md.exists() and part_md.stat().st_size > 0:
            log(f"  [{idx}/{len(parts)}] {part.name}: 已有 {part_md.name}，跳过")
            status[idx] = "skipped"
            continue
        # 提交（网络异常重试 2 次；401 直接中止，重试无意义）
        for attempt in range(3):
            try:
                batch_id = client.submit(str(part))
                pending.append((idx, part, batch_id, time.monotonic()))
                log(f"  [{idx}/{len(parts)}] {part.name}: 已提交 (batch {batch_id[:8]}...)")
                break
            except Exception as e:
                if is_auth_error(e):
                    log(f"错误: 提交被拒（401 Unauthorized）")
                    auth_hint()
                    sys.exit(2)
                if attempt == 2:
                    log(f"  [{idx}/{len(parts)}] {part.name}: 提交失败 - {e}")
                    status[idx] = "failed"
                else:
                    log(f"  [{idx}/{len(parts)}] {part.name}: 提交异常，重试 ({attempt + 1}/2): {e}")
                    time.sleep(10)

    # 轮询所有已提交任务
    deadline = time.monotonic() + timeout
    while pending:
        time.sleep(15)
        still: list[tuple[int, Path, str, float]] = []
        for idx, part, batch_id, submitted in pending:
            part_md = outdir / f"full_part{idx:02d}.md"
            try:
                results = client.get_batch(batch_id)
            except Exception as e:
                if is_auth_error(e):
                    log(f"错误: 查询被拒（401 Unauthorized）")
                    auth_hint()
                    sys.exit(2)
                if time.monotonic() > deadline:
                    status[idx] = "timeout"
                    continue
                log(f"  [{idx}/{len(parts)}] {part.name}: 查询异常，稍后重试: {e}")
                still.append((idx, part, batch_id, submitted))
                continue

            r = results[0] if results else None
            if r is None or r.state not in ("done", "failed"):
                if time.monotonic() > deadline:
                    log(f"  [{idx}/{len(parts)}] {part.name}: 超时（> {timeout}s）")
                    status[idx] = "timeout"
                    continue
                prog = ""
                if r is not None and getattr(r, "progress", None):
                    prog = f" {r.progress} "
                still.append((idx, part, batch_id, submitted))
                continue

            if r.state == "failed":
                log(f"  [{idx}/{len(parts)}] {part.name}: 解析失败 - {r.error} (code {r.err_code})")
                status[idx] = "failed"
                continue

            r.save_markdown(str(part_md), with_images=True)
            n_img = len(r.images)
            log(f"  [{idx}/{len(parts)}] {part.name}: 完成 -> {part_md.name} "
                f"({len(r.markdown or '')} 字符, {n_img} 图, 耗时 {int(time.monotonic() - submitted)}s)")
            status[idx] = "done"

        pending = still

    return status


def merge_parts(outdir: Path, n_parts: int, keep_parts: bool) -> int:
    """按序合并 full_partNN.md -> full.md，返回总行数"""
    chunks = []
    for idx in range(1, n_parts + 1):
        part_md = outdir / f"full_part{idx:02d}.md"
        text = part_md.read_text(encoding="utf-8")
        chunks.append(text.rstrip("\n"))
    merged = "\n\n".join(chunks) + "\n"
    full_md = outdir / "full.md"
    full_md.write_text(merged, encoding="utf-8")
    if not keep_parts:
        for idx in range(1, n_parts + 1):
            (outdir / f"full_part{idx:02d}.md").unlink(missing_ok=True)
        parts_dir = outdir / "_parts"
        if parts_dir.exists():
            for f in parts_dir.iterdir():
                f.unlink()
            parts_dir.rmdir()
    return merged.count("\n")


def main() -> None:
    ap = argparse.ArgumentParser(description="大 PDF 切块 + MinerU 转换 + 合并 full.md")
    ap.add_argument("pdf", help="PDF 文件路径")
    ap.add_argument("--outdir", default=None, help="输出目录（默认与 PDF 同目录）")
    ap.add_argument("--max-pages", type=int, default=195, help="每块最大页数（默认 195，API 上限 200）")
    ap.add_argument("--timeout", type=int, default=7200, help="总轮询超时秒数（默认 7200）")
    ap.add_argument("--check", action="store_true", help="只打印计划，不调用 API")
    ap.add_argument("--merge-only", action="store_true", help="只合并已存在的 full_partNN.md")
    ap.add_argument("--keep-parts", action="store_true", help="保留中间产物")
    args = ap.parse_args()

    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        log(f"错误: 文件不存在: {pdf_path}")
        sys.exit(1)
    outdir = Path(args.outdir) if args.outdir else pdf_path.parent
    outdir.mkdir(parents=True, exist_ok=True)

    total = page_count(pdf_path)
    n_parts = (total + args.max_pages - 1) // args.max_pages
    log(f"文件: {pdf_path.name}")
    log(f"页数: {total}，切块: {n_parts} 块（每块 ≤ {args.max_pages} 页）")

    if args.check:
        log("--check 模式，不调用 API。结束。")
        return

    if args.merge_only:
        lines = merge_parts(outdir, n_parts, args.keep_parts)
        log(f"合并完成: {outdir / 'full.md'}（{lines} 行）")
        return

    client = get_client()

    if n_parts == 1:
        log("单块文件，直接解析 ...")
        try:
            result = client.extract(str(pdf_path), timeout=args.timeout)
        except Exception as e:
            if is_auth_error(e):
                log("错误: 请求被拒（401 Unauthorized）")
                auth_hint()
                sys.exit(2)
            log(f"解析异常: {e}")
            sys.exit(1)
        if result.state != "done":
            log(f"解析失败: {result.error} (code {result.err_code})")
            sys.exit(1)
        full_md = outdir / "full.md"
        result.save_markdown(str(full_md), with_images=True)
        log(f"完成: {full_md}（{len(result.markdown or '')} 字符, {len(result.images)} 图）")
        return

    parts_dir = outdir / "_parts"
    parts = split_pdf(pdf_path, parts_dir, args.max_pages)
    status = convert_parts(client, parts, outdir, args.timeout)

    failed = sorted(i for i, s in status.items() if s not in ("done", "skipped"))
    if failed:
        log(f"以下块未成功: {failed}（中间产物已保留，可重跑本命令续传）")
        sys.exit(3)

    lines = merge_parts(outdir, n_parts, args.keep_parts)
    log(f"合并完成: {outdir / 'full.md'}（{lines} 行, {n_parts} 块）")


if __name__ == "__main__":
    main()
