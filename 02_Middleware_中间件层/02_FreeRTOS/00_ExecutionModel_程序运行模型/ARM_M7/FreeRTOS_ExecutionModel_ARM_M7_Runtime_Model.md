# ARM Cortex-M7 程序运行模型（FreeRTOS Port 前置学习主线）

## 核心问题

在精读/编写 FreeRTOS ARM_CM7 port 之前，必须回答：

> **Cortex-M7 的函数调用、异常进入、任务切换，在硬件上到底保存了什么、恢复了什么？MSP/PSP、CONTROL、EXC_RETURN、NVIC、FPU lazy stacking 如何协同？**

如果这些机制不清楚，port.c 里的 `pxPortInitialiseStack`、`vPortSVCHandler`、`xPortPendSVHandler` 就只是“看起来能跑的汇编”，无法判断对错。

## 结论

- 把「M7 程序运行模型」作为 TC3xx EM 的**并行主线**，先于 ARM_CM7 port 深读。
- 程序流按**三层叙事**展开：公共内核层（`xTaskCreate` ×2 → `vTaskStartScheduler`）→ 抽象 port 契约（任何平台必须履行的六条职责）→ M7 实现（`xPortStartScheduler` / SVC / PendSV / SysTick / NVIC / BASEPRI）→ 函数与汇编细节。
- 学习顺序按硬件依赖组织：**寄存器/模式 → 双栈 → 异常入口/栈帧 → EXC_RETURN → NVIC → 公共程序流 → 抽象 port 契约 → M7 实现 → Fault → 内存系统 → 对比 → 实验**。
- 主教材是 ARMv7-M ARM B1、Cortex-M7 TRM Ch2/5/6/7/8，以及官方 FreeRTOS V10.5.1 `portable/GCC/ARM_CM7/r0p1` 代码。
- 每个阶段以“能脱稿回答 + 能在调试器/QEMU 指出证据”为完成判据；最后用 8 个实验闭环。
- 实践分两阶段：先用 QEMU MPS2-AN500 看异常/栈帧/上下文切换；Cache/TCM/Trace 类实验再上实板。
- 实际入口以 `Cpu0_Main.c` 的 `xTaskCreate` ×2 + `vTaskStartScheduler()` 为锚点；从 port 层开始只按 **Cortex-M7** 讲，TriCore 只在对比章节出现，不混用。
- **源码级校正（首任务有两层）**：`prvAddNewTaskToReadyList` 在调度器启动前用 `<=` 比较优先级，两个 LED 任务同优先级（1），后创建的 LED2 会先成为 `pxCurrentTCB`。但 `vTaskStartScheduler` 随后创建 idle（0）和 timer task（`configTIMER_TASK_PRIORITY = 9`，本工程配置），timer task 优先级更高，最终 `pxCurrentTCB` 是 `Tmr Svc`。所以启动后第一个恢复的是 `Tmr Svc`；它阻塞到定时器队列后，PendSV 才切到 LED2（LED 任务中先跑 LED2）。后续流程、实验和交互台都按这个两层结论校正。

## 背景

- 建立日期：2026-11-10。
- 目标架构：ARMv7-M / Cortex-M7，不绑定具体厂商（STM32F7、NXP S32K3、i.MX RT 等均适用）。
- 本地 FreeRTOS：V10.5.1；TriCore Tasking port 已跑通，ARM_CM7 官方 port 已下载到附件区。
- 触发原因：按 TC3xx EM 的整理方式，为 M7 建立可对照、可实验的运行时模型主线。
- 现有笔记：
  - `01_Hardware_硬件层/01_Core/02_ARM_Cortex/ARM_M7_Core_Manual_Detailed_Mermaid.md`（Ch3 已覆盖编程模型/上下文/栈）
  - `01_Hardware_硬件层/01_Core/02_ARM_Cortex/ARM_M7_Core_FAULTMASK_Hardware_Mechanism_Use_Cases.md`
  - `01_Hardware_硬件层/01_Core/03_Comparison/Core_Comparison_Exception_CallStack_M7_vs_TC3xx.md`
  - `01_Hardware_硬件层/01_Core/03_Comparison/Core_Comparison_CPU_Pipeline_M7_TC3xx_Engineering.md`
- 代码附件：
  - `99_Attachments_附件/FreeRTOS_ARM_CM7_Port_V10.5.1/portable/GCC/ARM_CM7/r0p1/`
  - 同目录 `README.md` 有来源、SHA256 和 TriCore 函数对照表。

## 关键机制

### 1. 学习路线（EM0–EM12）

| 阶段 | 主题 | 主材料 | 核心问题 | 验证方式 |
|---|---|---|---|---|
| EM0 | 总图与寄存器 | ARMv7-M B1.3–B1.4；M7 TRM Ch2 | R0–R15、xPSR、CONTROL、MSP/PSP、三个 mask 寄存器各自作用？ | 画出寄存器分类图 |
| EM1 | 模式、权限与双栈 | ARMv7-M B1.3.1/B1.4.4；M7 TRM 2.2 | Thread/Handler 如何切换？Privileged/Unprivileged 如何进入？MSP/PSP 何时用哪个？ | 口头说明 + 调试器看 CONTROL |
| EM2 | 异常入口与硬件栈帧 | ARMv7-M B1.5.6/B1.5.7；DGUG 2.3 | 硬件自动压哪些寄存器？为什么是 8 个字？8 字节对齐如何做？ | 手工画出异常帧 |
| EM3 | EXC_RETURN 与异常返回 | ARMv7-M B1.5.8；M7 TRM 2.7 | 常用 EXC_RETURN 值？返回 Thread/Handler、MSP/PSP、FPU 上下文如何区分？ | 解码一个真实 EXC_RETURN |
| EM4 | NVIC、向量表、优先级 | ARMv7-M B1.5.3/B1.5.4/B1.5.12；M7 TRM Ch7 | VTOR、优先级分组、抢占、尾链、迟到如何工作？ | 对照向量表 + NVIC 寄存器 |
| EM5 | 公共程序流（平台无关） | `tasks.c`；本工程 `Cpu0_Main.c` | `xTaskCreate` ×2 → `vTaskStartScheduler` → 首任务 → `vTaskDelay` 的公共流程？`pxCurrentTCB` 如何选？idle 和 timer task 何时创建、为什么 timer task 会插队？ | 能画出 main → 内核 → port 边界的流程图 |
| EM5A | 抽象 port 契约（平台无关） | 本笔记 §2；HTML 第 9 节 | 任何 `xPortStartScheduler()` 必须保证哪六条职责？为什么内核公共代码不能自己做？违反后果是什么？ | 能脱稿列六条职责与不变量 |
| EM5B | M7 实现（平台相关） | 官方 ARM_CM7 `port.c`；HTML 第 10–12 节 | M7 用 SVC/PendSV/SysTick/NVIC/BASEPRI 如何逐条履行契约？`xPortStartScheduler` 启动前配置了什么？ | 对照 `port.c` 行号逐条讲 |
| EM6 | Fault 模型 | ARMv7-M B1.5.14；DGUG 2.4；已有 FAULTMASK 笔记 | HardFault 如何从 MemManage/BusFault/UsageFault 升级？CFSR/HFSR/MMFAR/BFAR 怎么读？ | 构造一个 fault 并读状态寄存器 |
| EM7 | 内存系统与运行时 | M7 TRM Ch5/Ch6；DGUG 2.2/4.6/4.8 | TCM、I/D Cache、Write Buffer、MPU 如何影响栈、ISR 延迟和上下文切换？ | 对照 MPU 区域 + Cache 维护 |
| EM8 | 调试与观测 | M7 TRM Ch9；ARMv7-M Part C | DWT/ITM/ETM/MTB 各看什么？如何在断点处看 MSP/PSP/EXC_RETURN/栈帧？ | 在调试器/QEMU 指出证据 |
| EM9 | 与 TriCore 正面对比 | `Core_Comparison_Exception_CallStack_M7_vs_TC3xx.md`；TC3xx EM | CSA 链 vs 硬件栈帧；BIV vs 向量表；SYSCALL vs SVC；ICR.IE vs BASEPRI | 口头对比 + 表格 |
| EM10 | 实验 | QEMU MPS2-AN500 / 实板 | SVC、PendSV、FPU、尾链、Fault 如何观察？ | 完成 E-EM-M7-01..08 |
| EM11 | 栈与容量预算 | ARMv7-M B1.5.6；官方 `port.c` | 基本帧/FPU 扩展帧多大？任务栈如何估算？中断嵌套占用哪条栈？ | 用 map/调试器算一遍 |
| EM12 | 配置与移植检查表 | ARM_CM7 `portmacro.h`；`FreeRTOSConfig.h` | `configPRIO_BITS`、`configMAX_SYSCALL_INTERRUPT_PRIORITY`、`configUSE_TASK_FPU_SUPPORT` 如何配？ | 逐项核对工程配置 |

### 2. 程序流三层叙事（对应 HTML 第 8–10 节）

| 层 | 讲什么 | 明确不出现 | HTML | 源码锚点 |
|---|---|---|---|---|
| 公共内核层（平台无关） | 两次 `xTaskCreate` 的分配/初始化/入就绪表；`vTaskStartScheduler` 创建 idle 和 timer task，再调用 `xPortStartScheduler`；`pxCurrentTCB` 选择（timer task 最终胜出） | 不讲 SVC/PendSV/SysTick，不讲 MSP/PSP | 第 8 节 | `tasks.c` L721、L816、L1026、L1954；`timers.c` L233 |
| 抽象 port 契约（平台无关） | 任何 `xPortStartScheduler()` 必须保证：周期 tick、切换触发、首任务上下文、中断屏蔽/临界区、启动不返回、平台特性 | 不出现具体异常/寄存器/指令名 | 第 9 节 | 六条职责表 + 抽象伪代码 |
| M7 实现（平台相关） | `xPortStartScheduler` 探测 NVIC 优先级位、设 PendSV/SysTick 最低、配 SysTick、开 FPU；SVC 启动首任务（`Tmr Svc`）；PendSV 切换；SysTick tick | 不混 TriCore 程序模型；TriCore 只在第 14 节对比 | 第 10–12 节 | 官方 `port.c` L290–L389、L244、L430、L489 |
| 细节与验证 | 每条汇编对应的寄存器/栈帧动作、Fault、实验 | — | 第 11–14 节 | `port.c`、ARMv7-M B1.5 |

**为什么这样分层**：公共内核知道“该跑哪个任务”，但不知道“怎么让 CPU 跑起来”；port 层的职责是把前者的决定翻译成具体平台的异常/寄存器动作。先把职责抽象出来，再看 M7 用 SVC/PendSV/SysTick 逐条履行，才不会把“汇编动作”误当成“设计目的”。

**源码级校正（首任务有两层）**：`prvAddNewTaskToReadyList` 在 `xSchedulerRunning == pdFALSE` 时执行：

```c
if( pxCurrentTCB->uxPriority <= pxNewTCB->uxPriority )
{
    pxCurrentTCB = pxNewTCB;
}
```

两个 LED 任务都是 priority 1，LED2 后创建，`<=` 成立，所以在 LED 任务中 `pxCurrentTCB` 先变成 LED2。但 `vTaskStartScheduler` 还会创建 idle（priority 0）和 timer task：

```c
/* timers.c: xTimerCreateTimerTask() 内部的创建调用（简化） */
xTaskCreate( prvTimerTask,
             configTIMER_SERVICE_TASK_NAME,   /* 默认 "Tmr Svc" */
             configTIMER_TASK_STACK_DEPTH,
             NULL,
             ( UBaseType_t ) configTIMER_TASK_PRIORITY | portPRIVILEGE_BIT,
             &xTimerTaskHandle );
```

本工程 `configTIMER_TASK_PRIORITY = 9`，高于 LED 任务的 1，因此 timer task 创建时再次替换 `pxCurrentTCB`。最终 `pxCurrentTCB = Tmr Svc`，SVC 恢复的第一个任务是 `Tmr Svc`；它阻塞在定时器队列后，PendSV 才切到 LED2。结论：**LED 任务中 LED2 先跑，但整个系统的首任务是 `Tmr Svc`**。交互台第 8 节和单步动画都按这个两层结论校正。

### 3. 与 FreeRTOS ARM_CM7 port.c 的映射

| port.c 函数/动作 | 运行模型概念 | 材料 |
|---|---|---|
| `xTaskCreate` | 分配 TCB/栈、构造初始帧、加入就绪表 | `tasks.c`；`pxPortInitialiseStack` |
| `vTaskStartScheduler` | 创建 idle（0）和 timer task（本工程 priority 9），关中断，置调度器运行，调用 `xPortStartScheduler`（平台分界点） | `tasks.c` L1954；`timers.c` L233 |
| `pxPortInitialiseStack` 构造初始栈帧 | 合成 xPSR/PC/LR/R12/R3–R0/EXC_RETURN/R4–R11（17 字）；不含 FPU 预置，FPU 由 lazy stacking 处理 | 官方 `port.c`；ARMv7-M B1.5.6 |
| `prvPortStartFirstTask` 取初始 MSP、清 CONTROL、`svc 0` | 向量表第 0 项、SVC 异常 | 官方 `port.c`；M7 TRM 2.7 |
| `vPortSVCHandler` 恢复首个任务上下文 | PSP、EXC_RETURN、Thread/PSP 返回 | 官方 `port.c`；ARMv7-M B1.5.8 |
| `xPortPendSVHandler` 保存 R4–R11，并按 EXC_RETURN bit4 条件保存 S16–S31，再切 PSP | 软件保存上下文 + PendSV 异常 | 官方 `port.c`；ARMv7-M B1.5.6 |
| `xPortSysTickHandler` 调 `xTaskIncrementTick`，必要时 pend PendSV | SysTick 异常、尾链/迟到 | 官方 `port.c`；M7 TRM Ch7 |
| `vPortEnterCritical` / `vPortExitCritical` | BASEPRI 临界区 | 官方 `portmacro.h` |
| `vPortSetupTimerInterrupt` | SysTick 重装值与时钟源 | 官方 `port.c`；M7 TRM Ch3 |
| `vPortEnableVFP` | CPACR 使能 CP10/CP11 | 官方 `port.c`；M7 TRM Ch8 |
| `vPortValidateInterruptPriority` | NVIC 优先级合法性检查 | 官方 `port.c`；M7 TRM Ch7 |
| `xPortStartScheduler`（抽象契约） | 保证 tick、切换触发、首任务上下文、临界区、启动不返回、平台特性 | 本笔记 §2；HTML 第 9 节 |
| `xPortStartScheduler`（M7） | 探测 NVIC 优先级位、设 PendSV/SysTick 最低、配 SysTick、开 FPU、`prvPortStartFirstTask` | 官方 `port.c` L290–L389 |

### 4. 检查点（能脱稿回答才算过）

1. R0–R15、xPSR、CONTROL、MSP/PSP、PRIMASK/BASEPRI/FAULTMASK 各自作用？
2. Thread/Handler 与 Privileged/Unprivileged 如何切换？`CONTROL.nPRIV/SPSEL` 如何变化？
3. 异常入口硬件自动保存哪些寄存器？为什么是 8 个字？8 字节对齐由谁保证？
4. FPU 扩展帧比基本帧多了什么？lazy stacking 在什么时候真正写入？
5. 常用 EXC_RETURN 值有哪些？如何区分返回 Thread/Handler、MSP/PSP、FPU 上下文？
6. NVIC 的向量表、优先级分组、抢占、尾链、迟到分别是什么？
7. SVC、PendSV、SysTick 在 FreeRTOS 启动、切换、Tick 中各自做什么？
8. `pxPortInitialiseStack` 构造的初始栈帧，和真实异常入口压出的帧如何对齐？
9. PendSV 为什么保存 R4–R11？R0–R3/R12/LR/PC/xPSR 由谁保存？
10. HardFault 如何从 MemManage/BusFault/UsageFault 升级？CFSR/HFSR/MMFAR/BFAR 怎么读？
11. BASEPRI、PRIMASK、FAULTMASK 的区别？FreeRTOS 临界区为什么选 BASEPRI？
12. M7 的硬件栈帧与 TriCore 的 CSA 链，本质差异是什么？
13. `xTaskCreate` 内部如何构造初始栈帧并加入就绪表？`vTaskStartScheduler` 为什么不返回？
14. 公共层：两次 `xTaskCreate` 后 `pxCurrentTCB` 为什么先变成 LED2？`vTaskStartScheduler` 又为什么把它换成 `Tmr Svc`？
15. 抽象契约：`xPortStartScheduler()` 必须保证哪六件事？为什么内核公共代码不能自己做？
16. M7 映射：M7 用哪些机制逐条履行这六条职责？`xPortStartScheduler` 在启动首任务前配置了什么？

### 5. 实践用例

| ID | 用例 | 目标 | 观察点 | 环境 |
|---|---|---|---|---|
| E-EM-M7-01 | SVC 进入/返回 | 验证异常入口/返回 | MSP/PSP、EXC_RETURN、栈帧 | QEMU |
| E-EM-M7-02 | PendSV 上下文切换 | 验证软件保存 R4–R11 | PSP、任务栈、PendSV 前后 | QEMU |
| E-EM-M7-03 | 首次任务启动 | 对比初始栈帧与真实异常帧 | `pxPortInitialiseStack` 构造的栈 | QEMU |
| E-EM-M7-04 | FPU lazy stacking | 验证扩展帧何时写入 | S0–S15、FPSCR、栈帧大小 | QEMU |
| E-EM-M7-05 | 尾链/迟到 | 验证 NVIC 优化 | 中断时间线、PendSV/SysTick | QEMU |
| E-EM-M7-06 | Fault 升级 | 验证 HardFault 与 CFSR | CFSR/HFSR/MMFAR/BFAR | QEMU |
| E-EM-M7-07 | BASEPRI vs PRIMASK | 验证临界区与中断延迟 | BASEPRI、NVIC 优先级 | QEMU/实板 |
| E-EM-M7-08 | Cache/MPU 对运行时的影响 | 验证内存系统行为 | I/D Cache、MPU 区域、栈 | 实板 |

### 6. 材料索引

- 官方 ARM_CM7 port（本地附件）：
  - `99_Attachments_附件/FreeRTOS_ARM_CM7_Port_V10.5.1/portable/GCC/ARM_CM7/r0p1/port.c`
  - `.../portmacro.h`
  - `.../README.md`（来源、SHA256、TriCore 对照表）
- 交互实验台：[ARM_M7_Exception_Stack_Interactive.html](./ARM_M7_Exception_Stack_Interactive.html)（14 节：总图、寄存器、双栈、栈帧、FPU、EXC_RETURN、NVIC、公共程序流、抽象 port 契约、M7 实现与 SVC、PendSV、SysTick、Fault、对比与实验）
- 本地 TriCore port：
  - `C:\Users\11064\Desktop\TC397_Platform_Jason\ADS\FreeRTOS\OS\FreeRTOS\portable\Tasking\TC3\port.c`
- ARMv7-M Architecture Reference Manual（DDI0403E）：
  - B1.3.1 Modes, privilege and stacks（p.???，按本地 full.md）
  - B1.4.1–B1.4.4 核心寄存器/xPSR/mask/CONTROL
  - B1.5 Exception model；B1.5.3 向量表；B1.5.4 优先级；B1.5.6 异常入口；B1.5.7 栈对齐；B1.5.8 异常返回；B1.5.12 尾链；B1.5.14 Fault
  - A2.4 Exceptions, faults and interrupts
- Cortex-M7 TRM（DDI0489F）：
  - Ch2 Programmers Model（2.2 modes、2.6 registers、2.7 exceptions）
  - Ch3 System Control；Ch4 Initialization；Ch5 Memory System；Ch6 MPU；Ch7 NVIC；Ch8 FPU；Ch9 Debug
- Cortex-M7 DGUG（DUI0646C）：
  - 2.1 Programmers model；2.2 Memory model；2.3 Exception model；2.4 Fault handling
  - 4.2 NVIC；4.4 SysTick；4.6 MPU；4.7 FPU；4.8 Cache maintenance
- Definitive Guide to Cortex-M3/M4：异常处理与 RTOS 上下文切换章节（按目录补充页码）
- 已有笔记：
  - [[ARM_M7_Core_Manual_Detailed_Mermaid]]
  - [[ARM_M7_Core_FAULTMASK_Hardware_Mechanism_Use_Cases]]
  - [[Core_Comparison_Exception_CallStack_M7_vs_TC3xx]]
  - [[Core_Comparison_CPU_Pipeline_M7_TC3xx_Engineering]]
  - [[FreeRTOS_ExecutionModel_TC3xx_Runtime_Model]]

### 7. QEMU 实践环境（第二阶段）

**结论：值得搭，但不要放在写文档之前。**

- 适合：SVC/PendSV、异常栈帧、EXC_RETURN、Fault、BASEPRI/PRIMASK。
- 不适合：Cache/TCM/Write Buffer/Trace 的精确行为；这些需要实板。
- 方案：
  1. 安装 QEMU（`qemu-system-arm`）和 GNU Arm Embedded Toolchain（`arm-none-eabi-gcc`）。
  2. 基于官方 ARM_CM7 port 搭一个 MPS2-AN500 最小 FreeRTOS demo（启动文件、链接脚本、向量表）。
  3. `qemu-system-arm -M mps2-an500 -kernel <elf> -nographic -s -S`，用 `arm-none-eabi-gdb` 观察 MSP/PSP/EXC_RETURN/栈帧。
- 预计成本：环境 30–60 分钟；最小 demo + 调试 2–4 小时。
- 如果暂时不想搭：先完成本 MD + port.c 对照，实验用例保留为待办；不影响主线。

## 应用场景

- **读 ARM_CM7 port.c**：每个函数对应到硬件异常/栈动作，不再“照抄汇编”。
- **讲清 port 设计**：按“公共层 → 抽象契约 → M7 实现”回答每个 port 函数为什么存在，而不是只背汇编。
- **调试切换**：能从 PSP/MSP、EXC_RETURN、栈帧判断上下文切换是否正常。
- **Fault 分析**：能从 CFSR/HFSR/MMFAR/BFAR 定位 HardFault。
- **栈预算**：能估算基本帧/FPU 扩展帧/中断嵌套对任务栈的影响。
- **跨架构对比**：把 M7 的硬件栈帧与 TriCore 的 CSA 链对应起来，服务多核/RTOS 面试和工程选型。

## 关联笔记

- [[FreeRTOS_ExecutionModel_TC3xx_Runtime_Model]]（AURIX 并行主线）
- [[Core_Comparison_Exception_CallStack_M7_vs_TC3xx]]（异常/调用栈对比）
- [[Core_Comparison_CPU_Pipeline_M7_TC3xx_Engineering]]（流水线对比）
- [[ARM_M7_Core_Manual_Detailed_Mermaid]]（M7 内核手册）
- [[ARM_M7_Core_FAULTMASK_Hardware_Mechanism_Use_Cases]]（FAULTMASK/异常屏蔽）
- [[FreeRTOS_00_总体学习与实践方案]]
- [[FreeRTOS_01_学习TODO]]
- [[FreeRTOS_02_实践TODO]]

## 待补充问题

1. QEMU MPS2-AN500 的最小 FreeRTOS demo 目录/构建方式需要在搭建时确认。
2. `configUSE_TASK_FPU_SUPPORT` 的取值与 lazy stacking 行为需在官方 `port.c`/`FreeRTOSConfig.h` 中逐项核对。
3. FPU 扩展帧的精确大小/对齐需按 ARMv7-M B1.5.7 核对后再写入容量预算。
4. Cache/TCM/MPU 实验需要实板；当前无 M7 板，先保留。
5. 交互 HTML 已按 14 节三层叙事落地；后续补 QEMU 实测截图/数据（SVC、PendSV、FPU、Fault）。

## 标签

#FreeRTOS #Cortex-M7 #ARMv7-M #程序运行模型 #异常 #PendSV #EXC_RETURN #Port前置 #学习路线

## Agent 整理记录

- 2026-11-12 按用户要求把程序流改为三层叙事（公共内核 → 抽象 port 契约 → M7 实现），交互台扩为 14 节；依据 `tasks.c` 的 `<=` 和 `timers.c` 的 timer task 创建路径校正首任务为 `Tmr Svc`（LED 任务中 LED2 先跑）；TriCore 仅保留在对比节。
- 2026-11-10 创建。依据用户要求，按 TC3xx EM 的结构建立 M7 并行主线；材料来自本地 ARMv7-M ARM、Cortex-M7 TRM/DGUG、官方 FreeRTOS V10.5.1 ARM_CM7 port，以及已有 M7 内核手册和异常对比笔记。
- 与 TC3xx EM 的差异：M7 没有 CSA 链，重点是硬件异常栈帧 + EXC_RETURN + 双栈 + NVIC；实验环境先 QEMU，Cache/Trace 后置。
