#!/usr/bin/env python3
"""Generate a self-contained interactive HTML memory report from a TASKING map.

Views:
  1. Memory overview   - used/free per physical region (PFlash, DSPR, PSPR, ...)
  2. Section types     - code / rodata / data / bss / heap / CSA / stacks / vectors
  3. Modules           - object-file contributions (tasks.o, port.o, iLLD, ...)
  4. Address layout    - sections positioned inside each memory region
  5. Section table     - sortable/searchable full detail

Usage:
    py -3 report_html.py [--project DIR] [--config Debug] [--output FILE] [--open]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import webbrowser
from collections import defaultdict
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from analyze import (  # noqa: E402
    _strip_section_id,
    analyze_core_affinity,
    eval_c_int,
    parse_defines,
    parse_map,
)

# --------------------------------------------------------------------------
# Classification
# --------------------------------------------------------------------------

TYPE_ORDER = [
    "Code",
    "RO Data",
    "Data",
    "BSS",
    "Heap",
    "CSA",
    "UStack",
    "IStack",
    "Vector",
    "Reserved",
    "Other",
]


def sec_type(name: str) -> str:
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


def mem_kind(name: str) -> str:
    n = name.replace("mpe:", "")
    if n.startswith("pfls"):
        return "PFlash"
    if n.startswith("dfls"):
        return "DFlash"
    if n.startswith("dsram"):
        return "DSPR"
    if n.startswith("psram"):
        return "PSPR"
    if n.endswith("_dlmu"):
        return "DLMU"
    if n.startswith("lmuram"):
        return "LMU"
    if n.startswith("edmem"):
        return "EMEM"
    if n == "ucb":
        return "UCB"
    return "Other"


KIND_ORDER = ["PFlash", "DFlash", "DSPR", "PSPR", "DLMU", "LMU", "EMEM", "UCB", "Other"]

# Memory regions the user does not want in the report (override in config.json).
EXCLUDED_MEMORIES = {"mpe:dfls0", "mpe:ucb", "mpe:edmem"}

GROUP_ORDER = ["flash", "dsp", "dlmu", "lmu", "other"]


def _load_report_cfg() -> dict:
    cfg_path = HERE.parent / "config.json"
    if not cfg_path.exists():
        return {}
    try:
        return json.loads(cfg_path.read_text(encoding="utf-8")).get("report", {})
    except Exception:
        return {}


_RCFG = _load_report_cfg()
EXCLUDED_MEMORIES = set(_RCFG.get("exclude_memories", EXCLUDED_MEMORIES))
GROUP_ORDER = _RCFG.get("group_order", GROUP_ORDER)
GROUP_LABELS = {
    "flash": "Flash",
    "dsp": "DSPR & PSPR",
    "dlmu": "CPUx DLMU",
    "lmu": "LMU",
    "other": "Other",
}


def mem_group(kind: str) -> str:
    if kind == "PFlash":
        return "flash"
    if kind in ("DSPR", "PSPR"):
        return "dsp"
    if kind == "DLMU":
        return "dlmu"
    if kind == "LMU":
        return "lmu"
    return "other"


def core_of(short: str) -> int:
    m = re.search(r"(\d+)", short)
    return int(m.group(1)) if m else 99


# --------------------------------------------------------------------------
# LSL memory definitions (authoritative base/size)
# --------------------------------------------------------------------------

def _parse_size(text: str) -> int:
    m = re.match(r"\s*(\d+)\s*([kKmM]?)", text)
    if not m:
        return 0
    value = int(m.group(1))
    unit = m.group(2).lower()
    if unit == "k":
        value *= 1024
    elif unit == "m":
        value *= 1024 * 1024
    return value


def parse_lsl(path: Path) -> dict[str, dict]:
    """Return {region: {base, size}} from a TASKING LSL file."""
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8", errors="replace")
    regions: dict[str, dict] = {}
    # Allow a trailing comment between the memory name and '{'.
    for m in re.finditer(r"\bmemory\s+(\w+)[^{]*\{(.*?)\n\s*\}", text, re.S):
        name, body = m.group(1), m.group(2)
        size_m = re.search(r"\bsize\s*=\s*(\d+\s*[kKmM]?)", body)
        size = _parse_size(size_m.group(1)) if size_m else 0
        base = None
        for mm in re.finditer(r"map\s+(?:cached\s+|not_cached\s+)?\(([^)]*)\)", body):
            mp = mm.group(1)
            if "dest=bus:sri" in mp and "reserved" not in mp:
                off = re.search(r"dest_offset\s*=\s*(0x[0-9a-fA-F]+)", mp)
                if off:
                    base = int(off.group(1), 16)
                    break
        if size:
            regions[name] = {"base": base, "size": size}
    return regions


# --------------------------------------------------------------------------
# Dataset
# --------------------------------------------------------------------------

def build_data(project: Path, config: str) -> dict:
    debug = project / config
    map_path = debug / "FreeRTOS.map"
    lsl_path = project / "Lcf_Tasking_Tricore_Tc.lsl"

    map_data = parse_map(map_path)
    lsl = parse_lsl(lsl_path)

    used = map_data["used_resources"]
    placed = map_data["sections"]
    link = map_data["link_result"]

    # Object file responsible for each input section.
    sec_module: dict[str, str] = {}
    link_total_by_module: dict[str, int] = defaultdict(int)
    for row in link:
        sec_module.setdefault(row["section"], row["file"])
        link_total_by_module[row["file"]] += row["size"]

    # Placed sections (what actually occupies memory).
    section_records: list[dict] = []
    for s in placed:
        t = sec_type(s["name"])
        mod = sec_module.get(s["name"], "linker/LSL")
        section_records.append(
            {
                "name": s["name"],
                "chip": s["chip"],
                "chip_display": s["chip"].replace("mpe:", "").upper(),
                "addr": s["space_addr"],
                "size": s["size"],
                "type": t,
                "module": mod,
                "group": s["group"],
            }
        )

    # Module aggregates (use placed sizes so totals reconcile with memory usage).
    module_size: dict[str, int] = defaultdict(int)
    module_types: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    module_chips: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for r in section_records:
        module_size[r["module"]] += r["size"]
        module_types[r["module"]][r["type"]] += r["size"]
        module_chips[r["module"]][r["chip"]] += r["size"]

    modules = [
        {
            "name": name,
            "size": size,
            "link_total": link_total_by_module.get(name, 0),
            "types": dict(module_types[name]),
            "chips": dict(module_chips[name]),
        }
        for name, size in module_size.items()
    ]
    modules.sort(key=lambda x: -x["size"])

    # Memories.
    memories: list[dict] = []
    for key, u in used.items():
        if key in EXCLUDED_MEMORIES:
            continue
        short = key.replace("mpe:", "")
        info = lsl.get(short, {})
        secs = [r for r in section_records if r["chip"] == key]
        by_type: dict[str, int] = defaultdict(int)
        for r in secs:
            by_type[r["type"]] += r["size"]

        total = u["total"]
        used_bytes = u["code"] + u["data"] + u["reserved"]
        sec_sum = sum(by_type.values())
        # Reserved/linker-generated remainder without a placed section.
        if used_bytes > sec_sum:
            by_type["Reserved"] += used_bytes - sec_sum

        kind = mem_kind(short)
        memories.append(
            {
                "name": key,
                "short": short,
                "display": short.upper(),
                "kind": kind,
                "group": mem_group(kind),
                "core": core_of(short),
                "base": info.get("base"),
                "total": total,
                "code": u["code"],
                "data": u["data"],
                "reserved": u["reserved"],
                "used": used_bytes,
                "free": u["free"],
                "by_type": dict(by_type),
                "sections": secs,
                "pct": (used_bytes * 100.0 / total) if total else 0.0,
            }
        )
    type_rank = {"DSPR": 0, "PSPR": 1}
    memories.sort(
        key=lambda m: (
            GROUP_ORDER.index(m["group"]) if m["group"] in GROUP_ORDER else 99,
            m["core"],
            type_rank.get(m["kind"], 0),
            m["name"],
        )
    )

    # Type totals across all placed sections + reserved remainder.
    type_totals: dict[str, int] = defaultdict(int)
    for m in memories:
        for t, size in m["by_type"].items():
            type_totals[t] += size

    # Split by storage class (DFlash/UCB/EMEM are excluded on request).
    flash_types: dict[str, int] = defaultdict(int)
    ram_types: dict[str, int] = defaultdict(int)
    for m in memories:
        target = flash_types if m["kind"] == "PFlash" else ram_types
        for t, size in m["by_type"].items():
            target[t] += size

    pflash_memories = [m for m in memories if m["kind"] == "PFlash"]
    ram_kinds = ("DSPR", "PSPR", "DLMU", "LMU")
    ram_memories = [m for m in memories if m["kind"] in ram_kinds]

    # FreeRTOS configuration cross-check.
    defines = parse_defines(project / "Configurations" / "FreeRTOSConfig.h")
    cfg_heap = eval_c_int(defines.get("configTOTAL_HEAP_SIZE", "")) if defines.get("configTOTAL_HEAP_SIZE") else None
    uc_heap = next((s["size"] for s in section_records if "ucHeap" in s["name"]), None)
    csa_sections = [s for s in section_records if s["type"] == "CSA"]

    summary = {
        "flash_used": sum(m["used"] for m in pflash_memories),
        "flash_total": sum(m["total"] for m in pflash_memories),
        "ram_used": sum(m["used"] for m in ram_memories),
        "ram_total": sum(m["total"] for m in ram_memories),
        "dsp_used": sum(m["used"] for m in memories if m["kind"] == "DSPR"),
        "dsp_total": sum(m["total"] for m in memories if m["kind"] == "DSPR"),
        "csa_total": sum(s["size"] for s in csa_sections),
        "csa_entries": (csa_sections[0]["size"] // 64) if csa_sections else 0,
        "heap_config": cfg_heap,
        "heap_actual": uc_heap,
    }

    config_info = {
        "tick": eval_c_int(defines.get("configTICK_RATE_HZ", "")) if defines.get("configTICK_RATE_HZ") else None,
        "max_prio": eval_c_int(defines.get("configMAX_PRIORITIES", "")) if defines.get("configMAX_PRIORITIES") else None,
        "min_stack": eval_c_int(defines.get("configMINIMAL_STACK_SIZE", "")) if defines.get("configMINIMAL_STACK_SIZE") else None,
        "preemption": defines.get("configUSE_PREEMPTION", ""),
        "stack_check": defines.get("configCHECK_FOR_STACK_OVERFLOW", ""),
        "timers": defines.get("configUSE_TIMERS", ""),
    }

    return {
        "meta": {
            "project": str(project),
            "config": config,
            "generated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "map": str(map_path),
            "lsl": str(lsl_path),
        },
        "summary": summary,
        "config": config_info,
        "memories": memories,
        "modules": modules,
        "sections": section_records,
        "core_affinity": analyze_core_affinity(map_data),
        "type_totals": dict(type_totals),
        "flash_types": dict(flash_types),
        "ram_types": dict(ram_types),
        "group_order": GROUP_ORDER,
        "group_labels": GROUP_LABELS,
        "type_order": TYPE_ORDER,
    }


# --------------------------------------------------------------------------
# HTML template
# --------------------------------------------------------------------------

HTML = r"""<!DOCTYPE html>
<html lang="zh-CN" data-theme="dark">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>TC397 内存占用报告</title>
<style>
:root[data-theme="dark"]{
  --bg:#0e1219; --panel:#151b24; --panel2:#1c2431; --border:#26303f;
  --text:#e6ebf2; --muted:#8b97a8; --free:#232a36; --accent:#4c8dff;
  --shadow:0 4px 18px rgba(0,0,0,.35);
}
:root[data-theme="light"]{
  --bg:#f4f6fa; --panel:#ffffff; --panel2:#eef2f7; --border:#d8e0ea;
  --text:#1b2430; --muted:#5d6b7c; --free:#e3e8ef; --accent:#2563eb;
  --shadow:0 4px 18px rgba(20,40,80,.08);
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--text);
  font-family:"Segoe UI","Microsoft YaHei",system-ui,-apple-system,sans-serif;font-size:14px;line-height:1.5}
.container{max-width:1440px;margin:0 auto;padding:28px 32px 60px}
header{display:flex;justify-content:space-between;align-items:flex-start;gap:20px;margin-bottom:24px}
h1{font-size:24px;margin:0 0 6px}
.sub{color:var(--muted);font-size:12px}
button{background:var(--panel2);color:var(--text);border:1px solid var(--border);
  border-radius:8px;padding:8px 14px;cursor:pointer;font-size:13px}
button:hover{border-color:var(--accent)}
h2{font-size:17px;margin:34px 0 14px;padding-bottom:8px;border-bottom:1px solid var(--border)}
h3{font-size:14px;margin:18px 0 8px;font-weight:600}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(215px,1fr));gap:14px}
.card{background:var(--panel);border:1px solid var(--border);border-radius:12px;padding:16px 18px;box-shadow:var(--shadow)}
.card .label{color:var(--muted);font-size:12px;margin-bottom:6px}
.card .value{font-size:24px;font-weight:700;letter-spacing:-.3px}
.card .meta{color:var(--muted);font-size:12px;margin-top:4px}
.card .bar{margin-top:10px}
.bar{display:flex;height:20px;border-radius:5px;overflow:hidden;background:var(--free);width:100%}
.bar>div{height:100%;transition:filter .12s}
.bar>div:hover{filter:brightness(1.25)}
.group-box{background:var(--panel);border:1px solid var(--border);border-radius:10px;padding:14px 18px;margin-bottom:14px}
.group-title{font-size:13px;font-weight:700;margin:0 0 10px;display:flex;justify-content:space-between;align-items:baseline;gap:12px}
.group-title span{color:var(--muted);font-weight:400;font-size:11.5px}
.mem-row{display:grid;grid-template-columns:275px 1fr 150px;gap:14px;align-items:center;padding:7px 0;border-bottom:1px dashed var(--border)}
.mem-row:last-child{border-bottom:none}
.mem-label b{display:block;font-size:13px}
.mem-label span{color:var(--muted);font-size:11px;display:block}
.mem-label .addr{font-size:10.5px;font-family:Consolas,"Cascadia Mono",monospace;margin-top:1px}
.mem-stats{text-align:right;font-size:12px;color:var(--muted)}
.mem-stats b{color:var(--text);font-size:13px}
.legend{display:flex;flex-wrap:wrap;gap:14px;margin:10px 0 4px;font-size:12px;color:var(--muted)}
.legend span{display:inline-flex;align-items:center;gap:6px}
.dot{width:10px;height:10px;border-radius:2px;display:inline-block}
.grid2{display:grid;grid-template-columns:1.15fr .85fr;gap:28px}
@media(max-width:980px){.grid2{grid-template-columns:1fr}.mem-row{grid-template-columns:1fr}.mem-stats{text-align:left}}
.donut-wrap{display:flex;gap:26px;align-items:center;flex-wrap:wrap}
.donut{width:190px;height:190px;border-radius:50%;position:relative;flex:0 0 auto}
.donut::after{content:"";position:absolute;inset:46px;background:var(--panel);border-radius:50%}
.donut-center{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;z-index:1}
.donut-center b{font-size:18px}
.donut-center span{font-size:11px;color:var(--muted)}
table{width:100%;border-collapse:collapse;font-size:12.5px}
th,td{padding:7px 9px;border-bottom:1px solid var(--border);text-align:left;white-space:nowrap}
th{color:var(--muted);font-weight:600;cursor:pointer;user-select:none;position:sticky;top:0;background:var(--panel);z-index:2}
th:hover{color:var(--accent)}
tr:hover td{background:var(--panel2)}
td.num{text-align:right;font-variant-numeric:tabular-nums}
.mono{font-family:Consolas,"Cascadia Mono",monospace}
input[type=search]{width:320px;max-width:100%;background:var(--panel);border:1px solid var(--border);
  color:var(--text);border-radius:8px;padding:8px 12px;margin-bottom:10px;font-size:13px}
.table-wrap{max-height:520px;overflow:auto;border:1px solid var(--border);border-radius:10px}
.addr-block{background:var(--panel);border:1px solid var(--border);border-radius:10px;padding:14px 16px;margin-bottom:14px}
.addr-head{display:flex;justify-content:space-between;gap:12px;align-items:baseline;margin-bottom:10px}
.addr-head .range{color:var(--muted);font-size:11px}
.addr-map{position:relative;height:30px;background:var(--free);border-radius:5px;overflow:hidden}
.addr-map .seg{position:absolute;top:0;height:100%;min-width:1px}
.addr-map .seg:hover{outline:1px solid #fff;outline-offset:-1px;z-index:3}
.addr-ticks{display:flex;justify-content:space-between;color:var(--muted);font-size:10.5px;margin-top:5px;font-family:Consolas,monospace}
.empty-note{color:var(--muted);font-size:12px;padding:6px 0}
.module-row{display:grid;grid-template-columns:190px 1fr 130px;gap:12px;align-items:center;padding:4px 0}
.module-row .name{font-size:12.5px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.module-row .num{text-align:right;font-size:12px;color:var(--muted);font-variant-numeric:tabular-nums}
.tooltip{position:fixed;display:none;z-index:99;background:var(--panel);border:1px solid var(--border);
  border-radius:8px;padding:8px 11px;font-size:12px;box-shadow:var(--shadow);max-width:420px;pointer-events:none;
  white-space:pre-line}
footer{margin-top:44px;padding-top:16px;border-top:1px solid var(--border);color:var(--muted);font-size:11.5px}
.kv{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:8px 18px;margin-top:8px}
.kv div{color:var(--muted);font-size:12px}
.kv b{color:var(--text)}
</style>
</head>
<body>
<div class="container">
  <header>
    <div>
      <h1>TC397 内存占用报告</h1>
      <div class="sub" id="meta"></div>
    </div>
    <button id="theme-toggle">切换主题</button>
  </header>

  <section class="cards" id="cards"></section>

  <h2>内存总览 · 各物理区域</h2>
  <div class="legend" id="legend"></div>
  <div id="memory-overview"></div>

  <h2>核归属检查</h2>
  <div id="core-affinity"></div>

  <div class="grid2">
    <section>
      <h2>段类型分布</h2>
      <div class="donut-wrap">
        <div class="donut" id="donut"><div class="donut-center"><b id="donut-total"></b><span>已占用</span></div></div>
        <div style="flex:1;min-width:250px"><table id="type-table"></table></div>
      </div>
    </section>
    <section>
      <h2>Flash / RAM 构成</h2>
      <div id="split-chart"></div>
    </section>
  </div>

  <h2>模块占用 · 按目标文件</h2>
  <div id="module-chart"></div>
  <input type="search" id="module-search" placeholder="搜索模块（如 tasks.o / Ifx / port）">
  <div class="table-wrap"><table id="module-table"></table></div>

  <h2>节区明细</h2>
  <input type="search" id="section-search" placeholder="搜索节区 / 模块 / 类型">
  <div class="table-wrap"><table id="section-table"></table></div>

  <footer id="footer"></footer>
</div>
<div class="tooltip" id="tooltip"></div>

<script>
const DATA = __DATA__;
const COLORS = {
  "Code":"#4C8DFF","RO Data":"#2BB3A3","Data":"#F5A623","BSS":"#9B7EDE",
  "Heap":"#E06C9F","CSA":"#E05C5C","UStack":"#45B26B","IStack":"#8BC34A",
  "Vector":"#C08A5E","Reserved":"#5C6779","Other":"#7A8494"
};
const TYPES = DATA.type_order;
const fmt = n => {
  if(n === null || n === undefined) return "—";
  if(n < 1024) return n + " B";
  if(n < 1024*1024) return (n/1024).toFixed(n<10240?2:1) + " KB";
  return (n/1024/1024).toFixed(2) + " MB";
};
const hex = n => "0x" + n.toString(16).toUpperCase();
const pct = (a,b) => b ? (a*100/b) : 0;
const esc = s => String(s).replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;"}[c]));
const tip = (el, text) => { el.dataset.tip = text; return el; };

function barSegment(type, size, total){
  const d = document.createElement("div");
  d.style.width = (total ? size*100/total : 0) + "%";
  d.style.background = COLORS[type] || COLORS.Other;
  tip(d, type + " · " + fmt(size) + " (" + pct(size,total).toFixed(1) + "%)");
  return d;
}

/* ---------- header ---------- */
document.getElementById("meta").textContent =
  DATA.meta.project + " · " + DATA.meta.config + " · 生成于 " + DATA.meta.generated;

/* ---------- cards ---------- */
function renderCards(){
  const s = DATA.summary;
  const cards = [
    {label:"PFlash 已用", value:fmt(s.flash_used), meta:fmt(s.flash_used)+" / "+fmt(s.flash_total)+" ("+pct(s.flash_used,s.flash_total).toFixed(1)+"%)", ratio:pct(s.flash_used,s.flash_total)},
    {label:"DSPR 已用（6 核）", value:fmt(s.dsp_used), meta:fmt(s.dsp_used)+" / "+fmt(s.dsp_total)+" ("+pct(s.dsp_used,s.dsp_total).toFixed(1)+"%)", ratio:pct(s.dsp_used,s.dsp_total)},
    {label:"全部 RAM 已用", value:fmt(s.ram_used), meta:"DSPR+PSPR+LMU+DLMU+EMEM · "+pct(s.ram_used,s.ram_total).toFixed(1)+"%", ratio:pct(s.ram_used,s.ram_total)},
    {label:"CSA 预留", value:fmt(s.csa_total), meta:"每核 "+s.csa_entries+" 个 CSA（64 B/个）", ratio:null},
    {label:"FreeRTOS 堆", value:fmt(s.heap_actual), meta:"configTOTAL_HEAP_SIZE = "+fmt(s.heap_config), ratio:null},
  ];
  const root = document.getElementById("cards");
  for(const c of cards){
    const div = document.createElement("div");
    div.className = "card";
    div.innerHTML = '<div class="label">'+esc(c.label)+'</div><div class="value">'+esc(c.value)+'</div><div class="meta">'+esc(c.meta)+'</div>';
    if(c.ratio !== null){
      const b = document.createElement("div"); b.className="bar";
      const used = document.createElement("div");
      used.style.width = Math.min(100,c.ratio)+"%"; used.style.background="var(--accent)";
      b.appendChild(used); div.appendChild(b);
    }
    root.appendChild(div);
  }
}

/* ---------- legend ---------- */
function renderLegend(){
  const root = document.getElementById("legend");
  for(const t of TYPES){
    const s = document.createElement("span");
    s.innerHTML = '<i class="dot" style="background:'+(COLORS[t]||COLORS.Other)+'"></i>'+t;
    root.appendChild(s);
  }
}

/* ---------- memory overview ---------- */
function renderOverview(){
  const root = document.getElementById("memory-overview");
  const groups = DATA.group_order || ["flash","dsp","dlmu","lmu","other"];
  for(const g of groups){
    const mems = DATA.memories.filter(m => m.group === g && m.total);
    if(!mems.length) continue;
    const gUsed = mems.reduce((a,m)=>a+m.used,0);
    const gTotal = mems.reduce((a,m)=>a+m.total,0);
    const box = document.createElement("div"); box.className="group-box";
    const title = document.createElement("div"); title.className="group-title";
    title.innerHTML = "<div>"+(DATA.group_labels[g]||g)+"</div>"+
      "<span>"+fmt(gUsed)+" / "+fmt(gTotal)+" ("+pct(gUsed,gTotal).toFixed(1)+"%)</span>";
    box.appendChild(title);

    for(const m of mems){
      const row = document.createElement("div"); row.className="mem-row";
      const label = document.createElement("div"); label.className="mem-label";
      const addrText = (m.base !== null && m.total)
        ? hex(m.base)+" – "+hex(m.base+m.total-1) : "—";
      label.innerHTML = "<b>"+esc(m.display)+"</b>"+
        "<span>"+m.kind+" · "+fmt(m.total)+"</span>"+
        "<span class='addr'>"+addrText+"</span>";
      const bar = document.createElement("div"); bar.className="bar";
      for(const t of TYPES){
        const size = m.by_type[t] || 0;
        if(size > 0) bar.appendChild(barSegment(t,size,m.total));
      }
      if(m.free > 0){
        const f = document.createElement("div");
        f.style.width = (m.free*100/m.total)+"%"; f.style.background="var(--free)";
        tip(f, "Free · "+fmt(m.free)+" ("+pct(m.free,m.total).toFixed(1)+"%)");
        bar.appendChild(f);
      }
      const stats = document.createElement("div"); stats.className="mem-stats";
      stats.innerHTML = "<b>"+m.pct.toFixed(1)+"%</b> 已用<br>"+fmt(m.used)+" / "+fmt(m.total);
      row.appendChild(label); row.appendChild(bar); row.appendChild(stats);
      box.appendChild(row);
    }
    root.appendChild(box);
  }
}

/* ---------- core affinity ---------- */
function renderCoreAffinity(){
  const ca = DATA.core_affinity;
  const root = document.getElementById("core-affinity");
  if(!ca) return;

  const box = document.createElement("div"); box.className="group-box";
  const title = document.createElement("div"); title.className="group-title";
  title.innerHTML = "<div>每核代码 / 数据归属</div>"+
    "<span>代码 → 本核 PFLS/PSPR；数据 → 本核 DSRAM/DLMU；共享数据 → LMU</span>";
  box.appendChild(title);

  const table = document.createElement("table");
  table.innerHTML = "<thead><tr><th>核</th><th>代码位置</th><th>数据位置</th><th>结果</th></tr></thead>";
  const tb = document.createElement("tbody");
  for(const c of ca.cores){
    const code = Object.keys(c.code_chips||{}).map(k=>k.replace("mpe:","").toUpperCase()).join(", ") || "—";
    const data = Object.keys(c.data_chips||{}).map(k=>k.replace("mpe:","").toUpperCase()).join(", ") || "—";
    const ok = c.code_ok && c.data_ok;
    const tr = document.createElement("tr");
    tr.innerHTML = "<td>Core "+c.core+"</td><td class='mono'>"+code+"</td><td class='mono'>"+data+"</td>"+
      "<td>"+(ok ? "✅ 通过" : "❌ "+(c.violations||[]).length+" 项违规")+"</td>";
    tb.appendChild(tr);
  }
  table.appendChild(tb); box.appendChild(table);

  if(ca.violations && ca.violations.length){
    const v = document.createElement("div"); v.className="empty-note";
    v.innerHTML = ca.violations.slice(0,10).map(x =>
      "❌ Core "+x.core+" · "+x.kind+" · <span class='mono'>"+esc(x.section)+"</span> 在 "+
      x.chip.replace("mpe:","").toUpperCase()+"，应为 "+
      x.expected.map(e=>e.replace("mpe:","").toUpperCase()).join("/")
    ).join("<br>");
    box.appendChild(v);
  }

  const sh = ca.shared || {total:0,in_lmu:0,by_chip:{}};
  const sp = ca.scratchpad || {pspr_code:0,dspr_data:0};
  const lines = [];
  if(sh.total > 0){
    const chips = Object.entries(sh.by_chip).map(([k,v])=>k.replace("mpe:","").toUpperCase()+" "+fmt(v)).join(", ");
    lines.push("<b>⚠️ 共享数据</b>: "+fmt(sh.total)+" 位于 "+chips+
      " — 单核/快速路径可接受；多核共享应迁移到 LMU");
  } else if(sh.in_lmu > 0){
    lines.push("<b>✅ 共享数据</b>: "+fmt(sh.in_lmu)+" 位于 LMURAM");
  } else {
    lines.push("<b>✅ 共享数据</b>: 未占用核私有 RAM");
  }
  lines.push("<b>PSPR 快速代码</b>: "+fmt(sp.pspr_code)+(sp.pspr_code?"":"（未使用）"));
  lines.push("<b>DSPR 快速数据</b>: "+fmt(sp.dspr_data)+"（含 CSA/栈/Heap）");
  const info = document.createElement("div"); info.className="legend";
  info.innerHTML = lines.map(x=>"<span>"+x+"</span>").join("");
  box.appendChild(info);

  root.appendChild(box);
}

/* ---------- type donut + table ---------- */
function renderTypes(){
  const totals = {};
  for(const t of TYPES) totals[t] = 0;
  for(const m of DATA.memories){
    for(const [t,v] of Object.entries(m.by_type)) totals[t] = (totals[t]||0) + v;
  }
  const sum = Object.values(totals).reduce((a,b)=>a+b,0);
  document.getElementById("donut-total").textContent = fmt(sum);

  let acc = 0; const stops = [];
  for(const t of TYPES){
    const v = totals[t] || 0;
    if(v <= 0) continue;
    const start = acc/sum*360, end = (acc+v)/sum*360;
    stops.push((COLORS[t]||COLORS.Other)+" "+start.toFixed(2)+"deg "+end.toFixed(2)+"deg");
    acc += v;
  }
  document.getElementById("donut").style.background =
    stops.length ? "conic-gradient("+stops.join(",")+")" : "var(--free)";

  const table = document.getElementById("type-table");
  table.innerHTML = "<thead><tr><th>类型</th><th class='num'>大小</th><th class='num'>占比</th></tr></thead>";
  const tb = document.createElement("tbody");
  for(const t of TYPES){
    const v = totals[t] || 0;
    if(v <= 0) continue;
    const tr = document.createElement("tr");
    tr.innerHTML = "<td><i class='dot' style='background:"+(COLORS[t]||COLORS.Other)+"'></i> "+t+"</td>"+
                   "<td class='num mono'>"+hex(v)+"</td><td class='num'>"+pct(v,sum).toFixed(1)+"%</td>";
    tb.appendChild(tr);
  }
  table.appendChild(tb);
}

/* ---------- flash / ram composition ---------- */
function stackedBar(title, map, total){
  const wrap = document.createElement("div");
  wrap.innerHTML = "<h3>"+title+" · "+fmt(total)+"</h3>";
  const bar = document.createElement("div"); bar.className="bar"; bar.style.height="26px";
  for(const t of TYPES){
    const v = map[t] || 0;
    if(v > 0) bar.appendChild(barSegment(t,v,total));
  }
  wrap.appendChild(bar);
  const legend = document.createElement("div"); legend.className="legend";
  for(const t of TYPES){
    const v = map[t] || 0;
    if(v <= 0) continue;
    const s = document.createElement("span");
    s.innerHTML = '<i class="dot" style="background:'+(COLORS[t]||COLORS.Other)+'"></i>'+t+" "+fmt(v);
    legend.appendChild(s);
  }
  wrap.appendChild(legend);
  return wrap;
}
function renderSplit(){
  const root = document.getElementById("split-chart");
  const flashTotal = Object.values(DATA.flash_types).reduce((a,b)=>a+b,0);
  const ramTotal = Object.values(DATA.ram_types).reduce((a,b)=>a+b,0);
  root.appendChild(stackedBar("Flash（PFlash）", DATA.flash_types, flashTotal));
  root.appendChild(stackedBar("RAM（DSPR / PSPR / DLMU / LMU）", DATA.ram_types, ramTotal));
}

/* ---------- modules ---------- */
function renderModules(filter){
  const q = (filter||"").toLowerCase();
  const mods = DATA.modules.filter(m=>!q || m.name.toLowerCase().includes(q));
  const max = Math.max(...mods.map(m=>m.size), 1);
  const root = document.getElementById("module-chart");
  root.innerHTML = "";
  for(const m of mods.slice(0,20)){
    const row = document.createElement("div"); row.className="module-row";
    const name = document.createElement("div"); name.className="name mono"; name.textContent=m.name;
    name.title = m.name;
    const bar = document.createElement("div"); bar.className="bar"; bar.style.height="16px";
    const seg = document.createElement("div");
    seg.style.width = (m.size*100/max)+"%";
    seg.style.background = COLORS[Object.entries(m.types).sort((a,b)=>b[1]-a[1])[0]?.[0]] || COLORS.Other;
    tip(seg, m.name+" · "+fmt(m.size)+"（占比按最大模块归一化）");
    bar.appendChild(seg);
    const num = document.createElement("div"); num.className="num"; num.textContent=fmt(m.size);
    row.appendChild(name); row.appendChild(bar); row.appendChild(num);
    root.appendChild(row);
  }

  const table = document.getElementById("module-table");
  table.innerHTML = "<thead><tr><th data-k='name'>模块</th><th data-k='size' class='num'>实际占用</th>"+
                    "<th data-k='link_total' class='num'>输入节区合计</th><th>主要类型</th></tr></thead>";
  const tb = document.createElement("tbody");
  for(const m of mods){
    const tr = document.createElement("tr");
    const dominant = Object.entries(m.types).sort((a,b)=>b[1]-a[1])[0];
    tr.innerHTML = "<td class='mono'>"+esc(m.name)+"</td>"+
      "<td class='num mono'>"+hex(m.size)+"</td>"+
      "<td class='num mono'>"+hex(m.link_total)+"</td>"+
      "<td>"+(dominant?esc(dominant[0])+" "+fmt(dominant[1]):"—")+"</td>";
    tb.appendChild(tr);
  }
  table.appendChild(tb);
}

/* ---------- section table ---------- */
let secSort = {key:"size", dir:-1};
function renderSections(filter){
  const q = (filter||"").toLowerCase();
  let rows = DATA.sections.filter(s=>!q ||
    s.name.toLowerCase().includes(q) || s.module.toLowerCase().includes(q) ||
    s.chip.toLowerCase().includes(q) || (s.chip_display||"").toLowerCase().includes(q) ||
    s.type.toLowerCase().includes(q));
  rows = rows.slice().sort((a,b)=>{
    const k = secSort.key;
    const va = a[k], vb = b[k];
    if(typeof va === "string") return va.localeCompare(vb)*secSort.dir;
    return (va-vb)*secSort.dir;
  });
  const table = document.getElementById("section-table");
  table.innerHTML = "<thead><tr>"+
    ["name","chip","addr","size","type","module"].map(k=>{
      const label = {name:"节区",chip:"内存",addr:"地址",size:"大小",type:"类型",module:"模块"}[k];
      const cls = (k==="addr"||k==="size") ? " class='num'" : "";
      return "<th data-k='"+k+"'"+cls+">"+label+"</th>";
    }).join("")+"</tr></thead>";
  const tb = document.createElement("tbody");
  for(const s of rows){
    const tr = document.createElement("tr");
    tr.innerHTML = "<td class='mono'>"+esc(s.name)+"</td>"+
      "<td>"+esc(s.chip_display || s.chip)+"</td>"+
      "<td class='num mono'>"+hex(s.addr)+"</td>"+
      "<td class='num mono'>"+hex(s.size)+"</td>"+
      "<td><i class='dot' style='background:"+(COLORS[s.type]||COLORS.Other)+"'></i> "+esc(s.type)+"</td>"+
      "<td class='mono'>"+esc(s.module)+"</td>";
    tb.appendChild(tr);
  }
  table.appendChild(tb);
  table.querySelectorAll("th").forEach(th=>{
    th.onclick = () => {
      const k = th.dataset.k;
      secSort = {key:k, dir: secSort.key===k ? -secSort.dir : (k==="size"||k==="addr"?-1:1)};
      renderSections(document.getElementById("section-search").value);
    };
  });
}

/* ---------- footer ---------- */
function renderFooter(){
  const c = DATA.config;
  document.getElementById("footer").innerHTML =
    "<div class='kv'>"+
    "<div>tick: <b>"+esc(c.tick ?? "—")+" Hz</b></div>"+
    "<div>最大优先级: <b>"+esc(c.max_prio ?? "—")+"</b></div>"+
    "<div>最小栈深: <b>"+esc(c.min_stack ?? "—")+" words</b></div>"+
    "<div>抢占: <b>"+esc(c.preemption || "—")+"</b></div>"+
    "<div>栈溢出检查: <b>"+esc(c.stack_check || "—")+"</b></div>"+
    "<div>软件定时器: <b>"+esc(c.timers || "—")+"</b></div>"+
    "</div><div style='margin-top:10px'>数据源: "+esc(DATA.meta.map)+"<br>LSL: "+esc(DATA.meta.lsl)+
    "<br>说明: 「实际占用」按实际放置节区汇总；「输入节区合计」为链接器 Link Result 中的目标文件贡献，可能包含被回收的节区。</div>";
}

/* ---------- events ---------- */
document.getElementById("theme-toggle").onclick = () => {
  const r = document.documentElement;
  r.dataset.theme = r.dataset.theme === "dark" ? "light" : "dark";
};
document.getElementById("module-search").oninput = e => renderModules(e.target.value);
document.getElementById("section-search").oninput = e => renderSections(e.target.value);

const tooltip = document.getElementById("tooltip");
document.addEventListener("mousemove", e => {
  const t = e.target.closest("[data-tip]");
  if(t){
    tooltip.textContent = t.dataset.tip;
    tooltip.style.display = "block";
    const x = Math.min(e.clientX + 14, window.innerWidth - 430);
    const y = Math.min(e.clientY + 14, window.innerHeight - 120);
    tooltip.style.left = x + "px"; tooltip.style.top = y + "px";
  } else {
    tooltip.style.display = "none";
  }
});

/* ---------- boot ---------- */
renderCards();
renderLegend();
renderOverview();
renderCoreAffinity();
renderTypes();
renderSplit();
renderModules("");
renderSections("");
renderFooter();
</script>
</body>
</html>
"""


def render(data: dict) -> str:
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    return HTML.replace("__DATA__", payload)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate an HTML memory report from a TASKING map")
    parser.add_argument("--project", default=None, help="project root")
    parser.add_argument("--config", default=None, help="build configuration (default: Debug)")
    parser.add_argument("--output", default=None, help="output html path")
    parser.add_argument("--open", action="store_true", help="open in browser")
    args = parser.parse_args()

    cfg_path = HERE.parent / "config.json"
    cfg = json.loads(cfg_path.read_text(encoding="utf-8")) if cfg_path.exists() else {}
    project = Path(args.project or cfg.get("project", {}).get("path", "."))
    config = args.config or cfg.get("project", {}).get("build_config", "Debug")
    map_name = cfg.get("artifacts", {}).get("map", "FreeRTOS.map")

    map_path = project / config / map_name
    if not map_path.exists():
        print(f"[report] map 不存在: {map_path}", file=sys.stderr)
        return 2

    data = build_data(project, config)
    html = render(data)

    out = Path(args.output) if args.output else project / "Reports" / "FreeRTOS_memory_report.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")

    s = data["summary"]
    print("=" * 66)
    print("TC397 内存报告已生成")
    print("=" * 66)
    print(f"输出: {out}")
    print(f"PFlash : {s['flash_used']:#x} / {s['flash_total']:#x}  ({s['flash_used']*100/s['flash_total']:.1f}%)")
    print(f"DSPR   : {s['dsp_used']:#x} / {s['dsp_total']:#x}  ({s['dsp_used']*100/s['dsp_total']:.1f}%)")
    print(f"RAM    : {s['ram_used']:#x} / {s['ram_total']:#x}  ({s['ram_used']*100/s['ram_total']:.1f}%)")
    print(f"CSA    : {s['csa_total']:#x}（每核 {s['csa_entries']} 个）")
    print(f"Heap   : config={s['heap_config']} actual={s['heap_actual']}")
    print(f"节区 {len(data['sections'])} 个，模块 {len(data['modules'])} 个")

    if args.open:
        webbrowser.open(out.resolve().as_uri())
    return 0


if __name__ == "__main__":
    sys.exit(main())
