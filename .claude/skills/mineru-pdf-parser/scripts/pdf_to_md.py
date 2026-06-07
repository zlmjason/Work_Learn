#!/usr/bin/env python3
"""PDF 转 Markdown / HTML / Word 封装脚本 —— 基于 MinerU 云端 API

用法:
    python pdf_to_md.py <pdf路径>              # 单文件转换，输出 md
    python pdf_to_md.py <pdf路径> -o <输出.md>  # 指定输出路径
    python pdf_to_md.py <pdf路径> -f html       # 输出带样式的 HTML（1.5倍行距+两端对齐）
    python pdf_to_md.py <pdf路径> -f docx       # 输出 Word 文档
    python pdf_to_md.py --batch <pdf目录>       # 批量转换
"""

import argparse
import os
import sys

# 导入 doc_to_md 中的后处理函数（同目录）
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from doc_to_md import md_to_html, md_to_docx, post_process_format, extract_pdf_images, update_image_refs


def get_mineru_client():
    """Create MinerU client with token from config if available."""
    import json
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.json")
    token = None
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                cfg = json.load(f)
                token = cfg.get("api_token", None)
        except Exception:
            pass
    from mineru import MinerU
    if token:
        client = MinerU(token)
        client._has_token = True
        return client
    client = MinerU()
    client._has_token = False
    return client


def check_mineru_installed():
    """检查 mineru-open-sdk 是否已安装"""
    try:
        import mineru
        return True
    except ImportError:
        return False


def convert_single(pdf_path: str, output_path: str = None, output_format: str = 'md'):
    """转换单个 PDF 文件"""
    if not os.path.exists(pdf_path):
        print(f"[错误] 文件不存在: {pdf_path}")
        sys.exit(1)

    client = get_mineru_client()
    print(f"正在解析: {pdf_path} ...")

    try:
        if getattr(client, '_has_token', False):
            result = client.extract(pdf_path)
        else:
            result = client.flash_extract(pdf_path)
    except Exception as e:
        print(f"[错误] 解析失败: {e}")
        sys.exit(1)

    if result.state != 'done':
        print(f"[错误] 解析失败: {result.error} (code: {result.err_code})")
        sys.exit(1)

    base_dir = os.path.dirname(pdf_path) or '.'
    base_name = os.path.splitext(os.path.basename(pdf_path))[0]

    # 先保存 md 作为中间产物
    md_path = os.path.join(base_dir, f"{base_name}.md")
    if output_path and output_format == 'md':
        md_path = output_path
    result.save_markdown(md_path)
    print(f"[完成] Markdown: {md_path}")

    # 提取图片
    img_dir = os.path.join(base_dir, 'images')
    img_count = extract_pdf_images(pdf_path, img_dir)
    if img_count > 0:
        print(f"[完成] 提取 {img_count} 张图片到: {img_dir}")
        update_image_refs(md_path, img_dir)
        print("[完成] 图片引用路径已更新")
    else:
        print("[信息] 未提取到图片（文档可能不含图片或提取失败）")

    # 格式后处理
    if output_format != 'md':
        final_path = post_process_format(md_path, output_format)
        return final_path

    return md_path


def convert_batch(pdf_dir: str, output_dir: str = None, output_format: str = 'md'):
    """批量转换目录下的所有 PDF"""
    if not os.path.isdir(pdf_dir):
        print(f"[错误] 目录不存在: {pdf_dir}")
        sys.exit(1)

    client = get_mineru_client()

    if not output_dir:
        output_dir = os.path.join(pdf_dir, "markdowns")
    os.makedirs(output_dir, exist_ok=True)

    pdf_files = [f for f in os.listdir(pdf_dir) if f.endswith(".pdf")]
    if not pdf_files:
        print("[警告] 目录下没有 PDF 文件")
        sys.exit(0)

    success = 0
    failed = 0
    for fname in pdf_files:
        pdf_path = os.path.join(pdf_dir, fname)
        base_name = os.path.splitext(fname)[0]
        out_md = os.path.join(output_dir, base_name + ".md")
        img_dir = os.path.join(output_dir, 'images')
        try:
            if getattr(client, '_has_token', False):
                result = client.extract(pdf_path)
            else:
                result = client.flash_extract(pdf_path)
            if result.state != 'done':
                print(f"❌ {fname}: {result.error} (code: {result.err_code})")
                failed += 1
                continue
            result.save_markdown(out_md)

            img_count = extract_pdf_images(pdf_path, img_dir)
            if img_count > 0:
                update_image_refs(out_md, img_dir)

            if output_format != 'md':
                post_process_format(out_md, output_format)

            print(f"✅ {fname}")
            success += 1
        except Exception as e:
            print(f"❌ {fname}: {e}")
            failed += 1

    print(f"\n完成: 成功 {success} 个, 失败 {failed} 个, 总计 {len(pdf_files)} 个")
    print(f"输出目录: {output_dir}")


def main():
    parser = argparse.ArgumentParser(description="PDF 转 Markdown / HTML / Word (MinerU)")
    parser.add_argument("input", help="PDF 文件路径或目录")
    parser.add_argument("-o", "--output", help="输出 Markdown 路径（单文件模式）")
    parser.add_argument("--batch", action="store_true", help="批量模式（input 为目录）")
    parser.add_argument("-f", "--format", choices=['md', 'html', 'docx'],
                        default='md',
                        help="输出格式: md=纯Markdown, html=带样式网页(1.5倍行距+两端对齐), docx=Word文档")
    args = parser.parse_args()

    if not check_mineru_installed():
        print("[错误] mineru-open-sdk 未安装")
        print("请运行: python3 -m pip install mineru-open-sdk")
        sys.exit(1)

    if args.batch:
        convert_batch(args.input, args.output, args.format)
    else:
        convert_single(args.input, args.output, args.format)


if __name__ == "__main__":
    main()
