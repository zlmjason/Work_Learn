# aurix-build-analyze 详细说明

## 1. 设计目标

ADS（Eclipse）工程的构建产物包含三类关键文件：

| 文件 | 内容 | 能回答的问题 |
|---|---|---|
| `.map` | 链接器的完整决策记录：命令行、内存使用、节区布局、符号地址、交叉引用、调用图 | 东西放到哪了？有没有溢出/重叠？某个符号是否存在？被谁引用？ |
| `.elf` | 可执行文件：ELF 头（入口/机器）、节区表、符号表 | 入口对不对？节区地址/大小与 map 是否一致？ |
| `.hex` | 烧录镜像（Intel HEX） | 校验和正确吗？地址覆盖与 ELF 一致吗？有没有缺 EOF？ |

分析器的核心思路：**不信任单一文件，做交叉验证**。

```text
源码时间  ──对比──►  ELF 时间        （是否陈旧）
map 符号  ──对比──►  ELF 入口        （入口一致）
map 布局  ──校验──►  地址/大小/对齐   （无重叠、不越界）
map 配置  ──对比──►  FreeRTOSConfig  （堆大小一致）
hex       ──校验──►  ELF 可加载范围   （覆盖一致）
map 交叉引用 ──────►  Port 接线      （SYSCALL hook 是否生效）
```

## 2. 编译模式详解

### 2.1 headless（推荐）

```bash
py -3 scripts/build.py --mode headless --analyze
```

内部执行的命令：

```text
AURIX-studioc.exe --launcher.ini <ADS>/AURIX-studio-headless.ini -nosplash \
  -application org.eclipse.cdt.managedbuilder.core.headlessbuild \
  -data <workspace> \
  -build FreeRTOS/Debug
```

`build.py` 自动处理两个 ADS 兼容问题：

| 问题 | 自动处理 |
|---|---|
| `AURIX-studio.ini` 强制注入 `-perspective com.infineon.aurix.buildmanager.perspective.c`，headless 应用拒绝该参数 | 生成 `AURIX-studio-headless.ini`（去掉这两行），用 `--launcher.ini` 指定 |
| `BoosterBuilder` 依赖 `org.eclipse.cdt.ui`，无头模式无 Workbench，构建抛 `Workbench has not been created yet` | 构建期间临时从 `.project` 移除该 builder，结束后自动恢复 |

- `--clean` 时改为 `-cleanBuild FreeRTOS/Debug`
- 运行前检查：
  1. `AURIX-studio.exe` 是否在运行（`tasklist`）→ 在运行则直接返回可操作提示
  2. 输出中是否出现 `Workspace already in use` → 提示关闭 ADS / 删除 `.lock`
- 成功判据：退出码 0 且三件产物存在且非空
- 实测耗时：全量 clean 构建约 2m30s（TC397 工程，`-O0`）

### 2.2 make（需商业许可）

```bash
py -3 scripts/build.py --mode make --clean
```

- 前置：在 ADS 中至少构建过一次，生成 `Debug/makefile`
- 环境：把 `toolchain_bin` 与 `make` 目录加入 `PATH`
- 只构建 `FreeRTOS.elf` 目标，跳过 `secondary-outputs`（`elfsize` 受非商业许可限制）
- 检测到 `F104` / `does not support running as standalone` 时返回退出码 2 并给出替代方案

### 2.3 auto

先 headless；若因环境受阻（退出码 2）直接返回，不再尝试 make（避免误导）。其他错误则回退 make 再试一次。

## 3. 检查项定义

### 3.1 产物

| 检查 | 规则 | 严重度 |
|---|---|---|
| 文件存在 | `.elf/.map/.hex` 均存在且非空 | fail |
| 产物同批 | 三件产物 mtime 差 ≤ `freshness_tolerance_sec` | warn |
| 源码新鲜度 | 应用层 `.c/.h`（排除 `Debug/`、`Libraries/`）不得比 ELF 新 | fail |

> 源码新鲜度是最实用的一项：它直接回答"我烧进去的是不是最新代码"。

### 3.2 构建

| 检查 | 规则 |
|---|---|
| 器件宏 | 链接参数包含 `__CPU__=tc39xb` |
| LSL 文件 | 参数中包含 `--lsl-file=` 或 `-d<file>.lsl` |

### 3.3 内存（Used Resources）

对每个 `mpe:*` 区域：

```text
code + data + reserved <= total
free >= min_free_memory_bytes（仅对有 code/data 的区域）
```

纯预留区（`mpe:dfls0`）不参与余量检查。

### 3.4 布局（Locate Result → Sections）

- 同一 memory chip 内按 `space_addr` 排序后，任意相邻节区满足
  `addr[i] + size[i] <= addr[i+1]`
- 每个节区满足 `space_addr % align == 0`

### 3.5 栈与 CSA

- `csa_tc0..csa_tc5` 存在，大小默认 `0x2000`（512 个 64B CSA）
- `ustack_tcN` / `istack_tcN` 存在且大小非 0
- core0 顺序：`ustack < istack < csa`（地址递增）

### 3.6 符号

必备符号（可在 `config.json` 调整）：

```text
_START, core0_main,
vPortSyscallHandler, vPortSystemContextHandler, vPortSystemTickHandler,
vPortEnterCritical, vPortExitCritical, vTaskSwitchContext
```

可选（可能被内联/裁剪）：`vPortStartFirstTask`, `vPortReclaimCSA`。

### 3.7 Port 接线（本项目最有价值的一项）

两个条件同时满足才算通过：

1. map 的 Cross References 中，`vPortSyscallHandler` 的 `Referenced in` 包含 `IfxCpu_Trap.o`
2. `Configurations/Ifx_Cfg.h` 定义了 `IFX_CFG_CPU_TRAP_SYSCALL_CPU0_HOOK` 且指向 `vPortSyscallHandler`

**背景**：S0 阶段真实故障——缺少 hook 时，`portYIELD()` 的 syscall trap 变成空操作，Tmr Svc 空转独占 CPU，应用任务永远不运行。编译、链接、tick 全部正常，只有运行时表现为「任务不跑」。这项检查能在构建阶段就抓住它。

### 3.8 配置一致性

- 解析 `Configurations/FreeRTOSConfig.h` 的 `#define`
- `configTOTAL_HEAP_SIZE` 必须等于 map 中 `ucHeap` 节区大小
- 输出 tick 频率、优先级数、最小栈深、抢占/定时器开关等信息

### 3.9 ELF

- `e_machine`（TriCore = 0x2C）
- ELF `e_entry` 必须等于 map 的 `_START`
- 统计 `.text` / `.data/.bss` 节区数量与总量

### 3.10 HEX

- 每条记录的校验和：所有字节求和后低 8 位为 0
- 必须存在 EOF（type 01）记录
- 数据地址范围应落在 ELF 可加载节区范围内
- 报告起始地址（type 05，通常 `0xa0000000`）

### 3.11 核归属（TC3xx 多核布局）

**规则**：

| 对象 | 应放位置 |
|---|---|
| Core N 的代码 | `PFLSN` 或 `PSPRN`（PSPR = 快速代码） |
| Core N 的数据 | `DSRPN` 或 `CPUN_DLMU`（DSPR = 快速数据） |
| 共享数据 | `LMU` 优先；DSPR/DLMU 仅作快速路径或单核设计例外 |

**归属判定**（按优先级）：

1. 模块名：`CpuN_Main.o`、`Ifx_Ssw_TcN.o`
2. 节区名 / 组名：`ustack_tcN`、`istack_tcN`、`csa_tcN`、`__CoreN_start`

**排除项**（避免误报）：

- `IfxCpu_Trap.*`：共享 trap 基础设施，其每核部分在 `IfxCpu_Trap_vectorTableN`；trap 代码本身跨 bank 放置可接受。
- `[.data...]`：ROM 拷贝镜像（初始化数据的 Flash 加载映像），放在 PFlash 是正确设计，不算"数据放错"。

**状态分级**：

| 情况 | 状态 |
|---|---|
| 核代码/数据放到别的核的私有区 | ❌ fail |
| 共享数据位于核私有 RAM（如 DSRAM0） | ⚠️ warn：单核/快速路径可接受；多核共享应迁移到 LMU |
| 共享数据位于 LMU | ✅ pass |
| PSPR 中有快速代码 / DSPR 中有快速数据 | ℹ️ info（正常用法） |

输出示例：

```text
[核归属]
  ✅ Core 0: code=PFLS0, data=DSRAM0
  ...
  ⚠️ 共享数据 → 核私有 RAM: 0x9251 位于 DSRAM0=0x9251；单核或快速路径可接受，多核共享应迁移到 LMU
  ℹ️ PSPR 快速代码: 0x0（未使用）
  ℹ️ DSPR 快速数据: 0x19a55（含 CSA/栈/Heap）
```

## 4. 配置字段（config.json）

| 字段 | 含义 |
|---|---|
| `project.path` | 工程根目录（含 `Debug/`） |
| `project.workspace` | Eclipse workspace（含 `.metadata/`） |
| `project.eclipse_project` | Eclipse 工程名（`.project` 中的 name） |
| `project.build_config` | 构建配置目录名，如 `Debug` |
| `project.ads_exe` | `AURIX-studioc.exe` 路径 |
| `project.make` | ADS 自带 `make.exe` 路径 |
| `project.toolchain_bin` | TASKING `cctc/ltc` 所在目录 |
| `artifacts` | 三件产物文件名 |
| `expected.device_macro` | 期望的器件宏 |
| `expected.entry_symbol` | 入口符号名（默认 `_START`） |
| `expected.csa_size_bytes` | 每核 CSA 区大小 |
| `expected.csa_cores` | 需要检查的核编号 |
| `expected.required_symbols` | 必须具备的符号 |
| `expected.freertos_symbols` | FreeRTOS 关键符号 |
| `expected.trap_reference` | Port 接线检查的符号与引用方 |
| `thresholds.freshness_tolerance_sec` | 三件产物时间差容限 |
| `thresholds.min_free_memory_bytes` | 内存余量告警阈值 |

## 5. 输出与退出码

- 人类可读：按分组打印 ✅/⚠️/❌/ℹ️
- `--json`：输出 `{checks, summary, data}`
- `--strict`：警告也视为失败
- 退出码：`0` 通过；`1` 失败；`2` 环境受阻

## 6. 移植到其他工程

1. 修改 `config.json` 的 `project.*` 与 `artifacts`
2. 调整 `expected.required_symbols`（不同 port/内核版本符号略有差异）
3. 若没有 CSA（Cortex-M 工程），把 `csa_cores` 设为空并关闭相关检查
4. 先用 `analyze.py` 跑一次，确认 map 格式兼容；TASKING 不同版本的表格列可能略有差异

## 7. HTML 内存可视化报告

```bash
py -3 scripts/report_html.py --open
# 指定输出
py -3 scripts/report_html.py --output D:/reports/mem.html
```

默认输出：`<project>/Reports/FreeRTOS_memory_report.html`（自包含，无外部依赖，可离线打开）。

**四个视角**：

| 视角 | 内容 | 数据来源 |
|---|---|---|
| 内存总览 | 按四个独立分组展示：**Flash** → **DSPR & PSPR** → **CPUx DLMU** → **LMU**；每个区域显示名称、地址范围、已用/空闲（按段类型堆叠） | Used Resources + Locate Result + LSL |
| 段类型分布 | Code / RO Data / Data / BSS / Heap / CSA / UStack / IStack / Vector / Reserved 的占比（环形图） | Locate Result 节区聚合 |
| 模块占用 | 目标文件（tasks.o / port.o / iLLD / linker-LSL）的实际占用与输入节区合计 | Locate Result + Link Result |
| 节区明细 | 全部节区的可搜索、可排序表格（含地址） | Locate Result |

**统计口径**：
- 「实际占用」按实际放置节区汇总，与内存条一致；
- 「输入节区合计」来自 Link Result，可能包含被链接器回收的节区，故可能大于实际占用；
- **默认排除** `mpe:dfls0`（DFI 预留）、`mpe:ucb`、`mpe:edmem`；可在 `config.json` 的 `report.exclude_memories` 调整；
- 分组顺序由 `config.json` 的 `report.group_order` 控制（默认 `flash → dsp → dlmu → lmu`）；
- `Reserved` 段用于补齐 Used Resources 与节区汇总之间的差额。

**交互**：深浅色切换；模块/节区搜索；明细表按列排序；内存条悬停提示。

## 8. 典型工作流

```bash
# 日常：改完代码，关闭 ADS → 构建 + 分析
py -3 scripts/build.py --analyze

# 只怀疑链接问题时（不动代码）
py -3 scripts/analyze.py

# CI 风格：警告即失败
py -3 scripts/analyze.py --strict --json

# 生成可视化报告并打开
py -3 scripts/report_html.py --open
```
