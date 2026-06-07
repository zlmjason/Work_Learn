#!/usr/bin/env python3
"""文档转 Markdown / HTML / Word 封装脚本 —— 基于 MinerU 云端 API

支持格式: PDF, Word(.doc/.docx), PPT(.ppt/.pptx), Excel(.xls/.xlsx), 图片(.png/.jpg/.jpeg/.tiff/.bmp)

用法:
    python doc_to_md.py <文件路径>                          # 输出 md（默认）
    python doc_to_md.py <文件路径> -f html                  # 输出带样式的 HTML（1.5倍行距+两端对齐）
    python doc_to_md.py <文件路径> -f docx                  # 输出 Word 文档
    python doc_to_md.py --batch <目录> -f html              # 批量转换
"""

import argparse
import os
import re
import sys
import zipfile

SUPPORTED_EXTS = (
    ".pdf", ".doc", ".docx", ".ppt", ".pptx",
    ".xls", ".xlsx", ".png", ".jpg", ".jpeg", ".tiff", ".bmp"
)


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
    try:
        import mineru
        return True
    except ImportError:
        return False


def extract_docx_images(docx_path: str, img_dir: str) -> int:
    """从 docx 中提取图片，返回提取数量"""
    os.makedirs(img_dir, exist_ok=True)
    try:
        from docx import Document
        doc = Document(docx_path)
        count = 0
        for rel in doc.part.rels.values():
            if 'image' in rel.reltype:
                image = rel.target_part
                ext = image.content_type.split('/')[-1]
                if ext == 'jpeg':
                    ext = 'jpg'
                count += 1
                img_path = os.path.join(img_dir, f'image_{count:02d}.{ext}')
                with open(img_path, 'wb') as f:
                    f.write(image.blob)
        # 兜底：zipfile 提取
        if count == 0:
            with zipfile.ZipFile(docx_path) as z:
                for name in z.namelist():
                    if name.startswith('word/media/'):
                        data = z.read(name)
                        ext = os.path.splitext(name)[1].lstrip('.')
                        if ext == 'jpeg':
                            ext = 'jpg'
                        count += 1
                        img_path = os.path.join(img_dir, f'image_{count:02d}.{ext}')
                        with open(img_path, 'wb') as f:
                            f.write(data)
        return count
    except Exception as e:
        print(f"  [警告] 图片提取失败: {e}")
        return 0


def extract_pdf_images(pdf_path: str, img_dir: str) -> int:
    """从 pdf 中提取图片，返回提取数量"""
    os.makedirs(img_dir, exist_ok=True)
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(pdf_path)
        count = 0
        for page_num in range(len(doc)):
            page = doc[page_num]
            images = page.get_images(full=True)
            for img in images:
                xref = img[0]
                pix = fitz.Pixmap(doc, xref)
                if pix.n > 4:
                    pix = fitz.Pixmap(fitz.csRGB, pix)
                count += 1
                img_path = os.path.join(img_dir, f'image_{count:02d}.png')
                pix.save(img_path)
                pix = None
        return count
    except ImportError:
        print("  [警告] PyMuPDF 未安装，跳过 PDF 图片提取。安装: python3 -m pip install PyMuPDF")
        return 0
    except Exception as e:
        print(f"  [警告] PDF 图片提取失败: {e}")
        return 0


def update_image_refs(md_path: str, img_dir: str):
    """更新 Markdown 中的图片引用路径"""
    if not os.path.exists(md_path):
        return
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 匹配 MinerU 生成的哈希图片路径
    old_images = re.findall(r'!\[\]\(images/[a-f0-9]+\.\w+\)', content)
    if not old_images:
        return

    extracted = sorted([
        f for f in os.listdir(img_dir)
        if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp'))
    ])

    for i, old in enumerate(old_images):
        if i < len(extracted):
            new = f'![](images/{extracted[i]})'
            content = content.replace(old, new, 1)

    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(content)


def md_to_html(md_path: str, html_path: str) -> bool:
    """将 Markdown 转换为带样式的 HTML（1.5倍行距 + 两端对齐）"""
    try:
        import markdown as md_lib
    except ImportError:
        print("  [错误] 生成 HTML 需要 markdown 库")
        print("  请运行: python3 -m pip install markdown")
        return False

    with open(md_path, 'r', encoding='utf-8') as f:
        md_content = f.read()

    html_body = md_lib.markdown(
        md_content,
        extensions=['tables', 'fenced_code', 'toc']
    )

    title = os.path.splitext(os.path.basename(md_path))[0]

    html_template = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        @media print {{
            body {{ padding: 0; max-width: 100%; }}
        }}
        body {{
            font-family: "Segoe UI", "Microsoft YaHei", "PingFang SC", "Noto Sans CJK SC", sans-serif;
            font-size: 11pt;
            line-height: 1.5;
            text-align: justify;
            max-width: 210mm;
            margin: 0 auto;
            padding: 25mm;
            color: #333;
            background: #fff;
        }}
        h1, h2, h3, h4, h5, h6 {{
            line-height: 1.3;
            text-align: left;
            color: #222;
            margin-top: 1.5em;
            margin-bottom: 0.6em;
            font-weight: 600;
        }}
        h1 {{ font-size: 1.8em; border-bottom: 2px solid #eee; padding-bottom: 0.3em; }}
        h2 {{ font-size: 1.5em; border-bottom: 1px solid #eee; padding-bottom: 0.2em; }}
        h3 {{ font-size: 1.25em; }}
        p {{
            text-align: justify;
            line-height: 1.5;
            margin: 0.8em 0;
            text-indent: 2em;
        }}
        p:has(img), p:has(table) {{ text-indent: 0; }}
        img {{
            max-width: 100%;
            height: auto;
            display: block;
            margin: 1em auto;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 1em 0;
            font-size: 10pt;
            line-height: 1.5;
        }}
        th, td {{
            border: 1px solid #ccc;
            padding: 6px 8px;
            text-align: left;
            vertical-align: top;
        }}
        th {{
            background-color: #f5f5f5;
            font-weight: 600;
        }}
        tr:nth-child(even) {{ background-color: #fafafa; }}
        pre {{
            background: #f8f8f8;
            padding: 1em;
            overflow-x: auto;
            line-height: 1.4;
            border-radius: 4px;
            border: 1px solid #e0e0e0;
            text-indent: 0;
        }}
        code {{
            font-family: "Consolas", "Monaco", "Courier New", monospace;
            background: #f0f0f0;
            padding: 2px 5px;
            border-radius: 3px;
            font-size: 0.9em;
        }}
        pre code {{
            background: none;
            padding: 0;
            font-size: 0.85em;
        }}
        blockquote {{
            border-left: 4px solid #ddd;
            margin: 1em 0;
            padding: 0.5em 1em;
            color: #555;
            background: #fafafa;
            text-indent: 0;
        }}
        ul, ol {{
            margin: 0.8em 0;
            padding-left: 2em;
            line-height: 1.5;
        }}
        li {{ margin: 0.3em 0; }}
        a {{ color: #0366d6; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
        hr {{ border: none; border-top: 1px solid #e0e0e0; margin: 1.5em 0; }}
    </style>
</head>
<body>
{html_body}
</body>
</html>'''

    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_template)

    return True


def md_to_docx(md_path: str, docx_path: str) -> bool:
    """将 Markdown 转换为 Word 文档（1.5倍行距 + 两端对齐）"""
    try:
        from docx import Document
        from docx.shared import Pt, Inches, RGBColor
        from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
        from docx.oxml.ns import qn
    except ImportError:
        print("  [错误] 生成 Word 需要 python-docx 库")
        print("  请运行: python3 -m pip install python-docx")
        return False

    doc = Document()

    # 默认样式
    style = doc.styles['Normal']
    style.font.name = 'Times New Roman'
    style.font.size = Pt(11)
    style._element.rPr.rFonts.set(qn('w:eastAsia'), 'Microsoft YaHei')
    style.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
    style.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    style.paragraph_format.space_after = Pt(6)
    style.paragraph_format.first_line_indent = Inches(0.3)

    # 标题样式
    for i, (font_size, space_before) in enumerate([(18, 12), (16, 10), (14, 8), (12, 6)], 1):
        h_style = doc.styles[f'Heading {i}']
        h_style.font.name = 'Times New Roman'
        h_style.font.size = Pt(font_size)
        h_style.font.bold = True
        h_style.font.color.rgb = RGBColor(0x22, 0x22, 0x22)
        h_style._element.rPr.rFonts.set(qn('w:eastAsia'), 'Microsoft YaHei')
        h_style.paragraph_format.space_before = Pt(space_before)
        h_style.paragraph_format.space_after = Pt(6)
        h_style.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
        h_style.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT

    with open(md_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    in_code_block = False
    code_lines = []
    current_table = []
    in_table = False

    def flush_code():
        nonlocal in_code_block, code_lines
        if code_lines:
            p = doc.add_paragraph()
            p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
            p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.first_line_indent = Inches(0)
            run = p.add_run(''.join(code_lines).rstrip('\n'))
            run.font.name = 'Consolas'
            run._element.rPr.rFonts.set(qn('w:eastAsia'), 'Consolas')
            run.font.size = Pt(9.5)
            run.font.color.rgb = RGBColor(0x33, 0x33, 0x33)
            code_lines = []
        in_code_block = False

    def flush_table():
        nonlocal in_table, current_table
        if not current_table:
            in_table = False
            return
        rows = []
        for line in current_table:
            cells = [c.strip() for c in line.strip('|').split('|')]
            rows.append(cells)
        if len(rows) >= 2:
            max_cols = max(len(r) for r in rows)
            table = doc.add_table(rows=len(rows), cols=max_cols)
            table.style = 'Table Grid'
            for i, row_cells in enumerate(rows):
                for j in range(max_cols):
                    cell = table.rows[i].cells[j]
                    cell.text = row_cells[j] if j < len(row_cells) else ''
                    for paragraph in cell.paragraphs:
                        paragraph.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
                        paragraph.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
                        paragraph.paragraph_format.first_line_indent = Inches(0)
                        for run in paragraph.runs:
                            run.font.size = Pt(10)
                            if i == 0:
                                run.font.bold = True
        current_table = []
        in_table = False

    for line in lines:
        stripped = line.strip()

        if stripped.startswith('```'):
            if in_code_block:
                flush_code()
            else:
                flush_table()
                in_code_block = True
            continue

        if in_code_block:
            code_lines.append(line)
            continue

        if stripped.startswith('|') and stripped.endswith('|'):
            if not in_table:
                flush_table()
            in_table = True
            current_table.append(line)
            continue
        elif in_table:
            flush_table()

        if not stripped:
            continue

        # 标题
        heading_match = re.match(r'^(#{1,6})\s+(.+)$', stripped)
        if heading_match:
            level = len(heading_match.group(1))
            text = heading_match.group(2).strip()
            text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
            text = re.sub(r'\*(.+?)\*', r'\1', text)
            doc.add_heading(text, level=min(level, 4))
            continue

        # 引用
        if stripped.startswith('>'):
            text = stripped[1:].strip()
            p = doc.add_paragraph(text)
            p.paragraph_format.left_indent = Inches(0.2)
            p.paragraph_format.first_line_indent = Inches(0)
            for run in p.runs:
                run.font.color.rgb = RGBColor(0x66, 0x66, 0x66)
            continue

        # 无序列表
        list_match = re.match(r'^(\s*)[-*+]\s+(.+)$', line)
        if list_match:
            indent = len(list_match.group(1))
            text = list_match.group(2)
            p = doc.add_paragraph(text, style='List Bullet')
            p.paragraph_format.left_indent = Inches(0.25 + indent * 0.15)
            p.paragraph_format.first_line_indent = Inches(-0.25)
            continue

        # 有序列表
        ordered_match = re.match(r'^(\s*)\d+\.\s+(.+)$', line)
        if ordered_match:
            indent = len(ordered_match.group(1))
            text = ordered_match.group(2)
            p = doc.add_paragraph(text, style='List Number')
            p.paragraph_format.left_indent = Inches(0.25 + indent * 0.15)
            p.paragraph_format.first_line_indent = Inches(-0.25)
            continue

        # 普通段落
        p = doc.add_paragraph()
        parts = re.split(r'(!?\[.*?\]\(.*?\)|\*\*.*?\*\*|\*.*?\*)', line.strip())
        for part in parts:
            if not part:
                continue
            img_match = re.match(r'!\[(.*?)\]\((.*?)\)', part)
            if img_match:
                alt, src = img_match.groups()
                img_path = os.path.join(os.path.dirname(md_path), src)
                if os.path.exists(img_path):
                    try:
                        p.add_run().add_picture(img_path, width=Inches(5.5))
                    except Exception:
                        p.add_run(f'[图片: {alt}]')
                else:
                    p.add_run(f'[图片: {alt} ({src})]')
                continue
            link_match = re.match(r'\[(.*?)\]\((.*?)\)', part)
            if link_match:
                text, url = link_match.groups()
                run = p.add_run(text)
                run.font.color.rgb = RGBColor(0x03, 0x66, 0xd6)
                run.font.underline = True
                continue
            bold_match = re.match(r'\*\*(.+?)\*\*', part)
            if bold_match:
                run = p.add_run(bold_match.group(1))
                run.bold = True
                continue
            italic_match = re.match(r'\*(.+?)\*', part)
            if italic_match:
                run = p.add_run(italic_match.group(1))
                run.italic = True
                continue
            p.add_run(part)

    if in_code_block:
        flush_code()
    if in_table:
        flush_table()

    doc.save(docx_path)
    return True


def post_process_format(md_path: str, output_format: str) -> str:
    """根据目标格式对 md 进行后处理"""
    if output_format == 'md':
        return md_path

    base = os.path.splitext(md_path)[0]

    if output_format == 'html':
        html_path = base + '.html'
        if md_to_html(md_path, html_path):
            print(f"[完成] HTML: {html_path}")
            return html_path
        return md_path

    if output_format == 'docx':
        docx_path = base + '.docx'
        if md_to_docx(md_path, docx_path):
            print(f"[完成] Word: {docx_path}")
            return docx_path
        return md_path

    return md_path


def convert_single(file_path: str, output_path: str = None, output_format: str = 'md'):
    if not os.path.exists(file_path):
        print(f"[错误] 文件不存在: {file_path}")
        sys.exit(1)

    ext = os.path.splitext(file_path)[1].lower()
    if ext not in SUPPORTED_EXTS:
        print(f"[错误] 不支持的格式: {ext}")
        print(f"支持格式: {', '.join(SUPPORTED_EXTS)}")
        sys.exit(1)

    client = get_mineru_client()
    print(f"正在解析: {file_path} ...")

    try:
        if getattr(client, '_has_token', False):
            result = client.extract(file_path)
        else:
            result = client.flash_extract(file_path)
    except Exception as e:
        print(f"[错误] 解析失败: {e}")
        sys.exit(1)

    if result.state != 'done':
        print(f"[错误] 解析失败: {result.error} (code: {result.err_code})")
        sys.exit(1)

    base_dir = os.path.dirname(file_path) or '.'
    base_name = os.path.splitext(os.path.basename(file_path))[0]

    # 先保存 md 作为中间产物
    md_path = os.path.join(base_dir, f"{base_name}.md")
    result.save_markdown(md_path)
    print(f"[完成] Markdown: {md_path}")

    # 提取图片
    img_dir = os.path.join(base_dir, 'images')
    img_count = 0
    if ext == '.docx':
        img_count = extract_docx_images(file_path, img_dir)
    elif ext == '.pdf':
        img_count = extract_pdf_images(file_path, img_dir)

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


def convert_batch(input_dir: str, output_dir: str = None, output_format: str = 'md'):
    if not os.path.isdir(input_dir):
        print(f"[错误] 目录不存在: {input_dir}")
        sys.exit(1)

    client = get_mineru_client()

    if not output_dir:
        output_dir = os.path.join(input_dir, "markdowns")
    os.makedirs(output_dir, exist_ok=True)

    files = [f for f in os.listdir(input_dir)
             if os.path.splitext(f)[1].lower() in SUPPORTED_EXTS]

    if not files:
        print("[警告] 目录下没有支持的文件")
        sys.exit(0)

    success = failed = 0
    for fname in files:
        fpath = os.path.join(input_dir, fname)
        ext = os.path.splitext(fname)[1].lower()
        base_name = os.path.splitext(fname)[0]
        out_md = os.path.join(output_dir, base_name + ".md")
        img_dir = os.path.join(output_dir, 'images')

        try:
            if getattr(client, '_has_token', False):
                result = client.extract(fpath)
            else:
                result = client.flash_extract(fpath)
            if result.state != 'done':
                print(f"❌ {fname}: {result.error} (code: {result.err_code})")
                failed += 1
                continue
            result.save_markdown(out_md)

            img_count = 0
            if ext == '.docx':
                img_count = extract_docx_images(fpath, img_dir)
            elif ext == '.pdf':
                img_count = extract_pdf_images(fpath, img_dir)

            if img_count > 0:
                update_image_refs(out_md, img_dir)

            if output_format != 'md':
                post_process_format(out_md, output_format)

            print(f"✅ {fname}")
            success += 1
        except Exception as e:
            print(f"❌ {fname}: {e}")
            failed += 1

    print(f"\n完成: 成功 {success} 个, 失败 {failed} 个, 总计 {len(files)} 个")
    print(f"输出目录: {output_dir}")


def main():
    parser = argparse.ArgumentParser(description="文档转 Markdown / HTML / Word (MinerU)")
    parser.add_argument("input", help="文件路径或目录")
    parser.add_argument("-o", "--output", help="输出路径（单文件模式）")
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
