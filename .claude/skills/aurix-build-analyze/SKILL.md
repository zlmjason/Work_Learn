---
name: aurix-build-analyze
description: 编译 AURIX TC3xx（ADS/TASKING）工程并分析链接产物（map/ELF/HEX），确保链接正确性。Trigger when the user asks to build the TC397/TC3xx project, check linker output, validate the map file, verify link correctness, or mentions "编译工程", "分析 map", "链接检查", "产物校验", "构建分析".
---

# AURIX TC3xx 构建与链接产物分析

## 用途

解决两个问题：

1. **自动化编译**：从命令行触发 ADS/TASKING 工程构建（绕开手动点 IDE）。
2. **链接准确性校验**：解析 `.map` / `.elf` / `.hex`，检查内存布局、栈与 CSA、关键符号、Port 接线、产物一致性。

## 快速开始

```bash
# 仅分析已有产物（随时可用，不依赖 IDE）
py -3 .claude/skills/aurix-build-analyze/scripts/analyze.py

# 编译后再分析（需先关闭 ADS GUI）
py -3 .claude/skills/aurix-build-analyze/scripts/build.py --analyze

# 只做链接检查，严格模式（警告也算失败）
py -3 .claude/skills/aurix-build-analyze/scripts/analyze.py --strict

# 机器可读输出
py -3 .claude/skills/aurix-build-analyze/scripts/analyze.py --json

# 生成 HTML 内存可视化报告并在浏览器打开
py -3 .claude/skills/aurix-build-analyze/scripts/report_html.py --open
```

## 两种构建设式

| 模式 | 命令 | 前提 | 说明 |
|---|---|---|---|
| `headless`（推荐） | `build.py --mode headless` | **ADS GUI 必须关闭** | 走 Eclipse 无头构建，在 IDE 进程内运行，非商业许可可用 |
| `make` | `build.py --mode make` | 需商业 TASKING 许可 | 直接调 make；非商业许可会报 `F104` |

`--mode auto`（默认）优先 headless。

`build.py` 会自动处理 ADS 的两个无头兼容问题（启动器注入 `-perspective`、BoosterBuilder 依赖 CDT UI），无需手工改配置；详见 `gotchas.md` 第 10、11 条。

## 检查项一览

| 分组 | 检查 |
|---|---|
| 产物 | 三件产物存在、同批生成、源码是否比 ELF 新（防止烧录陈旧产物） |
| 构建 | 链接器版本、器件宏 `tc39xb`、LSL 文件 |
| 内存 | 各内存区域 Code+Data+Reserved ≤ Total、余量 |
| 布局 | 节区地址重叠、对齐 |
| 栈与 CSA | 每核 `ustack/istack/csa` 大小与布局顺序 |
| 符号 | 必备符号、FreeRTOS 符号、入口符号 |
| **Port 接线** | `vPortSyscallHandler` 是否被 `IfxCpu_Trap.o` 引用（可捕获 S0 那类"yield 变空操作"故障） |
| **核归属** | 各核代码是否在本核 PFLS/PSPR、数据是否在本核 DSRAM/DLMU；共享数据是否在 LMU；PSPR/DSPR 快速路径使用情况 |
| 配置 | `configTOTAL_HEAP_SIZE` 与实际 `ucHeap` 一致；tick/优先级等 |
| ELF | 入口点与 map `_START` 一致、节区统计 |
| HEX | 记录校验和、EOF、地址覆盖 |

退出码：`0` 通过；`1` 有失败；`2` 构建环境受阻（workspace 锁定 / 许可限制）。

## 配置

默认路径在 `config.json`，可用 CLI 覆盖：

```bash
py -3 .../analyze.py --project "D:/other_project" --config Release
py -3 .../build.py --project "D:/other_project" --config Release
```

## 配套文件

| 文件 | 用途 |
|---|---|
| `reference.md` | map/ELF/HEX 解析细节、检查项定义、配置字段 |
| `gotchas.md` | 许可限制、workspace 锁、陈旧产物、解析陷阱 |
| `config.json` | 项目路径、产物名、期望符号与阈值 |
| `scripts/build.py` | 编译入口 |
| `scripts/analyze.py` | 产物分析入口 |
| `scripts/report_html.py` | 生成自包含 HTML 内存可视化报告 |

## 关联

- 工程：`C:\Users\11064\Desktop\TC397_Platform_Jason\ADS\FreeRTOS`（TC397 + FreeRTOS V10.5.1 + TASKING port）
- 学习路线：知识库 `02_Middleware_中间件层/02_FreeRTOS/FreeRTOS_00_总体学习与实践方案.md`
- Port 深潜：`FreeRTOS_Port_TC3xx_PortLayer_Full_Walkthrough.md`
