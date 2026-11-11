# FreeRTOS ARM Cortex-M7 Port（官方 V10.5.1）

## 来源

- 上游仓库：`FreeRTOS/FreeRTOS-Kernel`
- Tag：`V10.5.1`
- 官方路径：
  - `portable/GCC/ARM_CM7/r0p1/`
  - `portable/IAR/ARM_CM7/r0p1/`
- 官方页面：https://github.com/FreeRTOS/FreeRTOS-Kernel/tree/V10.5.1/portable/GCC/ARM_CM7/r0p1

## 下载说明

直连 `raw.githubusercontent.com` 时连接被重置，改用官方 tag 的镜像/压缩包通道获取：

- `https://codeload.github.com/FreeRTOS/FreeRTOS-Kernel/zip/refs/tags/V10.5.1`
- 镜像：`https://cdn.jsdelivr.net/gh/FreeRTOS/FreeRTOS-Kernel@V10.5.1/...`

文件头已核对为 `FreeRTOS Kernel V10.5.1`，协议为 MIT（见 `LICENSE.md`）。

校验值（SHA-256）：

```text
kernel.zip                                 3a3ceec6ef5a5ce14eb79eaa7df623f1ed0bc19ae73fddcf54fd2df2e4dae5c0
GCC/ARM_CM7/r0p1/port.c                    ed3868ee6c8e1c8f6645a3e03b9de3aaf3aca28417321f5d324420f9c1b736fc
GCC/ARM_CM7/r0p1/portmacro.h               df927dd0711b4846b47c858a456715d828dcbfdcd5e195e1903398db7fdb5166
```

## 目录

```text
FreeRTOS_ARM_CM7_Port_V10.5.1/
├── LICENSE.md
├── README.md
└── portable/
    ├── GCC/ARM_CM7/
    │   ├── ReadMe.txt
    │   └── r0p1/
    │       ├── port.c
    │       └── portmacro.h
    └── IAR/ARM_CM7/
        ├── ReadMe.txt
        └── r0p1/
            ├── port.c
            ├── portasm.s
            └── portmacro.h
```

## 关键文件

### GCC

V10.5.1 的 GCC ARM_CM7 port 只有 `port.c` + `portmacro.h`，SVC/PendSV/SysTick 的处理函数都在 `port.c` 里用内联汇编实现：

- `pxPortInitialiseStack`
- `xPortStartScheduler`
- `vPortSVCHandler` → `prvPortStartFirstTask`
- `xPortPendSVHandler`
- `xPortSysTickHandler`
- `vPortEnterCritical` / `vPortExitCritical`
- `vPortSetupTimerInterrupt`
- `vPortEnableVFP`（FPU 上下文）

### IAR

IAR 版把汇编拆到 `portasm.s`，更适合和 TriCore 的汇编 port 对照：

- `port.c`：C 侧初始化、临界区、Tick 逻辑
- `portasm.s`：`vPortSVCHandler`、`xPortPendSVHandler`、`xPortSysTickHandler`、`prvPortStartFirstTask`
- `portmacro.h`：寄存器/临界区/EXC_RETURN 相关宏

## 与本地 TriCore Tasking port 对照

本地 TriCore port：

```text
C:\Users\11064\Desktop\TC397_Platform_Jason\ADS\FreeRTOS\OS\FreeRTOS\portable\Tasking\TC3\port.c
C:\Users\11064\Desktop\TC397_Platform_Jason\ADS\FreeRTOS\OS\FreeRTOS\portable\Tasking\TC3\portmacro.h
```

| 功能 | ARM Cortex-M7（GCC） | TriCore TC3xx（Tasking） |
|---|---|---|
| 任务栈初始化 | `pxPortInitialiseStack` | `pxPortInitialiseStack` |
| 启动第一个任务 | `vPortSVCHandler` → `prvPortStartFirstTask` | `vPortStartFirstTask`（SYSCALL trap） |
| 上下文切换 | `xPortPendSVHandler` | `vPortSystemContextHandler` / `vPortSaveContext` / `vPortLoadContext` |
| 主动让出 | `portYIELD()` → PendSV | `vPortSyscallYield`（SYSCALL trap） |
| Tick | `xPortSysTickHandler` | `vPortSystemTickHandler` |
| 临界区 | `vPortEnterCritical` / `vPortExitCritical`（BASEPRI） | `vPortEnterCritical` / `vPortExitCritical`（ICR.IE） |
| 首次上下文源 | SVC + `xPortStartScheduler` | `vPortInitContextSrc` + `vPortStartFirstTask` |
| CSA / 栈回收 | 无 CSA；硬件异常栈帧自动恢复 | `vPortReclaimCSA` |
| FPU | `vPortEnableVFP` + lazy stacking | 无同名函数；浮点上下文随 Upper/Lower Context |

## 用途

- 和 TriCore 的 `port.c` 逐函数对照，理解“硬件 CSA 链”与“M7 硬件栈帧”的差异。
- 作为后续 `FreeRTOS_ExecutionModel_ARM_M7_Runtime_Model.md` 的代码索引。
- 不要直接拿本目录编译；编译需要完整的 FreeRTOS Kernel 源码与对应启动文件/链接脚本。
