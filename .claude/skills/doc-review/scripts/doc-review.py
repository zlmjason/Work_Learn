#!/usr/bin/env python3
"""
doc-review.py — Markdown 笔记规范检查脚本

用法:
    python doc-review.py <文件.md>
    python doc-review.py <目录>
    python doc-review.py <路径> --json
    python doc-review.py <路径> --only-issues
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any


# 项目约定配置（可被 config.json 覆盖）
DEFAULT_CONFIG = {
    "requiredSections": ["核心问题", "结论", "关键机制"],
    "allTemplateSections": [
        "核心问题", "结论", "背景", "关键机制", "应用场景",
        "关联笔记", "待补充问题", "标签", "Agent 整理记录"
    ],
    "technicalTerms": [
        "Cortex-M7", "Cortex-R52", "AURIX", "TriCore",
        "SPI", "QSPI", "I2C", "CAN", "CAN-FD", "LIN", "UART", "Ethernet", "FlexRay",
        "ADC", "DAC", "GPIO", "PWM", "GPT", "ICU", "WDG",
        "DMA", "MPU", "SCU", "RAM", "Flash", "Cache",
        "AUTOSAR", "FreeRTOS", "ISO 26262", "E2E",
        "DEM", "DET", "UDS", "DTC", "OBD",
        "OS", "EcuM", "BswM", "SchM"
    ],
    "filenamePrefixes": [
        "HW_", "AUTOSAR_", "FreeRTOS_", "Safety_", "Tools_",
        "AURIX_TC3xx_", "ARM_M7_", "Core_Comparison_"
    ],
    "todoMarkers": ["TODO", "FIXME", "待验证"],
}


def load_config() -> dict[str, Any]:
    """加载同目录 config.json 并合并默认值。"""
    config_path = Path(__file__).parent.parent / "config.json"
    cfg = dict(DEFAULT_CONFIG)
    if config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                user_cfg = json.load(f)
                cfg.update(user_cfg)
        except Exception:
            pass
    return cfg


class ReviewResult:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.checks: dict[str, tuple[str, list[str]]] = {}

    def add(self, category: str, status: str, messages: list[str] | None = None):
        self.checks[category] = (status, messages or [])

    def has_issues(self) -> bool:
        return any(status in ("warn", "fail") for status, _ in self.checks.values())

    def to_dict(self) -> dict[str, Any]:
        return {
            "file": self.file_path,
            "checks": {
                cat: {"status": status, "messages": msgs}
                for cat, (status, msgs) in self.checks.items()
            },
        }


def read_file(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception as exc:
        return f""


def check_filename(file_path: Path, cfg: dict[str, Any]) -> tuple[str, list[str]]:
    name = file_path.name
    msgs = []
    status = "pass"

    if " " in name:
        msgs.append(f"文件名包含空格: {name}")
        status = "fail"

    # 索引/说明类特殊文件豁免前缀检查
    if name not in ("INDEX.md", "README.md"):
        # 检查是否有合法前缀
        has_prefix = any(name.startswith(prefix) for prefix in cfg.get("filenamePrefixes", []))
        if not has_prefix and not file_path.parent.name.startswith(("00_", "90_", "99_")):
            msgs.append(f"文件名缺少项目约定前缀: {name}")
            if status == "pass":
                status = "warn"

    # 检查缩写是否大写：查找常见小写缩写
    lower_terms = [t for t in cfg.get("technicalTerms", []) if len(t) >= 2 and t.lower() in name.lower() and t not in name]
    if lower_terms:
        # 仅作 warn，因为可能有误报
        msgs.append(f"文件名中可能存在未大写的缩写: {lower_terms[:3]}")
        if status == "pass":
            status = "warn"

    if not msgs:
        msgs.append("文件名符合规范")
    return status, msgs


def check_heading_structure(content: str) -> tuple[str, list[str]]:
    lines = content.splitlines()
    h1_count = sum(1 for line in lines if re.match(r"^#\s+", line))
    has_h1 = h1_count >= 1

    msgs = []
    status = "pass"

    if not has_h1:
        msgs.append("缺少 H1 文档标题")
        status = "fail"
    elif h1_count > 1:
        msgs.append(f"存在 {h1_count} 个 H1 标题，建议只有 1 个")
        status = "warn"

    # 检查层级跳跃：## 后直接 ####
    prev_level = 0
    jumps = []
    for line in lines:
        m = re.match(r"^(#{1,6})\s+", line)
        if m:
            level = len(m.group(1))
            if prev_level > 0 and level > prev_level + 1:
                jumps.append(level)
            prev_level = level
    if jumps:
        msgs.append(f"发现标题层级跳跃: {jumps[:3]}")
        if status == "pass":
            status = "warn"

    if not msgs:
        msgs.append("标题结构正常")
    return status, msgs


def check_required_sections(content: str, cfg: dict[str, Any], enforce: bool = True) -> tuple[str, list[str]]:
    required = cfg.get("requiredSections", [])
    all_sections = cfg.get("allTemplateSections", [])

    missing_required = [s for s in required if f"## {s}" not in content]
    present_all = [s for s in all_sections if f"## {s}" in content]

    msgs = []
    status = "pass"

    if missing_required:
        if enforce:
            msgs.append(f"缺少必要章节: {missing_required}")
            status = "fail"
        else:
            # 非 MCU 笔记层（如 91_Tools 系列笔记）允许自定义模板，降级为提醒
            msgs.append(f"缺少必要章节（非 MCU 笔记层，降级提醒）: {missing_required}")
            status = "warn"

    missing_optional = [s for s in all_sections if s not in present_all]
    if missing_optional and status == "pass":
        msgs.append(f"缺少推荐章节: {missing_optional}")
        status = "warn"

    if not msgs:
        msgs.append(f"包含 {len(present_all)}/{len(all_sections)} 个推荐章节")
    return status, msgs


def check_code_blocks(content: str, skill_doc: bool = False) -> tuple[str, list[str]]:
    # 逐行扫描围栏：只统计"开围栏"行，闭合行 ``` 不计入
    # （旧实现用 findall 匹配所有围栏行，会把每个闭合行误计为未标注代码块）
    unnamed = 0
    in_block = False
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("```"):
            if in_block:
                in_block = False
            else:
                in_block = True
                if not stripped[3:].strip():
                    unnamed += 1

    msgs = []
    status = "pass"

    if unnamed > 0:
        if skill_doc:
            msgs.append(f"发现 {unnamed} 个未标注语言的代码块（Skill 文档中的 Markdown 模板可忽略）")
            status = "warn"
        else:
            msgs.append(f"发现 {unnamed} 个未标注语言的代码块")
            status = "warn" if unnamed <= 2 else "fail"
    else:
        msgs.append("所有代码块均已标注语言")

    return status, msgs


def check_technical_terms(content: str, cfg: dict[str, Any]) -> tuple[str, list[str]]:
    """抽样检查技术术语是否被翻译成中文。"""
    terms = cfg.get("technicalTerms", [])
    # 简单启发：如果术语前面出现明显的中文翻译提示，则 warn
    # 这里只做保守检查：术语被写成 "串行外设接口" 替代 SPI 较难精确判断，
    # 因此仅标记常见中文字符串。
    suspicious = []
    chinese_translations = {
        "串行外设接口": "SPI", "控制器局域网": "CAN", "通用输入输出": "GPIO",
        "模数转换": "ADC", "数模转换": "DAC", "看门狗": "WDG",
        "脉冲宽度调制": "PWM", "直接存储器访问": "DMA", "内存保护单元": "MPU"
    }
    for cn, en in chinese_translations.items():
        if cn in content:
            suspicious.append(f"{cn} -> 建议保留英文 {en}")

    status = "pass"
    if suspicious:
        status = "warn" if len(suspicious) <= 2 else "fail"

    if not suspicious:
        return "pass", ["未发现明显术语中文化"]
    return status, suspicious


def check_directory_placement(file_path: Path, cfg: dict[str, Any]) -> tuple[str, list[str]]:
    name = file_path.name
    path_str = str(file_path).replace("\\", "/")

    # 归档/临时/附件目录跳过严格检查
    if any(p in path_str for p in ["00_Inbox_临时收集", "90_Archive_归档", "99_Attachments_附件"]):
        return "pass", ["位于特殊目录，跳过路径匹配检查"]

    status = "pass"
    msgs = []

    # 简单映射规则
    if name.startswith("HW_Periph_Comm_") and "01_Communication" not in path_str:
        msgs.append("HW_Periph_Comm_ 文件应位于 Peripherals/01_Communication 下")
        status = "warn"
    elif name.startswith("AUTOSAR_Comm_") and "01_Communication" not in path_str:
        msgs.append("AUTOSAR_Comm_ 文件应位于 AUTOSAR/01_Communication 下")
        status = "warn"
    elif name.startswith("HW_Sys_") and "03_System" not in path_str:
        msgs.append("HW_Sys_ 文件应位于 Hardware/03_System 下")
        status = "warn"
    elif name.startswith("AUTOSAR_Sys_") and "07_System" not in path_str:
        msgs.append("AUTOSAR_Sys_ 文件应位于 AUTOSAR/07_System 下")
        status = "warn"
    elif name.startswith("FreeRTOS_") and "02_FreeRTOS" not in path_str:
        msgs.append("FreeRTOS_ 文件应位于 Middleware/02_FreeRTOS 下")
        status = "warn"
    elif name.startswith("Safety_") and "04_Safety_功能安全" not in path_str:
        msgs.append("Safety_ 文件应位于 04_Safety_功能安全 下")
        status = "warn"
    elif name.startswith("Tools_") and "05_Tools_工具链" not in path_str:
        msgs.append("Tools_ 文件应位于 05_Tools_工具链 下")
        status = "warn"

    if not msgs:
        msgs.append("目录放置与文件名前缀一致")
    return status, msgs


def check_todo_fixme(content: str, cfg: dict[str, Any]) -> tuple[str, list[str]]:
    markers = cfg.get("todoMarkers", ["TODO", "FIXME", "待验证"])
    found = []
    for marker in markers:
        if marker in content:
            found.append(marker)

    if not found:
        return "pass", ["未发现 TODO/FIXME/待验证 标记"]

    status = "warn" if len(found) <= 3 else "fail"
    return status, [f"发现未处理标记: {found}"]


def check_wiki_links(content: str) -> tuple[str, list[str]]:
    opens = content.count("[[")
    closes = content.count("]]")

    if opens == 0 and closes == 0:
        return "pass", ["无双链"]

    if opens == closes:
        return "pass", [f"双链格式正确 ({opens} 对)"]

    status = "warn"
    msgs = [f"双链数量不匹配: [[={opens}, ]]={closes}"]
    return status, msgs


def is_skill_doc(file_path: Path) -> bool:
    """判断是否为 Claude Code Skill 文档，遵循与知识笔记不同的规范。"""
    path_str = str(file_path).replace("\\", "/")
    name = file_path.name
    return "/.claude/skills/" in path_str or name in ("SKILL.md", "reference.md", "gotchas.md", "config.json")


def review_file(file_path: Path, cfg: dict[str, Any]) -> ReviewResult:
    result = ReviewResult(str(file_path))
    content = read_file(file_path)

    if not content:
        result.add("read", "fail", ["无法读取文件或文件为空"])
        return result

    skill_doc = is_skill_doc(file_path)

    # 必要章节检查的强制范围：仅 MCU 笔记层目录（config.json strictTemplateDirs）
    path_norm = str(file_path).replace("\\", "/")
    strict_dirs = cfg.get("strictTemplateDirs", [])
    enforce_required = any(f"/{d}/" in path_norm for d in strict_dirs) if strict_dirs else True

    # 通用检查（所有 Markdown 文件）
    checks = [
        ("标题结构", check_heading_structure(content)),
        ("代码块语言", check_code_blocks(content, skill_doc)),
        ("技术术语", check_technical_terms(content, cfg)),
        ("TODO/FIXME", check_todo_fixme(content, cfg)),
        ("双链格式", check_wiki_links(content)),
    ]

    # 知识笔记专属检查（不适用于 Skill 文档）
    if not skill_doc:
        checks = [
            ("文件名", check_filename(file_path, cfg)),
            ("标题结构", check_heading_structure(content)),
            ("必要章节", check_required_sections(content, cfg, enforce_required)),
            ("代码块语言", check_code_blocks(content, skill_doc)),
            ("技术术语", check_technical_terms(content, cfg)),
            ("目录放置", check_directory_placement(file_path, cfg)),
            ("TODO/FIXME", check_todo_fixme(content, cfg)),
            ("双链格式", check_wiki_links(content)),
        ]
    else:
        checks.insert(0, ("文件类型", ("pass", ["Skill 文档，跳过知识笔记专属检查"])))

    for category, (status, msgs) in checks:
        result.add(category, status, msgs)

    return result


def collect_md_files(path: Path) -> list[Path]:
    if path.is_file():
        return [path] if path.suffix.lower() == ".md" else []
    files = []
    for p in path.rglob("*.md"):
        # 跳过 .claude 内部和归档目录的过度检查
        if ".claude" in str(p) or ".obsidian" in str(p):
            continue
        files.append(p)
    return sorted(files)


def print_report(results: list[ReviewResult], only_issues: bool):
    for r in results:
        if only_issues and not r.has_issues():
            continue
        print(f"\n文件: {r.file_path}")
        for category, (status, msgs) in r.checks.items():
            icon = {"pass": "✅", "warn": "⚠️", "fail": "❌"}.get(status, "?")
            print(f"  {icon} {category:12s} {status}")
            for msg in msgs:
                print(f"      {msg}")


def main():
    parser = argparse.ArgumentParser(description="Review Markdown notes against project conventions")
    parser.add_argument("path", help="Markdown file or directory to review")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    parser.add_argument("--only-issues", action="store_true", help="Only show files with issues")
    args = parser.parse_args()

    target = Path(args.path)
    if not target.exists():
        print(f"[错误] 路径不存在: {target}", file=sys.stderr)
        sys.exit(1)

    cfg = load_config()
    files = collect_md_files(target)

    if not files:
        print("[信息] 未找到 Markdown 文件")
        sys.exit(0)

    results = [review_file(f, cfg) for f in files]

    if args.json:
        output = [r.to_dict() for r in results]
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        print_report(results, args.only_issues)
        total = len(results)
        issue_count = sum(1 for r in results if r.has_issues())
        print(f"\n总计: {total} 个文件, {issue_count} 个有 issue")


if __name__ == "__main__":
    main()
