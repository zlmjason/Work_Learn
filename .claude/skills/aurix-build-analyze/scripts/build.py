#!/usr/bin/env python3
"""Build an ADS/TASKING AURIX project from the command line.

Two modes are supported:

* headless : Eclipse/CDT headless build through AURIX-studioc.exe.  This runs
             inside the IDE process, so it works with the non-commercial
             TASKING licence.  The ADS GUI must be closed (workspace lock).
* make     : invoke the generated makefile directly.  Requires a TASKING
             licence that permits standalone execution (commercial licence);
             the free/non-commercial licence fails with F104.

Usage:
    py -3 build.py [--mode auto|headless|make] [--project DIR] [--config Debug]
                   [--clean] [--analyze] [--json]
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_CONFIG: dict = {
    "project": {
        "path": "C:/Users/11064/Desktop/TC397_Platform_Jason/ADS/FreeRTOS",
        "workspace": "C:/Users/11064/Desktop/TC397_Platform_Jason/ADS",
        "eclipse_project": "FreeRTOS",
        "build_config": "Debug",
        "ads_exe": "C:/Infineon/AURIX-Studio-1.7.2/AURIX-studioc.exe",
        "make": "C:/Infineon/AURIX-Studio-1.7.2/plugins/com.infineon.aurix.tools_1.7.2/build_system/tools/make/make.exe",
        "toolchain_bin": "C:/Infineon/AURIX-Studio-1.7.2/plugins/com.infineon.aurix.tools_1.7.2/build_system/tools/Compilers/Tasking_1.1r8/ctc/bin",
    },
    "artifacts": {"elf": "FreeRTOS.elf", "map": "FreeRTOS.map", "hex": "FreeRTOS.hex"},
    "build": {"jobs": 8, "timeout_sec": 900},
}


def load_config(project: str | None, config: str | None) -> dict:
    cfg = json.loads(json.dumps(DEFAULT_CONFIG))
    cfg_file = HERE.parent / "config.json"
    if cfg_file.exists():
        user = json.loads(cfg_file.read_text(encoding="utf-8"))
        for key, value in user.items():
            if isinstance(value, dict) and isinstance(cfg.get(key), dict):
                cfg[key].update(value)
            else:
                cfg[key] = value
    if project:
        cfg["project"]["path"] = project
    if config:
        cfg["project"]["build_config"] = config
    return cfg


def ads_process_running() -> bool:
    """Best-effort check for a running ADS GUI on Windows."""
    if os.name != "nt":
        return False
    try:
        out = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq AURIX-studio.exe", "/NH"],
            capture_output=True,
            text=True,
            timeout=15,
        ).stdout
        return "AURIX-studio.exe" in out
    except Exception:
        return False


def run(cmd: list[str], cwd: Path, env: dict | None = None, timeout: int = 900) -> tuple[int, str]:
    print(f"[build] $ {' '.join(cmd)}")
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(cwd),
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
        output = (proc.stdout or "") + (proc.stderr or "")
        return proc.returncode, output
    except FileNotFoundError as exc:
        return 127, f"命令不存在: {exc}"
    except subprocess.TimeoutExpired as exc:
        return 124, f"构建超时（{timeout}s）: {exc}"


def ensure_headless_ini(ads: Path) -> Path:
    """Create a launcher ini without ADS's injected -perspective argument.

    AURIX-studio.ini contains:
        -perspective
        com.infineon.aurix.buildmanager.perspective.c
    The CDT headless-build application rejects -perspective, so the launcher
    must be pointed at a copy without those two lines.
    """
    src = ads.parent / "AURIX-studio.ini"
    dst = ads.parent / "AURIX-studio-headless.ini"
    if not src.exists():
        return src
    if not dst.exists() or dst.stat().st_mtime < src.stat().st_mtime:
        text = src.read_text(encoding="utf-8", errors="replace")
        text = re.sub(r"(?m)^-perspective\s*\n.*\n", "", text)
        dst.write_text(text, encoding="utf-8")
    return dst


BOOSTER_RE = re.compile(
    r"\s*<buildCommand>\s*<name>com\.infineon\.aurix\.buildsystem\.builders\.booster</name>.*?</buildCommand>",
    re.S,
)


@contextmanager
def booster_disabled(project: Path):
    """Temporarily drop the Infineon BoosterBuilder from .project.

    BoosterBuilder depends on org.eclipse.cdt.ui (CUIPlugin), whose activator
    requires a Workbench.  In headless mode CUIPlugin.start() throws
    "Workbench has not been created yet" and the whole build fails with exit 13.
    The builder is irrelevant to compilation, so it is removed for the duration
    of the build and restored afterwards.
    """
    project_file = project / ".project"
    backup = project / ".project.headless-bak"
    if not project_file.exists():
        yield False
        return
    original = project_file.read_text(encoding="utf-8", errors="replace")
    if not BOOSTER_RE.search(original):
        yield False
        return
    shutil.copy2(project_file, backup)
    try:
        project_file.write_text(BOOSTER_RE.sub("", original), encoding="utf-8")
        print("[build] 已临时移除 BoosterBuilder（无头模式不兼容 CDT UI）")
        yield True
    finally:
        if backup.exists():
            shutil.move(str(backup), str(project_file))
            print("[build] .project 已恢复")


def build_headless(cfg: dict, clean: bool) -> tuple[int, str]:
    p = cfg["project"]
    ads = Path(p["ads_exe"])
    if not ads.exists():
        return 127, f"ADS 可执行文件不存在: {ads}"

    workspace = Path(p["workspace"])
    if not workspace.exists():
        return 127, f"workspace 不存在: {workspace}"

    if ads_process_running():
        return 2, (
            "检测到 ADS GUI 正在运行，workspace 被锁定，无头构建无法启动。\n"
            "请先关闭 AURIX Development Studio，再重试；或改用 --mode make（需商业许可）。"
        )

    ini = ensure_headless_ini(ads)
    target = f"{p['eclipse_project']}/{p['build_config']}"
    cmd = [
        str(ads),
        "--launcher.ini",
        str(ini),
        "-nosplash",
        "-application",
        "org.eclipse.cdt.managedbuilder.core.headlessbuild",
        "-data",
        str(workspace),
    ]
    if clean:
        cmd += ["-cleanBuild", target]
    else:
        cmd += ["-build", target]

    project = Path(p["path"])
    with booster_disabled(project):
        code, out = run(cmd, cwd=workspace, timeout=cfg["build"]["timeout_sec"])

    if "Workspace already in use" in out:
        return 2, (
            "workspace 已被占用（Workspace already in use）。\n"
            "请关闭 ADS 后重试；若 ADS 已关闭仍报错，删除 "
            f"{workspace / '.metadata' / '.lock'} 后重试。"
        )
    if "Workbench has not been created yet" in out:
        return 2, (
            "无头构建被 CDT UI 依赖阻断（BoosterBuilder 未能禁用）。\n"
            "请确认 .project 中存在 com.infineon.aurix.buildsystem.builders.booster 并可写。"
        )
    return code, out


def build_make(cfg: dict, clean: bool) -> tuple[int, str]:
    p = cfg["project"]
    project = Path(p["path"])
    debug_dir = project / p["build_config"]
    make_exe = Path(p["make"])
    toolchain = Path(p["toolchain_bin"])

    if not debug_dir.exists():
        return 127, f"构建目录不存在: {debug_dir}（请先在 ADS 中生成 makefile）"
    if not make_exe.exists():
        return 127, f"make 不存在: {make_exe}"
    if not toolchain.exists():
        return 127, f"TASKING 工具链目录不存在: {toolchain}"

    env = os.environ.copy()
    env["PATH"] = str(toolchain) + os.pathsep + str(make_exe.parent) + os.pathsep + env.get("PATH", "")

    output = ""
    if clean:
        code, out = run([str(make_exe), "clean"], cwd=debug_dir, env=env, timeout=cfg["build"]["timeout_sec"])
        output += out
        if code != 0:
            return code, output

    # 'FreeRTOS.elf' skips the secondary elfsize target, which is blocked by the
    # non-commercial standalone licence anyway.
    elf_target = cfg["artifacts"]["elf"]
    code, out = run(
        [str(make_exe), f"-j{cfg['build']['jobs']}", elf_target],
        cwd=debug_dir,
        env=env,
        timeout=cfg["build"]["timeout_sec"],
    )
    output += out

    if "F104" in output or "does not support running as standalone" in output:
        return 2, output + (
            "\n\n[结论] 当前 TASKING 许可证不允许脱离 IDE 独立编译。\n"
            "请使用 --mode headless（关闭 ADS 后运行），或在 ADS GUI 中执行 Build。"
        )
    return code, output


def verify_artifacts(cfg: dict) -> tuple[bool, str]:
    project = Path(cfg["project"]["path"])
    debug_dir = project / cfg["project"]["build_config"]
    missing, found = [], []
    for kind, name in cfg["artifacts"].items():
        path = debug_dir / name
        if path.exists() and path.stat().st_size > 0:
            found.append(f"{kind}={path.stat().st_size} B")
        else:
            missing.append(str(path))
    if missing:
        return False, "缺少产物: " + ", ".join(missing)
    return True, ", ".join(found)


def run_analyzer(cfg: dict, strict: bool) -> int:
    analyzer = HERE / "analyze.py"
    cmd = [sys.executable, str(analyzer), "--project", cfg["project"]["path"], "--config", cfg["project"]["build_config"]]
    if strict:
        cmd.append("--strict")
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    code, out = run(cmd, cwd=HERE, env=env, timeout=300)
    print(out)
    return code


def main() -> int:
    parser = argparse.ArgumentParser(description="Build AURIX TC3xx ADS/TASKING project")
    parser.add_argument("--mode", choices=["auto", "headless", "make"], default="auto")
    parser.add_argument("--project", help="project root")
    parser.add_argument("--config", help="build configuration (default: Debug)")
    parser.add_argument("--clean", action="store_true", help="clean before building")
    parser.add_argument("--analyze", action="store_true", help="run analyze.py after a successful build")
    parser.add_argument("--strict", action="store_true", help="pass --strict to the analyzer")
    parser.add_argument("--json", action="store_true", help="emit a JSON summary")
    args = parser.parse_args()

    cfg = load_config(args.project, args.config)

    if args.mode == "headless":
        code, out = build_headless(cfg, args.clean)
    elif args.mode == "make":
        code, out = build_make(cfg, args.clean)
    else:
        # Non-commercial licence blocks standalone make, so prefer headless.
        code, out = build_headless(cfg, args.clean)
        if code == 2 and ads_process_running():
            pass  # actionable message already returned
        elif code not in (0, 2):
            code2, out2 = build_make(cfg, args.clean)
            if code2 != 2:
                code, out = code2, out + "\n[fallback make]\n" + out2

    print(out)

    ok, detail = verify_artifacts(cfg)
    if code == 0 and not ok:
        code = 1

    if args.json:
        print(
            json.dumps(
                {
                    "mode": args.mode,
                    "exit_code": code,
                    "artifacts_ok": ok,
                    "artifacts": detail,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        print("\n" + "-" * 70)
        if code == 0:
            status = "成功"
        elif code == 2:
            status = "未执行（环境受阻）"
        else:
            status = "失败"
        print(f"构建结果: {status} (exit={code})")
        print(f"产物校验: {'✅ ' + detail if ok else '❌ ' + detail}")
        if code == 2 and ok:
            print("注意: 产物来自上一次构建，未被本次操作更新；请勿据此烧录。")

    if code == 0 and args.analyze:
        return run_analyzer(cfg, args.strict)
    return code


if __name__ == "__main__":
    sys.exit(main())
