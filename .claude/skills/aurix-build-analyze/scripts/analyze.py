#!/usr/bin/env python3
"""AURIX TC3xx (ADS/TASKING) build artifact analyzer.

Parses the TASKING linker map, the ELF file and the Intel HEX output, then
runs consistency / link-accuracy checks. Standard library only.

Usage:
    py -3 analyze.py [--project DIR] [--config Debug] [--json] [--strict]
"""

from __future__ import annotations

import argparse
import json
import re
import struct
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------

DEFAULT_CONFIG: dict[str, Any] = {
    "project": {
        "path": "C:/Users/11064/Desktop/TC397_Platform_Jason/ADS/FreeRTOS",
        "workspace": "C:/Users/11064/Desktop/TC397_Platform_Jason/ADS",
        "eclipse_project": "FreeRTOS",
        "build_config": "Debug",
    },
    "artifacts": {"elf": "FreeRTOS.elf", "map": "FreeRTOS.map", "hex": "FreeRTOS.hex"},
    "expected": {
        "device_macro": "__CPU__=tc39xb",
        "entry_symbol": "_START",
        "csa_size_bytes": 8192,
        "csa_cores": [0, 1, 2, 3, 4, 5],
        "required_symbols": [
            "_START",
            "core0_main",
            "vPortSyscallHandler",
            "vPortSystemContextHandler",
            "vPortSystemTickHandler",
            "vPortEnterCritical",
            "vPortExitCritical",
            "vTaskSwitchContext",
        ],
        "freertos_symbols": [
            "pxCurrentTCB",
            "vTaskSwitchContext",
            "vPortStartFirstTask",
            "vPortSyscallHandler",
            "vPortSystemTickHandler",
        ],
        "trap_reference": {"symbol": "vPortSyscallHandler", "referenced_by": "IfxCpu_Trap.o"},
        "heap_section": "ucHeap",
    },
    "thresholds": {"freshness_tolerance_sec": 120, "min_free_memory_bytes": 1024},
}

# Required symbols that are optional in some builds are filtered at runtime.
# vPortStartFirstTask is static inline in port.c and may not emit a symbol.
OPTIONAL_REQUIRED = {"vPortReclaimCSA", "vPortStartFirstTask"}


# --------------------------------------------------------------------------
# Result model
# --------------------------------------------------------------------------

@dataclass
class Check:
    group: str
    name: str
    status: str  # pass | warn | fail | info
    detail: str


@dataclass
class Report:
    checks: list[Check] = field(default_factory=list)
    data: dict[str, Any] = field(default_factory=dict)

    def add(self, group: str, name: str, status: str, detail: str = "") -> None:
        self.checks.append(Check(group, name, status, detail))

    def counts(self) -> dict[str, int]:
        out = {"pass": 0, "warn": 0, "fail": 0, "info": 0}
        for c in self.checks:
            out[c.status] = out.get(c.status, 0) + 1
        return out


# --------------------------------------------------------------------------
# Linker map parser
# --------------------------------------------------------------------------

BANNER_RE = re.compile(r"^\*{10,}")


def _strip_section_id(name: str) -> str:
    return re.sub(r"\s*\(\d+\)\s*$", "", name).strip()


def section_type(name: str) -> str:
    """Classify a section name into a human-meaningful type."""
    n = name
    if n.startswith("csa_tc"):
        return "CSA"
    if n.startswith("ustack_tc"):
        return "UStack"
    if n.startswith("istack_tc"):
        return "IStack"
    if "inttab" in n or n.startswith(".vector"):
        return "Vector"
    if "ucHeap" in n or n == "heap" or n.startswith("heap."):
        return "Heap"
    if n.startswith(".text"):
        return "Code"
    if n.startswith(".rodata") or n.startswith(".data.rel.ro"):
        return "RO Data"
    if n.startswith(".data") or n.startswith(".sdata") or n.startswith(".zdata"):
        return "Data"
    if n.startswith(".bss") or n.startswith(".sbss") or n.startswith(".zbss"):
        return "BSS"
    return "Other"


# Modules that belong to the RTOS kernel / are shared by all tasks.
SHARED_KERNEL_MODULES = {
    "tasks.o",
    "queue.o",
    "list.o",
    "timers.o",
    "port.o",
    "heap_1.o",
    "event_groups.o",
    "stream_buffer.o",
    "croutine.o",
}

CORE_PATTERNS = [
    re.compile(r"Ifx_Ssw_Tc(\d)"),
    re.compile(r"Cpu(\d)_Main"),
    re.compile(r"(?:ustack|istack|csa)_tc(\d)", re.I),
    re.compile(r"(?:ustack|istack|csa)(\d)", re.I),
    re.compile(r"__Core(\d)_start"),
]


def _core_of_section(section: dict[str, Any], module: str) -> int | None:
    """Infer the owning core for a placed section, or None if shared/unknown."""
    name = section.get("name", "")
    group = section.get("group", "")
    # Trap stubs are common infrastructure; the per-core part is the vector table.
    if "IfxCpu_Trap" in module or "IfxCpu_Trap" in name:
        return None
    # ROM copy images such as [.data.Cpu0_Main.g_cpuSyncEvent] live in flash
    # by design; they are the load image of a data section, not data placement.
    if name.startswith("["):
        return None
    for text in (module, name, group):
        for pattern in CORE_PATTERNS:
            m = pattern.search(text)
            if m:
                return int(m.group(1))
    return None


def analyze_core_affinity(map_data: dict[str, Any]) -> dict[str, Any]:
    """Check per-core placement and shared-data placement.

    Rules:
      * core N code  -> PFLSN or PSPRN
      * core N data  -> DSPRN or CPUN_DLMU
      * shared data  -> LMU (preferred); DSPR/DLMU acceptable for fast paths
                        or single-core designs, reported as info/warn.
      * fast code    -> PSPR (reported as info)
      * fast data    -> DSPR (reported as info)
    """
    module_by_section: dict[str, str] = {}
    for row in map_data.get("link_result", []):
        module_by_section.setdefault(row["section"], row["file"])

    cores: dict[int, dict[str, Any]] = {}
    for n in range(6):
        cores[n] = {
            "core": n,
            "code_ok": True,
            "data_ok": True,
            "code_chips": defaultdict(int),
            "data_chips": defaultdict(int),
            "violations": [],
        }

    violations: list[dict[str, Any]] = []
    shared_by_chip: dict[str, int] = defaultdict(int)
    shared_by_module: dict[str, int] = defaultdict(int)
    shared_lmu = 0
    pspr_code = 0
    pspr_sections: list[dict[str, Any]] = []
    dspr_data = 0
    dspr_sections: list[dict[str, Any]] = []

    for s in map_data.get("sections", []):
        name = s["name"]
        chip = s["chip"]
        size = s["size"]
        module = module_by_section.get(name, "")
        t = section_type(name)

        if t in ("Code", "Vector") and chip.startswith("mpe:psram"):
            pspr_code += size
            pspr_sections.append({"name": name, "chip": chip, "size": size, "module": module})
        if t in ("Data", "BSS", "Heap", "CSA", "UStack", "IStack") and chip.startswith("mpe:dsram"):
            dspr_data += size
            dspr_sections.append({"name": name, "chip": chip, "size": size, "module": module})

        core = _core_of_section(s, module)
        if core is not None and core in cores:
            if t in ("Code", "Vector", "RO Data"):
                cores[core]["code_chips"][chip] += size
                expected = {f"mpe:pfls{core}", f"mpe:psram{core}"}
                if chip not in expected:
                    cores[core]["code_ok"] = False
                    v = {
                        "core": core,
                        "kind": "code",
                        "section": name,
                        "module": module,
                        "chip": chip,
                        "expected": sorted(expected),
                        "size": size,
                    }
                    violations.append(v)
                    cores[core]["violations"].append(v)
            elif t in ("Data", "BSS", "Heap", "CSA", "UStack", "IStack"):
                cores[core]["data_chips"][chip] += size
                expected = {f"mpe:dsram{core}", f"mpe:cpu{core}_dlmu"}
                if chip not in expected:
                    cores[core]["data_ok"] = False
                    v = {
                        "core": core,
                        "kind": "data",
                        "section": name,
                        "module": module,
                        "chip": chip,
                        "expected": sorted(expected),
                        "size": size,
                    }
                    violations.append(v)
                    cores[core]["violations"].append(v)
            # Other types (e.g. ROM copy images) are not placement-checked.
        else:
            # Shared data heuristics: kernel modules / library data.
            if t in ("Data", "BSS", "Heap"):
                if chip == "mpe:lmuram":
                    shared_lmu += size
                elif chip.startswith("mpe:dsram") or chip.endswith("_dlmu"):
                    shared_by_chip[chip] += size
                    shared_by_module[module or "linker/LSL"] += size

    shared_total = sum(shared_by_chip.values())
    return {
        "cores": [cores[n] for n in sorted(cores)],
        "violations": violations,
        "shared": {
            "total": shared_total,
            "in_lmu": shared_lmu,
            "by_chip": dict(shared_by_chip),
            "by_module": dict(sorted(shared_by_module.items(), key=lambda x: -x[1])),
        },
        "scratchpad": {
            "pspr_code": pspr_code,
            "pspr_sections": pspr_sections,
            "dspr_data": dspr_data,
            "dspr_sections": dspr_sections,
        },
    }


def parse_map(path: Path) -> dict[str, Any]:
    """Parse the TASKING linker map into structured data."""
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()

    used: dict[str, dict[str, int]] = {}
    sections: list[dict[str, Any]] = []
    symbols: dict[str, int] = {}
    cross_refs: list[dict[str, str]] = []
    link_result: list[dict[str, Any]] = []
    invocation: dict[str, str] = {"tool": "", "path": "", "arguments": ""}

    # Find banner offsets so we can scope each section.
    banners: list[tuple[int, str]] = []
    for i, line in enumerate(lines):
        if BANNER_RE.match(line.strip()):
            banners.append((i, line.strip("* \t\r\n")))
    banners.append((len(lines), "END"))

    def scope(idx: int) -> tuple[int, int]:
        for (start, _name), (end, _next) in zip(banners, banners[1:]):
            if start == idx:
                return start, end
        return 0, len(lines)

    for start, name in banners[:-1]:
        end = next((s for s, _n in banners if s > start), len(lines))
        block = lines[start:end]

        if "Tool and Invocation" in name:
            for line in block:
                cells = [c.strip() for c in line.split("|")]
                if len(cells) >= 3:
                    key = cells[1]
                    if key == "tool":
                        invocation["tool"] = cells[2]
                    elif key == "path":
                        invocation["path"] = cells[2]
                    elif key == "arguments" or key.startswith("file:"):
                        # Arguments may span several lines; concatenate.
                        # The map splits the command line across an "arguments"
                        # row and one or more "file:<id>" continuation rows.
                        invocation["arguments"] += " " + " ".join(
                            c.strip() for c in cells[2:] if c.strip()
                        )

        elif "Used Resources" in name:
            for line in block:
                m = re.match(
                    r"^\|\s*(mpe:[A-Za-z0-9_]+)\s*\|\s*(0x[0-9a-fA-F]+)\s*\|"
                    r"\s*(0x[0-9a-fA-F]+)\s*\|\s*(0x[0-9a-fA-F]+)\s*\|"
                    r"\s*(0x[0-9a-fA-F]+)\s*\|\s*(0x[0-9a-fA-F]+)\s*\|",
                    line,
                )
                if m:
                    used[m.group(1)] = {
                        "code": int(m.group(2), 16),
                        "data": int(m.group(3), 16),
                        "reserved": int(m.group(4), 16),
                        "free": int(m.group(5), 16),
                        "total": int(m.group(6), 16),
                    }

        elif "Locate Result" in name:
            # The Locate Result banner contains several sub-tables:
            #   * Task entry addresses
            #   * Sections
            #   * Symbols (sorted on name)
            #   * Symbols (sorted on address)
            #   * Combined sections
            sub_blocks: list[tuple[str, list[str]]] = []
            for line in block:
                if line.startswith("* "):
                    sub_blocks.append((line[2:].strip(), []))
                elif sub_blocks:
                    sub_blocks[-1][1].append(line)

            row_re = re.compile(
                r"^\|\s*(mpe:[A-Za-z0-9_]+)\s*\|\s*([^|]*)\s*\|\s*([^|]+?)\s*\|"
                r"\s*(0x[0-9a-fA-F]+)\s*\|\s*(0x[0-9a-fA-F]+)\s*\|"
                r"\s*(0x[0-9a-fA-F]+)\s*\|\s*(0x[0-9a-fA-F]+)\s*\|"
            )
            sym_re = re.compile(
                r"^\|\s*([A-Za-z_][A-Za-z0-9_.$]*)\s*\|\s*(0x[0-9a-fA-F]+)\s*\|"
            )
            for sub_name, sub_lines in sub_blocks:
                if sub_name.startswith("Sections"):
                    for line in sub_lines:
                        m = row_re.match(line)
                        if not m:
                            continue
                        sec_name = _strip_section_id(m.group(3))
                        if not sec_name or sec_name.startswith("-"):
                            continue
                        sections.append(
                            {
                                "chip": m.group(1),
                                "group": m.group(2).strip(),
                                "name": sec_name,
                                "size": int(m.group(4), 16),
                                "space_addr": int(m.group(5), 16),
                                "chip_addr": int(m.group(6), 16),
                                "align": int(m.group(7), 16),
                            }
                        )
                elif sub_name.startswith("Symbols (sorted on name)"):
                    for line in sub_lines:
                        m = sym_re.match(line)
                        if m:
                            symbols[m.group(1)] = int(m.group(2), 16)

        elif "Link Result" in name:
            # Per-object contribution table:
            # | file.o | input section (id) | size | offset | output section | out size |
            link_re = re.compile(
                r"^\|\s*([^|]+?\.(?:o|obj))\s*\|\s*([^|]+?)\s*\|"
                r"\s*(0x[0-9a-fA-F]+)\s*\|"
            )
            for line in block:
                m = link_re.match(line)
                if not m:
                    continue
                link_result.append(
                    {
                        "file": m.group(1).strip(),
                        "section": _strip_section_id(m.group(2)),
                        "size": int(m.group(3), 16),
                    }
                )

        elif "Cross References" in name:
            ref_re = re.compile(
                r"^\|\s*([^|]+?\.o)\s*\|\s*([^|]+?)\s*\|\s*([A-Za-z_]\w*)\s*\|\s*([^|]*?)\s*\|"
            )
            for line in block:
                m = ref_re.match(line)
                if m:
                    cross_refs.append(
                        {
                            "file": m.group(1).strip(),
                            "section": m.group(2).strip(),
                            "symbol": m.group(3).strip(),
                            "referenced_in": m.group(4).strip(),
                        }
                    )

        elif "Symbols (sorted on name)" in name:
            sym_re = re.compile(
                r"^\|\s*([A-Za-z_][A-Za-z0-9_.$]*)\s*\|\s*(0x[0-9a-fA-F]+)\s*\|"
            )
            for line in block:
                m = sym_re.match(line)
                if m:
                    symbols[m.group(1)] = int(m.group(2), 16)

    return {
        "tool_invocation": invocation,
        "used_resources": used,
        "sections": sections,
        "symbols": symbols,
        "cross_refs": cross_refs,
        "link_result": link_result,
    }


# --------------------------------------------------------------------------
# Minimal ELF32 parser (little-endian; TriCore ELF is ELF32 LE)
# --------------------------------------------------------------------------

def parse_elf(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    if data[:4] != b"\x7fELF":
        raise ValueError("not an ELF file")
    ei_class = data[4]
    ei_data = data[5]
    if ei_class != 1:
        raise ValueError("only ELF32 is supported")
    if ei_data != 1:
        raise ValueError("only little-endian ELF is supported")

    (
        e_type,
        e_machine,
        e_version,
        e_entry,
        e_phoff,
        e_shoff,
        e_flags,
        e_ehsize,
        e_phentsize,
        e_phnum,
        e_shentsize,
        e_shnum,
        e_shstrndx,
    ) = struct.unpack_from("<HHIIIIIHHHHHH", data, 16)

    shdrs = []
    for i in range(e_shnum):
        off = e_shoff + i * e_shentsize
        if off + 40 > len(data):
            break
        shdrs.append(struct.unpack_from("<IIIIIIIIII", data, off))

    # Section header string table.
    shstr = b""
    if 0 <= e_shstrndx < len(shdrs):
        _, _, _, _, sh_offset, sh_size, _, _, _, _ = shdrs[e_shstrndx]
        shstr = data[sh_offset : sh_offset + sh_size]

    def sname(idx: int) -> str:
        if not shstr or idx >= len(shstr):
            return ""
        end = shstr.find(b"\x00", idx)
        return shstr[idx:end].decode("ascii", errors="replace")

    sections = []
    for sh in shdrs:
        name_off, sh_type, sh_flags, sh_addr, sh_offset, sh_size, sh_link, sh_info, sh_addralign, sh_entsize = sh
        sections.append(
            {
                "name": sname(name_off),
                "type": sh_type,
                "flags": sh_flags,
                "addr": sh_addr,
                "offset": sh_offset,
                "size": sh_size,
                "align": sh_addralign,
            }
        )

    return {
        "type": e_type,
        "machine": e_machine,
        "entry": e_entry,
        "phnum": e_phnum,
        "sections": sections,
        "size": len(data),
    }


# --------------------------------------------------------------------------
# Intel HEX parser
# --------------------------------------------------------------------------

def parse_hex(path: Path) -> dict[str, Any]:
    ranges: list[tuple[int, int]] = []
    errors: list[str] = []
    start_address: int | None = None
    base = 0
    eof = False

    for lineno, raw_line in enumerate(path.read_text(encoding="ascii", errors="replace").splitlines(), 1):
        line = raw_line.strip()
        if not line:
            continue
        if not line.startswith(":"):
            errors.append(f"line {lineno}: missing ':'")
            continue
        try:
            rec = bytes.fromhex(line[1:])
        except ValueError:
            errors.append(f"line {lineno}: invalid hex")
            continue
        if len(rec) < 5:
            errors.append(f"line {lineno}: record too short")
            continue
        if sum(rec) & 0xFF != 0:
            errors.append(f"line {lineno}: checksum mismatch")
        length = rec[0]
        addr = (rec[1] << 8) | rec[2]
        rtype = rec[3]
        payload = rec[4 : 4 + length]
        if rtype == 0x00:
            start = base + addr
            ranges.append((start, start + length))
        elif rtype == 0x01:
            eof = True
            break
        elif rtype == 0x02 and len(payload) == 2:
            base = ((payload[0] << 8) | payload[1]) << 4
        elif rtype == 0x04 and len(payload) == 2:
            base = ((payload[0] << 8) | payload[1]) << 16
        elif rtype == 0x05 and len(payload) == 4:
            start_address = int.from_bytes(payload, "big")

    merged: list[tuple[int, int]] = []
    for start, end in sorted(ranges):
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))

    return {
        "ranges": merged,
        "errors": errors,
        "start_address": start_address,
        "eof": eof,
        "total_bytes": sum(e - s for s, e in merged),
    }


# --------------------------------------------------------------------------
# C header / FreeRTOSConfig parsing
# --------------------------------------------------------------------------

CAST_RE = re.compile(
    r"\(\s*(?:const\s+)?(?:size_t|uint\d+_t|int\d*_t|unsigned\s+\w+|signed\s+\w+|long|short|char|int)\s*\)"
)


def parse_defines(path: Path) -> dict[str, str]:
    defines: dict[str, str] = {}
    if not path.exists():
        return defines
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = re.sub(r"/\*.*?\*/", "", line)
        m = re.match(r"\s*#\s*define\s+(\w+)\s+(.*)", line)
        if m:
            defines[m.group(1)] = m.group(2).strip()
    return defines


def eval_c_int(expr: str) -> int | None:
    s = expr.strip().rstrip(";")
    s = CAST_RE.sub("", s)
    s = re.sub(r"\b(0[xX][0-9a-fA-F]+|\d+)[uUlL]+\b", r"\1", s)
    s = s.strip()
    try:
        value = eval(s, {"__builtins__": {}}, {})  # noqa: S307 - trusted local header
        return int(value)
    except Exception:
        return None


# --------------------------------------------------------------------------
# Checks
# --------------------------------------------------------------------------

def add_header_checks(rep: Report, cfg: dict[str, Any], debug_dir: Path) -> dict[str, Path]:
    arts = cfg["artifacts"]
    paths = {k: debug_dir / v for k, v in arts.items()}
    missing = [k for k, p in paths.items() if not p.exists()]
    if missing:
        rep.add("产物", "文件存在", "fail", f"缺少: {', '.join(missing)}")
    else:
        rep.add(
            "产物",
            "文件存在",
            "pass",
            ", ".join(f"{k}={p.stat().st_size} B" for k, p in paths.items()),
        )
    return {k: p for k, p in paths.items() if p.exists()}


def check_freshness(rep: Report, cfg: dict[str, Any], paths: dict[str, Path]) -> None:
    if len(paths) < 3:
        return
    mtimes = {k: p.stat().st_mtime for k, p in paths.items()}
    spread = max(mtimes.values()) - min(mtimes.values())
    tol = cfg["thresholds"]["freshness_tolerance_sec"]
    if spread <= tol:
        rep.add("产物", "产物同批", "pass", f"三件产物时间差 {spread:.0f}s ≤ {tol}s")
    else:
        rep.add(
            "产物",
            "产物同批",
            "warn",
            f"三件产物时间差 {spread:.0f}s > {tol}s，可能存在陈旧产物",
        )

    # Source newer than ELF => artifacts are stale (critical for flashing).
    project = Path(cfg["project"]["path"])
    elf = paths["elf"]
    elf_mtime = elf.stat().st_mtime
    stale: list[str] = []
    for pattern in ("*.c", "*.h"):
        for src in project.rglob(pattern):
            # Skip build outputs and third-party libraries for noise control.
            parts = set(src.parts)
            if "Debug" in parts or "Libraries" in parts:
                continue
            if src.stat().st_mtime > elf_mtime + 1:
                stale.append(str(src.relative_to(project)))
    if stale:
        rep.add(
            "产物",
            "源码新鲜度",
            "fail",
            f"{len(stale)} 个源文件比 ELF 新（产物过期），例: {', '.join(stale[:5])}",
        )
    else:
        rep.add("产物", "源码新鲜度", "pass", "应用层源码均不晚于 ELF")


def check_invocation(rep: Report, map_data: dict[str, Any], cfg: dict[str, Any]) -> None:
    inv = map_data["tool_invocation"]
    tool = inv.get("tool", "")
    args = inv.get("arguments", "")
    rep.add("构建", "链接器", "info", tool or "(未解析)")
    device = cfg["expected"]["device_macro"]
    if device in args:
        rep.add("构建", "器件宏", "pass", device)
    else:
        rep.add("构建", "器件宏", "fail", f"未在链接参数中找到 {device}")

    # cctc translates --lsl-file= into ltc's -d option; accept both forms.
    m = re.search(r"(?:--lsl-file=|-d)(\S+\.lsl)", args)
    if m:
        lsl = m.group(1)
        rep.add("构建", "LSL 文件", "info", lsl)
    else:
        rep.add("构建", "LSL 文件", "warn", "未在链接参数中找到 LSL 文件")


def check_memory(rep: Report, used: dict[str, dict[str, int]], cfg: dict[str, Any]) -> None:
    if not used:
        rep.add("内存", "Used Resources", "fail", "未解析到内存使用表")
        return
    min_free = cfg["thresholds"]["min_free_memory_bytes"]
    problems = []
    for name, u in sorted(used.items()):
        total = u["code"] + u["data"] + u["reserved"]
        if total > u["total"]:
            problems.append(f"{name} 超限 {total:#x}/{u['total']:#x}")
        elif u["free"] < min_free and u["total"] > 0 and (u["code"] or u["data"]):
            # Pure-reserved regions (e.g. mpe:dfls0, DFI/UCB) legitimately have
            # no free space and no code/data; don't flag them.
            problems.append(f"{name} 余量仅 {u['free']:#x}")
    if problems:
        rep.add("内存", "容量", "fail", "; ".join(problems))
    else:
        rep.add("内存", "容量", "pass", f"{len(used)} 个内存区域均未超限")

    for key in ("mpe:pfls0", "mpe:dsram0"):
        if key in used:
            u = used[key]
            rep.add(
                "内存",
                key,
                "info",
                f"code={u['code']:#x} data={u['data']:#x} reserved={u['reserved']:#x} free={u['free']:#x}",
            )


def check_section_overlap(rep: Report, sections: list[dict[str, Any]]) -> None:
    by_chip: dict[str, list[dict[str, Any]]] = {}
    for s in sections:
        if s["size"] > 0:
            by_chip.setdefault(s["chip"], []).append(s)

    overlaps = []
    for chip, secs in by_chip.items():
        secs.sort(key=lambda x: x["space_addr"])
        for a, b in zip(secs, secs[1:]):
            if a["space_addr"] + a["size"] > b["space_addr"]:
                overlaps.append(
                    f"{chip}: {a['name']}[{a['space_addr']:#x}+{a['size']:#x}] "
                    f"与 {b['name']}[{b['space_addr']:#x}] 重叠"
                )
    if overlaps:
        rep.add("布局", "节区重叠", "fail", "; ".join(overlaps[:5]))
    else:
        rep.add("布局", "节区重叠", "pass", f"{len(sections)} 个节区无地址重叠")

    bad_align = [
        f"{s['name']}@{s['space_addr']:#x} 对齐 {s['align']:#x}"
        for s in sections
        if s["align"] > 0 and s["space_addr"] % s["align"] != 0
    ]
    if bad_align:
        rep.add("布局", "对齐", "warn", "; ".join(bad_align[:5]))
    else:
        rep.add("布局", "对齐", "pass", "所有节区满足对齐要求")


def check_csa_stacks(rep: Report, sections: list[dict[str, Any]], cfg: dict[str, Any]) -> None:
    by_name = {s["name"]: s for s in sections}
    expected_csa = cfg["expected"]["csa_size_bytes"]

    for core in cfg["expected"]["csa_cores"]:
        name = f"csa_tc{core}"
        sec = by_name.get(name)
        if not sec:
            rep.add("栈与CSA", name, "fail", "未找到 CSA 节区")
            continue
        if sec["size"] != expected_csa:
            rep.add(
                "栈与CSA",
                name,
                "warn",
                f"大小 {sec['size']:#x}，期望 {expected_csa:#x}（{expected_csa//64} 个 CSA）",
            )
        else:
            rep.add("栈与CSA", name, "pass", f"{sec['size']:#x}（{sec['size']//64} 个 CSA）")

    for core in cfg["expected"]["csa_cores"]:
        for kind in ("ustack", "istack"):
            name = f"{kind}_tc{core}"
            sec = by_name.get(name)
            if not sec:
                rep.add("栈与CSA", name, "fail", "未找到栈节区")
            elif sec["size"] == 0:
                rep.add("栈与CSA", name, "fail", "栈大小为 0")
            else:
                rep.add("栈与CSA", name, "pass", f"{sec['size']:#x}")

    # Core 0 is the one this FreeRTOS build actually uses; make its relationships explicit.
    us, isx, csa = by_name.get("ustack_tc0"), by_name.get("istack_tc0"), by_name.get("csa_tc0")
    if us and isx and csa:
        ok = us["space_addr"] + us["size"] <= isx["space_addr"] and isx["space_addr"] + isx["size"] <= csa["space_addr"]
        rep.add(
            "栈与CSA",
            "core0 布局顺序",
            "pass" if ok else "fail",
            f"ustack[{us['space_addr']:#x}] < istack[{isx['space_addr']:#x}] < csa[{csa['space_addr']:#x}]",
        )


def check_symbols(rep: Report, symbols: dict[str, int], cfg: dict[str, Any]) -> None:
    missing = []
    for name in cfg["expected"]["required_symbols"]:
        if name in OPTIONAL_REQUIRED:
            continue
        if name not in symbols:
            missing.append(name)
    if missing:
        rep.add("符号", "关键符号", "fail", f"缺少: {', '.join(missing)}")
    else:
        required_count = sum(1 for n in cfg["expected"]["required_symbols"] if n not in OPTIONAL_REQUIRED)
        rep.add("符号", "关键符号", "pass", f"{required_count} 个必备符号齐全")

    missing_fr = [n for n in cfg["expected"]["freertos_symbols"] if n not in symbols]
    if missing_fr:
        rep.add("符号", "FreeRTOS 符号", "fail", f"缺少: {', '.join(missing_fr)}")
    else:
        rep.add("符号", "FreeRTOS 符号", "pass", ", ".join(cfg["expected"]["freertos_symbols"]))

    entry = cfg["expected"]["entry_symbol"]
    if entry in symbols:
        rep.add("符号", "入口符号", "info", f"{entry}={symbols[entry]:#x}")
    else:
        rep.add("符号", "入口符号", "fail", f"未找到 {entry}")


def check_port_wiring(rep: Report, map_data: dict[str, Any], project: Path, cfg: dict[str, Any]) -> None:
    """Catch the S0 failure mode: SYSCALL trap not wired to the FreeRTOS handler."""
    sym = cfg["expected"]["trap_reference"]["symbol"]
    expected_ref = cfg["expected"]["trap_reference"]["referenced_by"]
    refs = [r for r in map_data["cross_refs"] if r["symbol"] == sym]
    ref_files = {r["referenced_in"] for r in refs}
    if expected_ref in ref_files:
        rep.add("Port 接线", "SYSCALL trap", "pass", f"{sym} 被 {expected_ref} 引用")
    else:
        rep.add(
            "Port 接线",
            "SYSCALL trap",
            "fail",
            f"{sym} 未被 {expected_ref} 引用（引用方: {', '.join(sorted(ref_files)) or '无'}）——检查 Ifx_Cfg.h 的 TRAP_SYSCALL hook",
        )

    ifx_cfg = project / "Configurations" / "Ifx_Cfg.h"
    if ifx_cfg.exists():
        text = ifx_cfg.read_text(encoding="utf-8", errors="replace")
        if "IFX_CFG_CPU_TRAP_SYSCALL_CPU0_HOOK" in text and "vPortSyscallHandler" in text:
            rep.add("Port 接线", "Ifx_Cfg.h hook", "pass", "已定义 SYSCALL hook")
        else:
            rep.add("Port 接线", "Ifx_Cfg.h hook", "fail", "未定义 IFX_CFG_CPU_TRAP_SYSCALL_CPU0_HOOK")
    else:
        rep.add("Port 接线", "Ifx_Cfg.h hook", "warn", "未找到 Configurations/Ifx_Cfg.h")


def check_heap_config(rep: Report, map_data: dict[str, Any], project: Path) -> None:
    cfg_h = project / "Configurations" / "FreeRTOSConfig.h"
    defines = parse_defines(cfg_h)
    if not defines:
        rep.add("配置", "FreeRTOSConfig.h", "warn", "未找到或无法解析")
        return

    heap_expr = defines.get("configTOTAL_HEAP_SIZE", "")
    heap_val = eval_c_int(heap_expr) if heap_expr else None
    # Find ucHeap section size in Locate Result.
    heap_sections = [s for s in map_data["sections"] if "ucHeap" in s["name"]]
    if heap_val is not None and heap_sections:
        actual = heap_sections[0]["size"]
        if actual == heap_val:
            rep.add("配置", "堆大小一致", "pass", f"configTOTAL_HEAP_SIZE={heap_val:#x} == ucHeap {actual:#x}")
        else:
            rep.add("配置", "堆大小一致", "fail", f"config={heap_val:#x} != ucHeap={actual:#x}")

    tick = eval_c_int(defines.get("configTICK_RATE_HZ", "")) if defines.get("configTICK_RATE_HZ") else None
    if tick:
        rep.add("配置", "tick", "info", f"configTICK_RATE_HZ={tick}（周期 {1000/tick:.3f} ms）")

    for key in (
        "configMAX_PRIORITIES",
        "configMINIMAL_STACK_SIZE",
        "configUSE_PREEMPTION",
        "configCHECK_FOR_STACK_OVERFLOW",
        "configUSE_TIMERS",
    ):
        if key in defines:
            rep.add("配置", key, "info", defines[key])


def check_core_affinity(rep: Report, map_data: dict[str, Any], cfg: dict[str, Any]) -> None:
    """Verify per-core code/data placement and shared-data placement."""
    result = analyze_core_affinity(map_data)

    for core in result["cores"]:
        n = core["core"]
        code_chips = ", ".join(k.replace("mpe:", "").upper() for k in core["code_chips"]) or "—"
        data_chips = ", ".join(k.replace("mpe:", "").upper() for k in core["data_chips"]) or "—"
        if core["violations"]:
            details = "; ".join(
                f"{v['section']} 在 {v['chip'].replace('mpe:', '').upper()}，应为 {'/'.join(e.replace('mpe:', '').upper() for e in v['expected'])}"
                for v in core["violations"][:3]
            )
            rep.add("核归属", f"Core {n}", "fail", f"code={code_chips}, data={data_chips}；{details}")
        else:
            rep.add("核归属", f"Core {n}", "pass", f"code={code_chips}, data={data_chips}")

    shared = result["shared"]
    if shared["in_lmu"] > 0:
        rep.add("核归属", "共享数据 → LMU", "pass", f"{shared['in_lmu']:#x} 位于 LMU")
    if shared["total"] > 0:
        chips = ", ".join(f"{k.replace('mpe:', '').upper()}={v:#x}" for k, v in shared["by_chip"].items())
        rep.add(
            "核归属",
            "共享数据 → 核私有 RAM",
            "warn",
            f"{shared['total']:#x} 位于 {chips}；单核或快速路径可接受，多核共享应迁移到 LMU",
        )
    elif shared["in_lmu"] == 0:
        rep.add("核归属", "共享数据", "pass", "未发现共享数据占用核私有 RAM")

    sp = result["scratchpad"]
    rep.add(
        "核归属",
        "PSPR 快速代码",
        "info",
        f"{sp['pspr_code']:#x}" + ("（未使用）" if sp["pspr_code"] == 0 else ""),
    )
    rep.add(
        "核归属",
        "DSPR 快速数据",
        "info",
        f"{sp['dspr_data']:#x}（含 CSA/栈/Heap）",
    )


def check_elf(rep: Report, elf: dict[str, Any], map_data: dict[str, Any], cfg: dict[str, Any]) -> None:
    entry_sym = cfg["expected"]["entry_symbol"]
    map_entry = map_data["symbols"].get(entry_sym)
    if map_entry is not None:
        if elf["entry"] == map_entry:
            rep.add("ELF", "入口一致", "pass", f"ELF entry == map {entry_sym} == {elf['entry']:#x}")
        else:
            rep.add("ELF", "入口一致", "fail", f"ELF entry {elf['entry']:#x} != map {entry_sym} {map_entry:#x}")
    else:
        rep.add("ELF", "入口一致", "warn", f"map 中无 {entry_sym}")

    rep.add("ELF", "机器类型", "info", f"e_machine={elf['machine']:#x}")

    text_secs = [s for s in elf["sections"] if s["name"].startswith(".text") and s["size"] > 0]
    data_secs = [s for s in elf["sections"] if (s["name"].startswith(".data") or s["name"].startswith(".bss")) and s["size"] > 0]
    rep.add("ELF", "节区统计", "info", f"{len(elf['sections'])} 节区；.text={len(text_secs)}，.data/.bss={len(data_secs)}")

    # Cross-check total section payload against map's PFlash usage (rough sanity).
    total_text = sum(s["size"] for s in text_secs)
    pfls = sum(
        u["code"] + u["data"]
        for name, u in map_data["used_resources"].items()
        if name.startswith("mpe:pfls")
    )
    if pfls and total_text:
        rep.add("ELF", "代码量对照", "info", f"ELF .text 合计 {total_text:#x}；map PFlash 使用 {pfls:#x}")


def check_hex(rep: Report, hex_data: dict[str, Any], elf: dict[str, Any]) -> None:
    if hex_data["errors"]:
        rep.add("HEX", "记录校验", "fail", "; ".join(hex_data["errors"][:5]))
    else:
        rep.add("HEX", "记录校验", "pass", f"{len(hex_data['ranges'])} 个连续段，校验通过")

    if hex_data["eof"]:
        rep.add("HEX", "EOF 记录", "pass", "存在")
    else:
        rep.add("HEX", "EOF 记录", "fail", "缺少 EOF 记录")

    if hex_data["start_address"] is not None:
        rep.add("HEX", "启动地址", "info", f"{hex_data['start_address']:#x}")

    loadable = [s for s in elf["sections"] if s["size"] > 0 and (s["flags"] & 0x2)]
    if loadable and hex_data["ranges"]:
        hex_start = min(s for s, _ in hex_data["ranges"])
        hex_end = max(e for _, e in hex_data["ranges"])
        elf_start = min(s["addr"] for s in loadable if s["addr"])
        elf_end = max(s["addr"] + s["size"] for s in loadable if s["addr"])
        if hex_start >= elf_start and hex_end <= elf_end + 0x1000:
            rep.add("HEX", "地址覆盖", "pass", f"HEX [{hex_start:#x},{hex_end:#x}] 落在 ELF 可加载范围内")
        else:
            rep.add(
                "HEX",
                "地址覆盖",
                "warn",
                f"HEX [{hex_start:#x},{hex_end:#x}] 与 ELF [{elf_start:#x},{elf_end:#x}] 不完全一致",
            )


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def load_config(project: str | None, config: str | None) -> dict[str, Any]:
    cfg = json.loads(json.dumps(DEFAULT_CONFIG))
    cfg_file = Path(__file__).resolve().parent.parent / "config.json"
    if cfg_file.exists():
        user_cfg = json.loads(cfg_file.read_text(encoding="utf-8"))
        for key, value in user_cfg.items():
            if isinstance(value, dict) and isinstance(cfg.get(key), dict):
                cfg[key].update(value)
            else:
                cfg[key] = value
    if project:
        cfg["project"]["path"] = project
    if config:
        cfg["project"]["build_config"] = config
    return cfg


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze AURIX TC3xx ADS/TASKING build artifacts")
    parser.add_argument("--project", help="project root (contains Debug/)")
    parser.add_argument("--config", help="build configuration directory name (default: Debug)")
    parser.add_argument("--json", action="store_true", help="emit JSON report")
    parser.add_argument("--strict", action="store_true", help="treat warnings as failures")
    args = parser.parse_args()

    cfg = load_config(args.project, args.config)
    project = Path(cfg["project"]["path"])
    debug_dir = project / cfg["project"]["build_config"]

    rep = Report()
    if not debug_dir.exists():
        rep.add("产物", "构建目录", "fail", f"不存在: {debug_dir}")
        return emit(rep, args)

    paths = add_header_checks(rep, cfg, debug_dir)
    check_freshness(rep, cfg, paths)

    map_data: dict[str, Any] = {"tool_invocation": {}, "used_resources": {}, "sections": [], "symbols": {}, "cross_refs": []}
    elf_data: dict[str, Any] | None = None
    hex_data: dict[str, Any] | None = None

    if "map" in paths:
        map_data = parse_map(paths["map"])
        check_invocation(rep, map_data, cfg)
        check_memory(rep, map_data["used_resources"], cfg)
        check_section_overlap(rep, map_data["sections"])
        check_csa_stacks(rep, map_data["sections"], cfg)
        check_symbols(rep, map_data["symbols"], cfg)
        check_port_wiring(rep, map_data, project, cfg)
        check_heap_config(rep, map_data, project)
        check_core_affinity(rep, map_data, cfg)

    if "elf" in paths:
        try:
            elf_data = parse_elf(paths["elf"])
            check_elf(rep, elf_data, map_data, cfg)
        except Exception as exc:  # noqa: BLE001 - report, don't crash
            rep.add("ELF", "解析", "fail", str(exc))

    if "hex" in paths:
        try:
            hex_data = parse_hex(paths["hex"])
            if elf_data:
                check_hex(rep, hex_data, elf_data)
            else:
                rep.add("HEX", "解析", "warn", "ELF 不可用，跳过地址覆盖检查")
        except Exception as exc:  # noqa: BLE001
            rep.add("HEX", "解析", "fail", str(exc))

    rep.data = {
        "project": str(project),
        "debug_dir": str(debug_dir),
        "map_symbols": len(map_data["symbols"]),
        "map_sections": len(map_data["sections"]),
        "elf_sections": len(elf_data["sections"]) if elf_data else 0,
        "hex_bytes": hex_data["total_bytes"] if hex_data else 0,
    }
    return emit(rep, args)


def emit(rep: Report, args: argparse.Namespace) -> int:
    counts = rep.counts()
    if args.json:
        print(
            json.dumps(
                {
                    "checks": [c.__dict__ for c in rep.checks],
                    "summary": counts,
                    "data": rep.data,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        print("=" * 78)
        print("AURIX TC3xx 构建产物分析")
        print("=" * 78)
        group = None
        for c in rep.checks:
            if c.group != group:
                print(f"\n[{c.group}]")
                group = c.group
            icon = {"pass": "✅", "warn": "⚠️ ", "fail": "❌", "info": "ℹ️ "}[c.status]
            print(f"  {icon} {c.name}: {c.detail}")
        print("\n" + "-" * 78)
        print(
            f"汇总: {counts['pass']} 通过 / {counts['warn']} 警告 / "
            f"{counts['fail']} 失败 / {counts['info']} 信息"
        )
        if rep.data:
            print(f"数据: {rep.data}")

    if counts["fail"] > 0:
        return 1
    if args.strict and counts["warn"] > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
