# 12 Core Debug Controller（内核调试控制器）

> 来源：`TC3xx Architecture vol1.pdf`，TriCore™ TC1.6.2 Core Architecture Manual，Volume 1，第 12 章。  
> 说明：本文件按原第 12 章的章节结构翻译为简体中文；寄存器名、字段名、指令名、信号名和二进制/十六进制取值保持英文/原格式，便于与原文和调试工具交叉核对。

TriCore™ 调试功能是架构、具体实现以及软件工具之间的接口。需要注意的是，后续架构代际中的相关机制可能会有所不同。

Core Debug Controller 设计目标是支持需要非侵入式调试的实时系统。CPU Core 内的大部分架构状态以及 Core 片上存储器，都可以通过系统地址映射（Address Map）进行访问。

对 Core 调试功能的访问，通常由包含该 CPU 的系统中的 On-Chip Debug Support（OCDS，片上调试支持）提供。

## Core Debug Controller Features（内核调试控制器特性）

Core Debug Controller 的特性主要面向软件开发环境。它提供实时运行控制能力，并使调试器能够观察数据、存储器等内部资源。特性包括：

- 实时运行控制：暂停（Halt）和重新启动（Restart）CPU。
- 访问并更新内部寄存器和 Core 本地存储器。
- 设置具有复杂触发条件的断点（breakpoints）和观察点（watchpoints）。

## Enabling the Core Debug Controller（使能内核调试控制器）

为了使能 Core Debug Controller，包含该 Core 的系统必须设置 Debug Status Register（DBGSR）中的 Debug Enable 位（DE）。当 `DBGSR.DE == 0` 时，Core Debug Controller 被禁用；当 `DBGSR.DE == 1` 时，Core Debug Controller 被使能。

`DBGSR.DE` 位如何被控制，以及 Core Debug Controller 如何被使能或禁用，取决于具体系统实现。当 Core Debug Controller 被使能时，称 Core 处于 debug mode（调试模式）。

## 12.1 Run Control Features（运行控制特性）

实时运行控制功能通过地址映射读写进行访问和控制，典型情况下由 OCDS 执行，也可以由任何具备相应授权的其他总线主设备执行。Core Debug Controller 向 Core 提供硬件挂钩，用于检测 Debug Event（调试事件），并由这些事件产生 Debug Action（调试动作）。

Core Debug Controller 提供 4 个用于与 OCDS 通信的信号：

- **Core Break-In**  
  OCDS 向 Core 指示发生了值得关注的条件。

- **Core Break-Out**  
  Core 向 OCDS 指示发生了值得关注的条件。

- **Core Suspend-In**  
  OCDS 向 Core 指示进入 Halt mode（暂停模式）。

- **Core Suspend-Out**  
  Core 向 OCDS 指示 Debug Status Register（DBGSR）中 `SUSP` 字段（`DBGSR.SUSP`）的状态。该信号可以通过写 Debug Status Register 控制，而 Core Break-Out 信号不能通过这种方式控制。

### Features（特性）

- 硬件支持单步执行（single-step）。
- 可导致 Debug Action 的 Debug Event 包括：
  - 外部 Core Break-In 信号对 Core 的断言。
  - 执行 `DEBUG` 指令。
  - 执行 `MTCR`（Move To Core Register）或 `MFCR`（Move From Core Register）指令。
  - Trigger Event Unit 产生的事件。
- Debug Action 可以是下列动作中的一个或多个：
  - 更新 Debug Status Register。
  - 通过 Core Break-Out 信号和/或 Core Suspend-Out 信号指示事件。
  - 暂停 CPU 执行。
  - 进入 Breakpoint Trap（断点陷阱）。
  - 产生 Breakpoint Interrupt（断点中断）。
  - 控制性能计数器。
- 实时特性：
  - Core 正在运行时，可对 Core 存储器和寄存器进行读写，且侵入性最小；但可能会“偷取”周期（cycle stealing）。
  - 可通过 Breakpoint Interrupt Debug Action 来服务高优先级中断例程。

> **Note**：CPU 运行时读写其他系统存储器可能具有侵入性，具体取决于完成该操作所需的周期数。发生这种情况时，会产生 cycle stealing。

Debug Event 和 Debug Action 的编程可以在 CPU 运行时进行，通常只有很小或没有侵入。Debug Event 的检测不会影响实时执行。

## 12.2 Debug Events（调试事件）

当 Core Debug Controller 被使能时，Debug Event 可以由以下来源产生：

- Core Break-In 信号。参见 12.2.1 External Debug Event。
- 执行 `DEBUG` 指令。参见 12.2.2 Debug Instruction。
- 执行 `MTCR` 或 `MFCR` 指令。参见 12.2.3 MTCR and MFCR Instructions。
- 硬件事件生成单元。参见 12.2.4 Trigger Event Unit。

### 12.2.1 External Debug Event（外部调试事件）

External Debug Event 与指令流没有任何关联，但它提供了一种无需复位即可停止 CPU 并获得 CPU 控制权的能力。如果 CPU 当前正在执行多周期且不可取消的指令（例如上下文保存和恢复），CPU 可能需要若干时钟周期才能识别该 Debug Event。

当 Core Break-In 信号被断言时，所采取的 Debug Action 由 `EXEVT`（External Event）寄存器指定。

### 12.2.2 Debug Instruction（调试指令）

TriCore 支持用户模式 `DEBUG` 指令。当 Core Debug Controller 被使能时，该指令可产生 Debug Event。当 Core Debug Controller 被禁用时，该指令被视为 `NOP`（No Operation）。`DEBUG` 指令提供 16-bit 和 32-bit 两种形式。

该特性便于软件调试：它允许跳转到监控程序，并提供一种开销较低的软件插桩和查询机制。

Debug Event 发生时采取的 Debug Action 由 `SWEVT`（Software Debug Event）寄存器指定。

### 12.2.3 MTCR and MFCR Instructions（MTCR 和 MFCR 指令）

当使用 `MTCR`（Move To Core Register）或 `MFCR`（Move From Core Register）指令读取或修改用户 Core Special Function Register（CSFR）时，会产生 Debug Event。这使调试软件能够监控、检测并修改 CSFR 的变化。

当 `MTCR` 或 `MFCR` 访问 `F000H` 到 `FDFFH` 范围内的寄存器时，不会产生 Debug Event。该范围包含所有专用 Debug SFR（Special Function Registers）：

- Debug Status Register（`DBGSR`）。
- Core Register Access Event Register（`CREVT`）。
- Software Debug Event Register（`SWEVT`）。
- External Event Register（`EXEVT`）。
- Trigger Event Register（`TRnEVT` / `TRxEVT`）。
- Debug Monitor Start Register（`DMS`）。
- Debug Context Pointer Register（`DCX`）。
- Debug Trap Control Register（`DBGTCR`）。
- Accumulated Trigger Information Register（`TRIG_ACC`）。

Additional Counter Registers（附加计数器寄存器）：

- Counter Control Register。
- CPU Clock Count Register。
- Instruction Count Register。
- Multi-Count Register 1。
- Multi-Count Register 2。
- Multi-Count Register 3。

当 Debug Event 被触发时，采取的 Debug Action 由 `CREVT` 寄存器指定。配置 Debug Controller 或访问 Performance counters 不会导致 debug event。

### 12.2.4 Trigger Event Unit（触发事件单元）

Trigger Event Unit 负责在一组可编程 Debug Trigger 有效时产生 Debug Event。Debug Trigger 可以是：

- 代码地址（Code Addresses）。
- 数据访问（Data Accesses）。

> **Note**：比较的地址为虚拟地址（virtual addresses）。

这些 Debug Trigger 作为输入提供给一个可编程逻辑模块，该模块以 Debug Event 作为输出。

当 Debug Event 被触发时，所采取的 Debug Action 由 Trigger Event register（`TRnEVT`）指定。

## 12.3 Debug Triggers（调试触发器）

每个 debug trigger 由一个 trigger address register（`TRnADR`）和一个关联的 trigger event register（`TRnEVT`）组成。成对的 debug trigger address 可用于定义地址范围。

Core Debug Controller 可以产生以下类型的 Debug Trigger：

- 在特定地址执行指令。
- 在某一地址范围内执行指令。
- 从特定地址加载一个值。
- 从某一地址范围内加载一个值。
- 向特定地址存储一个值。
- 向某一地址范围内存储一个值。

可用 debug trigger 的数量由具体实现决定。

### 12.3.1 Combining Debug Triggers（组合调试触发器）

奇数和偶数 trigger address register 可以成对组合，用于定义地址范围。当地址处于该范围内时，会产生 trigger。

- `Even Address Register <= Address < Odd Address Register`

通过设置该对寄存器中 event trigger 的 `RNG` 位，可将一对寄存器定义为 range pair。若偶数 EVT trigger 的 `RNG` 位被置位，则该范围的所有设置均取自偶数 EVT register，奇数 EVT register 被忽略。

- `TR0ADR` 和 `TR1ADR` 定义 `Range0`，由 `TR0EVT.RNG` 使能。
- `TR2ADR` 和 `TR3ADR` 定义 `Range1`，由 `TR2EVT.RNG` 使能。
- `TR4ADR` 和 `TR5ADR` 定义 `Range2`，由 `TR4EVT.RNG` 使能。
- `TR6ADR` 和 `TR7ADR` 定义 `Range3`，由 `TR6EVT.RNG` 使能。

> **Note**：奇数编号 Trigger Event register（如 `TR1EVT`、`TR3EVT` 等）的 `RNG` 位始终为保留位。

### 12.3.2 Task Specific Debug Triggers（任务特定调试触发器）

在某些情况下，可能希望仅当目标地址由特定任务产生时才断言 debug trigger。这通过 Application Space Identifier（ASI，应用空间标识符）比较功能实现。

如果 Trigger Event register（`TRnEVT`）中的 `ASI_EN` 位被置位，则只有在地址匹配且 `TRnEVT.ASI` 字段与当前任务 ASI（配置在 `TASK_ASI` register 中）匹配时，trigger 才会被断言。

### 12.3.3 Accumulated Debug Trigger Information（累计调试触发信息）

为了进一步辅助调试，提供了 `TRIG_ACC` register。该寄存器包含自上次清除该寄存器以来 debug trigger 的累计状态。每当某个 trigger 被激活时，无论其是否导致 debug event，都会被记录在 `TRIG_ACC` register 中。对于范围比较，仅记录低端 trigger 的激活。

例如，若 `TRIG_ACC.T[n]` 被置位，则表示自上次清除 `TRIG_ACC` register 以来，trigger-n 已经被激活过。

`TRIG_ACC` register 为只读寄存器，任何读操作都会清除该寄存器，所有写操作均被忽略。

## 12.4 Debug Actions（调试动作）

当 Debug Event 发生时，根据相关 Event Register 的编程配置，会采取以下 Debug Action 中的一个或多个：

- 更新 Debug Status Register（`DBGSR`）。
- 通过 Core Break-Out Signal 指示。
- 通过 Core Suspend-Out Signal 指示。
- Halt。
- Breakpoint Trap。
- Breakpoint Interrupt。
- Suspend Out。
- Performance Counter Start/Stop。
- None。
- Disabled。
- Suspend In Halt。

### 12.4.1 Update Debug Status Register（DBGSR）（更新调试状态寄存器）

当 Debug Event 发生时，Debug Status Register（`DBGSR`）中的以下字段始终会被更新：

- `EVTSRC`（Event Source）
- `PEVT`（Posted Event）
- `PREVSUSP`（Previous State of Suspend Signal）
- `SUSP`（Current State of Suspend Signal）

`PREVSUSP` 字段由 `SUSP` 字段的内容更新。

`SUSP` 字段由触发 Debug Event 的寄存器中的 `EVTA` 字段更新，这些寄存器可以是 `EXEVT`、`CREVT`、`SWEVT` 或 `TRnEVT`。

### 12.4.2 Indicate on Core Break-Out Signal（通过 Core Break-Out 信号指示）

Debug Event 可以向 OCDS 指示该事件已经发生。需要注意，该信号是否连接到外部引脚由具体实现决定。

### 12.4.3 Indicate on Core Suspend-Out Signal（通过 Core Suspend-Out 信号指示）

当发生 Core Suspend-Out action 时，Debug Status Register（`DBGSR`）中 `SUSP` 字段的值会被复制到 `PREVSUSP` 字段（`DBGSR.PREVSUSP`）。

`DBGSR.SUSP` 字段会更新为触发 Debug Event 的寄存器（`EXEVT`、`CREVT`、`SWEVT` 或 `TRnEVT`）中 `SUSP` 字段的内容。

对 `DBGSR.SUSP` 位的修改会反映到 Core Suspend-Out Signal 上。写 `DBGSR.SUSP` 位时，不会更新 `PREVSUSP`。

当 debug event 导致 breakpoint interrupt 被 posted 时，`DBGSR.SUSP`、`DBGSR.PREVSUSP` 和 Core Suspend-Out signal 保持不变。

### 12.4.4 Halt（暂停）

Debug Action `Halt` 会使 CPU 进入 Halt mode。Halt mode 会取消：

- 若 `BBM`（Break Before Make）被置位，则取消导致 breakpoint 的指令以及其后的所有指令。
- 若 `BBM` 未置位，则取消导致 breakpoint 的指令之后的所有指令。

这些指令被取消后，CPU 进入 Halt mode，在该模式下不再取指或执行指令。当 `DBGSR.HALT` 位字段被设置为 `01B` 时进入 Halt mode。进入 Halt mode 时，`DBGSR.EVTSRC` 位字段会被更新。

进入 Halt mode 后，外部 Debug system 可通过映射到 FPI 地址空间的架构状态来查询目标。

暂停期间，CPU 不响应任何中断。只有当 Debug Status Register 中的 `HALT` 位被清除（`DBGSR.HALT`）后，CPU 才恢复执行。通过向 `HALT` 字段写入 `10B` 可清除该位。

也可以通过写 `DBGSTR.HALT` 字段进入 halt。该操作被视为 external event，并会相应更新 `DBGSTR` 字段。

`DBGSTR.HALT` 字段由复位清除，CPU 随后恢复正常运行。

### 12.4.5 Breakpoint Trap（断点陷阱）

Breakpoint Trap 在不使用任何用户资源的情况下进入 Debug Monitor。它依赖以下仿真器资源：

- 一个 Debug Monitor，其执行从 `DMS`（Debug Monitor Start Address）register 定义的地址开始。
- 在 `DCX`（Debug Context Save Area Pointer）register 定义的地址处，有一块 4-word RAM 区域可用。该区域用于在 Debug Monitor 入口序列中保存关键状态。

当进入 Breakpoint Trap 时，会执行以下动作：

- 将 `PSW` 写入 `DCX + 4H`。
- 将 `PCXI` 写入 `DCX + 0H`。
- 将 `A[10]` 写入 `DCX + 8H`。
- 将 `A[11]` 写入 `DCX + CH`。
- `A[11] = PC`。
- 若 `PSW.IS == 0`，则将 `ISP` 的内容写入 `A10`。
- `PCXI.PIE = ICR.IE`。
- `PCXI.PCPN = ICR.CCPN`。
- `PC = DMS`。
- `PSW.PRS = 0H`。
- `PSW.IO = 2H`。
- `PSW.GW = 0H`。
- `PSW.IS = 1H`。
- `PSW.CDE = 0H`。
- `PSW.CDC = 0000000B`。
- `ICR.IE = 0H`。
- `DBGTCR.DTA = 1H`。

对应的返回序列由特权指令 `RFM`（Return From Monitor）提供。该机制提供一条自动进入 Debug Monitor 的路径，且不占用用户资源。随后使用 `RFM` 指令将控制权返回原始任务。当不处于 debug mode（即 `DBGSR.DE == 0`）时，`RFM` 指令为 `NOP`。

> **Note**：对于由 trap 或 interrupt 引起的任何 CSA 访问，其 load/store 地址上产生 breakpoint trap 的机制会被抑制。

#### Emulator Space（仿真器空间）

为了使 debug monitor 不必修改当前 memory protection 设置即可运行，在 debug mode 下会应用以下保护修改：

- 包含 `DMS` 指针的 16 MByte 区域（Base address == `{DMS[31:24], 24’h000000}`）在 debug mode 下对 instruction fetch 禁用 `MPX` trap。
- 包含 `DCX` 指针的 16 MByte 区域（Base address == `{DCX[31:24], 24’h000000}`）在 debug mode 下对 load 和 store 操作禁用 `MPR` 与 `MPW` trap。

这两个存储器区域称为 emulator space。通过设置 `SYSCON` register 中的 Emulator Space Disable 位（`SYSCON.ESDIS`），可以无条件禁用该行为。

emulator space 的可缓存性取决于 `PMA` registers 为其所在 segment 分配的 memory attributes。

#### Multiple Breakpoint Traps（多个断点陷阱）

进入 breakpoint trap 时，TriCore 会在 `DCX` register 指示的位置保存一个 debug context（`PCX`、`PSW`、`A10`、`A11`）。在 debug trap handler 结束时，使用 `RFM` 指令恢复该状态。

`DCX` 位置只能存储单个 debug context。因此，如果触发多个 breakpoint trap，就会产生问题：只保留最后一个 breakpoint trap 保存的状态，此前 breakpoint trap 的全部状态都会丢失。

为避免这种情况，breakpoint trap 入口序列会设置 Debug Trap Control Register（`DBGTCR`）中的 Debug Trap Active（`DTA`）位。该位用于抑制后续 breakpoint trap。

`DTA` 位在 `RFM` 指令执行时被清除，在 breakpoint trap 时被置位；也可以通过 `MTCR` 设置和清除。只有在 `DTA == 0` 时，才允许进入 breakpoint trap。进入 breakpoint trap 会将 `DTA` 位置 1。因此，在 breakpoint trap handler 清除 `DTA` 位之前，或者 breakpoint trap handler 以 `RFM` 结束之前，后续 breakpoint trap 会被禁用。

在 application reset 之后，`DTA` 位被置为 1。因此，在允许 debug trap 发生之前，必须先清除该寄存器。

### 12.4.6 Breakpoint Interrupt（断点中断）

Debug Event 可采取的 Debug Action 之一是产生 Breakpoint Interrupt。中断优先级可编程，并由与该 breakpoint interrupt 关联的控制寄存器定义。

该架构允许一个 Debug Event 产生 4 个 Breakpoint Interrupt 中的一个，每个 Breakpoint Interrupt 都可以有自己的中断优先级。Breakpoint Interrupt 的数量由具体实现决定。

Breakpoint Interrupt 允许定义灵活的 Debug 环境，从而满足实时系统高效调试的许多要求。例如，在调试器处于活动状态时，仍可保持安全关键代码的执行。

Breakpoint Interrupt 可用于提供传统微控制器中常见的 conventional Debug Model：即 breakpoint 通过停止处理器来调试。实现方式是简单地将最高中断优先级分配给 Debug Monitor，或者确保在 Debug Monitor 中禁用中断。

同时，它也提供灵活性，允许关键中断被配置为比 Debug Monitor 更高的优先级。其优点包括：

- Debug Monitor 可以像任何其他中断一样，被更高级别的中断打断。这允许 CPU 在 Debug Monitor 运行期间服务关键中断。
- 在关键例程中 posted 的任何 Debug Event 都会被推迟，直到 CPU 优先级降至低于 Debug Monitor 的优先级。

#### Figure 27 Debug Monitor - Simple and Advanced Models（调试监控器：简单模型与高级模型）

- **Simple Debug Model**：Debug Monitor 在系统中具有最高优先级，因此不能被中断。
- **Advanced Debug Model**：Debug Monitor 的优先级低于 Interrupt A。这意味着 Debug Monitor 在处理 Background Task 或 Interrupt Routine B 中的 Breakpoint 时，可以被 Interrupt A 打断并服务 Interrupt A。

#### Posted Breakpoint Interrupts（已挂起的断点中断）

需要考虑这样一种情况：面向 CPU 的 Breakpoint Interrupt 的中断优先级低于当前 CPU 优先级。例如，在 Figure 27 的 Advanced Model 中，如果在 Interrupt Routine A 中设置 Breakpoint Interrupt，则会存在问题，因为 Debug Monitor 被配置为低于当前任务的优先级。

这种场景通过在与 Breakpoint 相关联的中断级别上 post 一个 software interrupt 来表示。因此，当 CPU interrupt priority level 降到低于 Debug Monitor 的级别时，会进入 Debug Monitor routine。

为了向 Monitor routine 指示 Breakpoint 曾被推迟，在 post software interrupt 时，Debug Status register 中的 Posted Event 位（`PEVT`）会被置位。Breakpoint Interrupt handler 负责检查 Debug Status register 中的该位，并在必要时清除该位。

> **Note**：当 breakpoint interrupt 被 posted 时，`DBGSR.SUSP` 和 `DBGSR.PREVSUSP` 不会更新。

1. 无论 breakpoint interrupt 是否被 posted，`DBGSR.EVTSRC` 始终会被更新。

#### Interrupts to Other Targets（面向其他目标的中断）

除了可以面向 CPU，breakpoint interrupt 也可以面向系统中的其他 Core。

### 12.4.7 Suspend Out（暂停输出）

当 debug event 发生时，suspend out 信号会被断言或取反。suspend out 信号的前一状态记录在 `DBGSR.PREVSUSP` 中。

### 12.4.8 Performance Counter Start/Stop（性能计数器启动/停止）

当 performance counter 以 task mode 工作时，计数器由 debug action 启动和停止。所有 event register 都允许启动或停止计数器。

Trigger event registers 还允许将模式在 active（start）与 inactive（stop）之间切换。这使得在某些应用中，可以使用单个 RTE 控制 performance counter。

### 12.4.9 None（无动作）

event register 的 `EVTA` 字段不会执行任何动作；但对于事件来说，suspend out signal、performance count 和 `DBGSR` register 更新仍会正常发生。

### 12.4.10 Disabled（禁用）

事件被禁用，且不会发生任何动作。suspend out signal、performance counter control 和 `DBGSR` register 均会忽略该事件。

### 12.4.11 Suspend In Halt（Suspend-In 暂停）

当 Suspend In 信号被断言时，只要 debug 被使能，就始终会进入 halt mode。只要 Suspend In 保持断言，CPU 就保持在 halt mode。当 Suspend In 被取反时，CPU 从 halt 释放。

该机制用于在多核系统中同时暂停多个 Core，并同时将其从 halt 释放。

## 12.5 Priority of Debug Events（调试事件优先级）

多个 trigger point 可能会同时被激活。与流水线中最早指令关联的 trigger 会优先处理。此外，与流水线中同一点同时关联的 Trigger point，其优先级从高到低如下：

- 外部输入断言（asynchronous）。
- PC 上的可编程 bank trigger。
  - 当多个 trigger 同时有效时，0 优先级最高，7 优先级最低。
- `MTCR` / `MFCR` 指令。
- `DEBUG` 指令。
- Address 上的可编程 trigger。
  - 当多个 trigger 同时有效时，0 优先级最高，7 优先级最低。

## 12.6 Call Tracing（调用跟踪）

TriCore 系统中的子程序调用跟踪通过基于 `PSW` 的 call depth counter 和 `CDO` trap handler 实现。

调用跟踪的序列如下：

1. 将基于 `PSW` 的 Call Depth Counter 设置为在每次子程序调用时产生 `CDO` trap（`PSW.CDC = 1111110B`）。
2. 使能 Call Depth 计数系统（`PSW.CDE = 1`）。
3. 当下一次尝试执行 `CALL` 时，将进入 `CDO` trap，而不是执行子程序调用。
4. `CDO` trap handler 执行所需的 trace 功能。
5. `CDO` trap handler 清除存储器中 trapping context 的 `PSW.CDE` 位。
6. `CDO` trap handler 执行 Return from Exception（`RFE`）。这会从存储器中恢复 trapping context，但此时 call depth tracing 已被禁用（`PSW.CDE = 0`）。
7. 原始 `CALL` 被执行。由于 call depth tracing system 此时已禁用（`PSW.CDE = 0`），子程序调用会成功执行。

补充规则：

- 每当 `CALL` 指令保存 `PSW` 时，`CDE` 位会被强制为 `1`。
- 在子程序开始时，`PSW.CDE` 位的状态为 `1`。

在 Call Tracing 序列中，`PSW.CDE` 位具有“一次性”（one-shot）操作特性：在 `CDO` trap 清除后，仅对一次子程序调用禁用。

更多信息请参见本手册 Volume 2 中的 `CALL` 指令说明。

## 12.7 The Debug Control Registers（调试控制寄存器）

Debug Status Register（`DBGSR`）包含 CPU core 中 Core Debug Controller 硬件当前状态的信息：

- 一个用于指示 debug 是否被使能的位。
- 上一次 Debug Event 的来源。

每个 Debug Event 来源都有一个关联的寄存器，该寄存器定义 Debug Event 被触发时应采取的 Debug Action。这些寄存器还可以包含触发 Debug Event 所必须满足的附加条件信息，例如 Debug Trigger 的组合条件。

## 12.8 Debug Control Registers - Summary（调试控制寄存器汇总）

Core Debug Controller Registers：

| Register | Description（中文） | Offset Address |
|---|---|---:|
| DBGSR | Debug Status Register，调试状态寄存器 | FD00H |
| EXEVT | External Event Register，外部事件寄存器 | FD08H |
| CREVT | Core Register Access Event Register，Core 寄存器访问事件寄存器 | FD0CH |
| SWEVT | Software Debug Event Register，软件调试事件寄存器 | FD10H |
| TRIG_ACC | Trigger Accumulator Register，触发累计寄存器 | FD30H |
| DMS | Debug Monitor Start Address Register，调试监控器起始地址寄存器 | FD40H |
| DCX | Debug Context Save Area Pointer Register，调试上下文保存区指针寄存器 | FD44H |
| DBGTCR | Debug Trap Control Register，调试陷阱控制寄存器 | FD48H |
| TASK_ASI | Application Space Identifier Register，应用空间标识符寄存器 | 8004H |
| TR0EVT | Trigger Event 0 Configuration Register，触发事件 0 配置寄存器 | F000H |
| TR0ADR | Trigger Event 0 Address Register，触发事件 0 地址寄存器 | F004H |
| TR1EVT | Trigger Event 1 Configuration Register，触发事件 1 配置寄存器 | F008H |
| TR1ADR | Trigger Event 1 Address Register，触发事件 1 地址寄存器 | F00CH |
| TR2EVT | Trigger Event 2 Configuration Register，触发事件 2 配置寄存器 | F010H |
| TR2ADR | Trigger Event 2 Address Register，触发事件 2 地址寄存器 | F014H |
| TR3EVT | Trigger Event 3 Configuration Register，触发事件 3 配置寄存器 | F018H |
| TR3ADR | Trigger Event 3 Address Register，触发事件 3 地址寄存器 | F01CH |
| TR4EVT | Trigger Event 4 Configuration Register，触发事件 4 配置寄存器 | F020H |
| TR4ADR | Trigger Event 4 Address Register，触发事件 4 地址寄存器 | F024H |
| TR5EVT | Trigger Event 5 Configuration Register，触发事件 5 配置寄存器 | F028H |
| TR5ADR | Trigger Event 5 Address Register，触发事件 5 地址寄存器 | F02CH |
| TR6EVT | Trigger Event 6 Configuration Register，触发事件 6 配置寄存器 | F030H |
| TR6ADR | Trigger Event 6 Address Register，触发事件 6 地址寄存器 | F034H |
| TR7EVT | Trigger Event 7 Configuration Register，触发事件 7 配置寄存器 | F038H |
| TR7ADR | Trigger Event 7 Address Register，触发事件 7 地址寄存器 | F03CH |

## 12.9 Debug Control Registers（调试控制寄存器）

### Debug Status Register（调试状态寄存器）

`DBGSR` - Debug Status Register，地址 `FD00H`，复位值：`0000 0000H`

| Field | Bits | Type | Description（中文） |
|---|---:|---|---|
| RES | [31:13] | - | 保留。 |
| EVTSRC | [12:8] | rh | Event Source，事件来源。`0`：`EXEVT`；`1`：`CREVT`；`2`：`SWEVT`；`16 + n`：`TRnEVT`（`n = 0..7`）；其他值保留。 |
| PEVT | 7 | rwh | Posted Event。`0`：无 posted event；`1`：有 posted event。 |
| PREVSUSP | 6 | rh | Core Suspend-Out Signal 的前一状态。`0`：前一 core suspend-out 非活动；`1`：前一 core suspend-out 活动。当 Debug Event 导致 `DBGSR.SUSP` 被硬件更新时，该字段更新；对 `DBGSR.SUSP` 的写操作不会更新该字段。 |
| RES | 5 | - | 保留。 |
| SUSP | 4 | rwh | Core Suspend-Out Signal 的当前状态。`0`：core suspend-out 非活动；`1`：core suspend-out 活动。 |
| SIH | 3 | rh | Suspend-in Halt。表示 Suspend-In 信号状态。`1`：Suspend-In 信号被断言，CPU 处于 Halt Mode；`0`：Suspend-In 信号被取反，CPU 不处于 Halt Mode（但 Debug Event 或写 `DBGSR.HALT` 触发 Halt 机制的情况除外）。 |
| HALT | [2:1] | rwh | CPU Halt Request / Status Field。`HALT[0]` 为实际 Halt 位；`HALT[1]` 为 mask 位，用于指定软件写操作是否更新 `HALT[0]`。`HALT[1]` 读出始终为 0。必须将 `HALT[1]` 写 1 才能通过软件更新 `HALT[0]`。读写含义：`00B` 读：CPU running；写：`HALT[0]` 不变。`01B` 读：CPU halted；写：`HALT[0]` 不变。`10B` 读：不适用；写：复位 `HALT[0]`。`11B` 读：不适用；写：若 `DBGSR.DE == 1`，置位 `HALT[0]`；若 `DBGSR.DE == 0`，`HALT[0]` 不变。 |
| DE | 0 | rh | Debug Enable。决定 core debug 是否使能。`0`：Core Debug 禁用；`1`：Core Debug 使能。 |

### External Event Register（外部事件寄存器）

`EXEVT` - External Event Register，地址 `FD08H`，复位值：`0000 0000H`

| Field | Bits | Type | Description（中文） |
|---|---:|---|---|
| RES | [31:8] | - | 保留。 |
| CNT | [7:6] | rw | Counter。当该事件发生时，在 task mode 下按如下方式调整 performance counters 的控制：`00`：不改变；`01`：启动 performance counters；`10`：停止 performance counters；`11`：切换 performance counter control（当前停止则启动，当前运行则停止）。 |
| SUSP | 5 | rw | Core Debug Suspend-Out Signal State。当 Debug Event 被触发时，要赋给 Core Debug suspend-out signal 的值。 |
| BOD | 4 | rw | Breakout Disable。`0`：按照 `EVTA` 字段指定的 Debug Action 断言 `BRKOUT` 信号；`1`：不断言 `BRKOUT` 信号。该设置优先于 `EVTA` 字段产生的任何断言。 |
| BBM | 3 | rw | Break Before Make（BBM）或 Break After Make（BAM）选择。`0`：Break after make（BAM）；`1`：Break before make（BBM）。 |
| EVTA | [2:0] | rw | Event Associated。Debug Event 关联的 Debug Action。见下表。 |

`EVTA` 取值：

| BOD | EVTA | Debug Action（中文） |
|---:|---:|---|
| 0 | 000B | Disabled。 |
| 0 | 001B | Pulse `BRKOUT` Signal。 |
| 0 | 010B | Halt 并 pulse `BRKOUT` Signal。 |
| 0 | 011B | Breakpoint trap 并 pulse `BRKOUT` Signal。 |
| 0 | 100B | Breakpoint interrupt 0 并 pulse `BRKOUT` Signal。 |
| 0 | 101B | 若实现，则 breakpoint interrupt 1 并 pulse `BRKOUT` Signal；若未实现，则 None。 |
| 0 | 110B | 若实现，则 breakpoint interrupt 2 并 pulse `BRKOUT` Signal；若未实现，则 None。 |
| 0 | 111B | 若实现，则 breakpoint interrupt 3 并 pulse `BRKOUT` Signal；若未实现，则 None。 |
| 1 | 000B | Disabled。 |
| 1 | 001B | None。 |
| 1 | 010B | Halt。 |
| 1 | 011B | Breakpoint trap。 |
| 1 | 100B | Breakpoint interrupt 0。 |
| 1 | 101B | 若实现，则 breakpoint interrupt 1；若未实现，则 None。 |
| 1 | 110B | 若实现，则 breakpoint interrupt 2；若未实现，则 None。 |
| 1 | 111B | 若实现，则 breakpoint interrupt 3；若未实现，则 None。 |

### Core Register Access Event Register（Core 寄存器访问事件寄存器）

`CREVT` - Core Register Access Event，地址 `FD0CH`，复位值：`0000 0000H`

`CREVT` 字段定义与 `EXEVT` 的通用事件字段一致：`CNT`、`SUSP`、`BOD`、`BBM`、`EVTA`。区别在于该事件源来自 Core register 访问事件。

| Field | Bits | Type | Description（中文） |
|---|---:|---|---|
| RES | [31:8] | - | 保留。 |
| CNT | [7:6] | rw | 当该事件发生时，在 task mode 下控制 performance counters：`00` 不变，`01` 启动，`10` 停止，`11` 切换。 |
| SUSP | 5 | rw | Debug Event 被触发时赋给 Core debug suspend-out signal 的值。 |
| BOD | 4 | rw | Breakout Disable。`0`：按 `EVTA` 断言 `BRKOUT`；`1`：不允许 `BRKOUT` 断言。 |
| BBM | 3 | rw | `0`：BAM；`1`：BBM。 |
| EVTA | [2:0] | rw | Debug Event 关联的 Debug Action，取值同 `EXEVT.EVTA`。 |

### Software Debug Event Register（软件调试事件寄存器）

`SWEVT` - Software Debug Event，地址 `FD10H`，复位值：`0000 0000H`

`SWEVT` 字段定义与 `EXEVT` 的通用事件字段一致：`CNT`、`SUSP`、`BOD`、`BBM`、`EVTA`。区别在于该事件源来自软件 `DEBUG` 指令。

| Field | Bits | Type | Description（中文） |
|---|---:|---|---|
| RES | [31:8] | - | 保留。 |
| CNT | [7:6] | rw | 当该事件发生时，在 task mode 下控制 performance counters：`00` 不变，`01` 启动，`10` 停止，`11` 切换。 |
| SUSP | 5 | rw | 事件被触发时赋给 Core Debug suspend-out signal 的值。 |
| BOD | 4 | rw | Breakout Disable。`0`：按 `EVTA` 断言 `BRKOUT`；`1`：不允许 `BRKOUT` 断言。 |
| BBM | 3 | rw | `0`：BAM；`1`：BBM。 |
| EVTA | [2:0] | rw | Debug Event 关联的 Debug Action，取值同 `EXEVT.EVTA`。 |

### Trigger Event Registers（触发事件寄存器）

`TRxEVT` 存储每个 trigger 的配置。`TRxEVT` 会按照 comparator 的数量进行复制。

> **Note**：奇数编号 Trigger Event register（如 `TR1EVT`、`TR3EVT` 等）的 `RNG` 位始终保留。

`TRxEVT` - Trigger Event x，地址 `F0XXH`，复位值：`0000 0000H`

| Field | Bits | Type | Description（中文） |
|---|---:|---|---|
| RES | [31:29] | - | 保留。 |
| ALD | 28 | rw | Address Load。与 `TYP = 0` 配合使用。 |
| AST | 27 | rw | Address Store。与 `TYP = 0` 配合使用。 |
| RES | [26:21] | - | 保留。 |
| ASI | [20:16] | rw | Address Space Identifier。Debug Trigger 进程的 ASI。 |
| ASI_EN | 15 | rw | Enable ASI Comparison。`0`：不执行 ASI 比较，Debug Trigger 对所有进程有效；`1`：使能 ASI 比较，只有当前进程 ASI 与 `TRnEVT.ASI` 匹配时才触发 Debug Event。 |
| RES | 14 | - | 保留。 |
| RNG | 13 | rw | Compare Type。该定义仅适用于偶数编号 Trigger Event register（如 `TR0EVT`、`TR2EVT` 等）；奇数编号的 `RNG` 位始终保留。`1B`：Range；`0B`：Equality。偶数 comparator 设为 range 后，其关联上邻 comparator 的 `EVTR` 设置将被忽略。 |
| TYP | 12 | rw | Input Selection。`0B`：Address；`1B`：PC。 |
| RES | [11:8] | - | 保留。 |
| CNT | [7:6] | rw | 当该事件发生时，在 task mode 下控制 performance counters：`00` 不变，`01` 启动，`10` 停止，`11` 切换。 |
| SUSP | 5 | rw | Debug Event 被触发时赋给 Core Debug suspend-out signal 的值。 |
| BOD | 4 | rw | Breakout Disable。`0`：按 `EVTA` 断言 `BRKOUT`；`1`：不允许 `BRKOUT` 断言。 |
| BBM | 3 | rw | Break Before Make（BBM）或 Break After Make（BAM）选择。对 code trigger：`0` 表示 code only triggers Break After Make（BAM），`1` 表示 code only triggers Break Before Make（BBM）。对 trigger：`0` 表示 trigger 为 BAM，`1` 表示 trigger 为 BBM。 |
| EVTA | [2:0] | rw | 指定与 Debug Event 关联的 Debug Action。取值与 `EXEVT.EVTA` 相同。 |

### Trigger Address Register（触发地址寄存器）

`TRxADR` 存储每个 trigger 的比较地址值。

`TRxADR` - Trigger Address x，地址 `F0XXH`，复位值：`0000 0000H`

| Field | Bits | Type | Description（中文） |
|---|---:|---|---|
| ADDR | [31:0] | rw | Comparison Address，比较地址。对于 PC comparison，bit[0] 始终为 0。 |

### Trigger Accumulator Register（触发累计寄存器）

`TRIG_ACC` 存储自上次清除以来累计的 debug trigger 状态。

> **Note**：任何读操作都会清除该寄存器，写操作会被忽略。

`TRIG_ACC` - Core Debug Trigger Accumulator，地址 `FD30H`，复位值：`0000 0000H`

| Field | Bits | Type | Description（中文） |
|---|---:|---|---|
| RES | [31:8] | - | 保留。 |
| T7 | 7 | rh | 自上次清除以来 Trigger-7 已激活。 |
| T6 | 6 | rh | 自上次清除以来 Trigger-6 已激活。 |
| T5 | 5 | rh | 自上次清除以来 Trigger-5 已激活。 |
| T4 | 4 | rh | 自上次清除以来 Trigger-4 已激活。 |
| T3 | 3 | rh | 自上次清除以来 Trigger-3 已激活。 |
| T2 | 2 | rh | 自上次清除以来 Trigger-2 已激活。 |
| T1 | 1 | rh | 自上次清除以来 Trigger-1 已激活。 |
| T0 | 0 | rh | 自上次清除以来 Trigger-0 已激活。 |

### Debug Monitor Start Address Register（调试监控器起始地址寄存器）

`DMS` reset value 为 `{20’hA0000, 3’B0001, CORE_ID, 6’B000000}`。

`DMS` - Debug Monitor Start Address，地址 `FD40H`，复位值：Implementation Specific

| Field | Bits | Type | Description（中文） |
|---|---:|---|---|
| DMS Value | [31:1] | rw | Debug Monitor Start Address。当进入 breakpoint trap 时，monitor code execution 开始执行的地址。 |
| RES | 0 | - | 保留。 |

### Debug Context Save Area Pointer Register（调试上下文保存区指针寄存器）

`DCX` register 的 reset value 为 `{20’hA0000, 3’b010, core_id, 6’b000000}`。

`DCX` - Debug Context Save Area Pointer，地址 `FD44H`，复位值：Implementation Specific

| Field | Bits | Type | Description（中文） |
|---|---:|---|---|
| DCX Value | [31:6] | rw | Debug Context Save Area Pointer。Breakpoint trap 之后 debug context 的存储地址。 |
| RES | [5:0] | - | 保留。 |

### Debug Trap Control Register（调试陷阱控制寄存器）

Debug Trap Control Register 包含 `DTA`（Debug Trap Active）位。

`DTA` 位定义为：在执行 `RFM` 指令时被清除，在 breakpoint trap 时被置位。也可以通过 `MTCR` 设置和清除。

在 application reset 后，`DTA` 位被置为 1。因此，在允许 debug trap 发生之前，必须清除该寄存器。

`DBGTCR` - Debug Trap Control Register，地址 `FD48H`，复位值：`0000 0001H`

| Field | Bits | Type | Description（中文） |
|---|---:|---|---|
| RES | [31:1] | - | 保留。 |
| DTA | 0 | rwh | Debug Trap Active Bit。`1`：一个 breakpoint trap 处于 active；`0`：无 breakpoint trap active。只有在 `DTA == 0` 时才可进入 breakpoint trap。进入 breakpoint trap 会将 `DTA` 置 1。因此，在 breakpoint trap handler 清除 `DTA` 位之前，或 breakpoint trap handler 以 `RFM` 结束之前，后续 breakpoint trap 被禁用。 |

### Address Space Identifier Register（TASK_ASI）（地址空间标识符寄存器）

`TASK_ASI` - Address Space Identifier Register，地址 `8004H`，复位值：Implementation Specific

| Field | Bits | Type | Description（中文） |
|---|---:|---|---|
| RES | [31:5] | - | 保留。 |
| ASI | [4:0] | rw | Address Space Identifier。`ASI` register 包含当前进程的 Address Space Identifier。 |

## 12.10 Core Performance Measurement and Analysis（Core 性能测量与分析）

Core 性能的实时测量可为系统开发人员、架构师、编译器开发人员、应用开发人员、OS 开发人员等提供有用洞察。

TriCore 包含一种能力：在不对处理器执行产生实时影响的情况下，测量处理器不同方面的性能。性能测量硬件被配置为一次只能同时采集性能测量项的一个子集。

Performance measurement block 可用于测量以下基础参数：

- CPU Clocks。
- Instruction Count。
- Instruction Cache Hit / Miss。
- Data Cache Hit / Miss（clean 或 dirty）。

实际可测量的参数由具体实现决定。

Performance counters 可以以 free-running 方式使用：使能后采集聚合信息。也可以结合 debug event logic 使用，用于控制某个单独任务的操作“窗口”，例如按某个期望事件动态启动和停止 counters，从而过滤测量信息。

### Typical Performance Counter Usage（性能计数器典型用法）

Performance counters 由 `CCTRL` CSFR register 控制。

通过向 `CCTRL.CE` counter enable 位写入适当值，可以使能或禁用 performance counters。

典型情况下，为了进行基线测量，总是统计两个参数：

- clock count。
- issued instruction 的数量。

以下两类中各选一种：

- Instruction Cache Hits。
- Data Cache Hits。

以及：

- Instruction Cache Misses。
- Data Cache Clean Misses。

另外还有：

- Data Cache Dirty Misses（需要 cache write-back / eviction）。

> **Note**：Counters 只能在被禁用时写入，即不处于 counting mode 时。任何在 counting-mode 下的写入尝试都不会产生效果。

> **Note**：Counters 一旦使能，即为 free-running incrementors。达到最大值后会回绕到 0。

Counter function 的分组允许将典型测量进行聚类，例如 Data Cache performance 与 Instruction Cache performance。

这些都可以结合 clock cycles 和 issued instructions 的背景统计进行测量。

Counters 的启动并不精确同步到任何流水线阶段。例如，一旦 instruction counter 被使能计数，它会从该时钟周期开始统计所有 retiring instructions。类似地，一旦 instruction cache miss counter 启动，它会从该时钟周期开始统计所有 instruction cache misses。

有两种方式使能 counters：Normal mode 和 Task mode（`CCTRL.CM`）。

Normal（默认模式）或 Task mode 由 `CCTRL.CM` 配置：

- **Normal mode**：counters 一旦使能即开始计数，并持续计数直到被禁用。
- **Task mode**：只有在处理器检测到带有“启动 performance counters”动作的 debug event 时，counters 才会计数。

### Writing of the Counters（计数器写入）

Counters 可在任意时间读取，但只能在不主动计数时写入，即在其被禁用时写入。若 counters 被禁用，则不认为其处于 counting mode，因此可以写入。

当满足以下条件时，counter 被认为处于 counting mode：

- 已选择 Normal 或 Task mode。
- mode 为 active（Normal mode 始终 active）。
- Counter Control register（`CCTRL`）中的 counter enable `CE` 位被使能。

### Counter Modes（计数器模式）

Counter Control CSFR 中的 Counter Mode（`CM`）位（即 `CCTRL.CM`）决定所有 counters 的工作模式。

在 Normal mode 下，如果 `CCTRL` 中 Count enable 位（`CCTRL.CE`）被置位，则 counter 会在各自的 trigger 上递增。

在 Task mode 下，debug unit 会提供额外的 gating control，使 performance counters 收集的数据能够按特定条件过滤，例如仅针对单个 task。

### Wrapping of the counters / Sticky bit（计数器回绕 / 粘滞位）

Performance counters 会通过 sticky bit 向用户指示 counter 是否发生过回绕。这有助于判断两个测量值之间 counter 是否曾经回绕。

- 所有 performance counters 都是 31-bit counter，采用 free wrapping 操作。
- 每个 counter 的 bit 31 是 sticky 位。当 bits 30:0 回绕时，该位被置位。它保持置位，直到由软件写入清除。

## 12.11 Performance Counter Registers（性能计数器寄存器）

Performance counter registers 如下：

| Register | Description（中文） | Offset Address | Reference |
|---|---|---:|---|
| CCTRL | Counter Control Register，计数器控制寄存器 | FC00H | Page 32 |
| CCNT | CPU Clock Count Register，CPU 时钟计数寄存器 | FC04H | Page 33 |
| ICNT | Instruction Count Register，指令计数寄存器 | FC08H | Page 34 |
| M1CNT | Multi Count Register 1，多功能计数寄存器 1 | FC0CH | Page 35 |
| M2CNT | Multi Count Register 2，多功能计数寄存器 2 | FC10H | Page 36 |
| M3CNT | Multi Count Register 3，多功能计数寄存器 3 | FC14H | Page 37 |

### Counter Control Register（计数器控制寄存器）

`CCTRL` - Counter Control，地址 `FC00H`，复位值：`0000 0000H`

| Field | Bits | Type | Description（中文） |
|---|---:|---|---|
| RES | [31:11] | - | 保留。 |
| M3 | [10:8] | rw | `M3CNT` configuration，Implementation Specific。 |
| M2 | [7:5] | rw | `M2CNT` configuration，Implementation Specific。 |
| M1 | [4:2] | rw | `M1CNT` configuration，Implementation Specific。 |
| CE | 1 | rw | Count Enable。`0`：禁用 counters：`CCNT`、`ICNT`、`M1CNT`、`M2CNT`、`M3CNT`；`1`：使能这些 counters。 |
| CM | 0 | rw | Counter Mode。`0`：Normal Mode；`1`：Task Mode。 |

### CPU Clock Cycle Count Register（CPU 时钟周期计数寄存器）

`CCNT` - CPU Clock Cycle Count，地址 `FC04H`，复位值：`0000 0000H`

| Field | Bits | Type | Description（中文） |
|---|---:|---|---|
| SOvf | 31 | rw | Sticky Overflow bit。当 count value `[30:0] = 31’h7FFF_FFFF` 时由硬件置位；只能由软件清除。 |
| Count Value | [30:0] | rw | Count Value。CPU Clock Cycles 的当前计数。 |

### Instruction Count Register（指令计数寄存器）

`ICNT` - Instruction Count，地址 `FC08H`，复位值：`0000 0000H`

| Field | Bits | Type | Description（中文） |
|---|---:|---|---|
| SOvf | 31 | rw | Sticky Overflow bit。当 count value `[30:0] = 31’h7FFF_FFFF` 时由硬件置位；只能由软件清除。 |
| Count Value | [30:0] | rw | Count Value。已执行指令的计数。 |

### Multi-Count Register 1（多功能计数寄存器 1）

`M1CNT` - Multi-Count Register 1，地址 `FC0CH`，复位值：`0000 0000H`

| Field | Bits | Type | Description（中文） |
|---|---:|---|---|
| SOvf | 31 | rw | Sticky Overflow bit。当 count value `[30:0] = 31’h7FFF_FFFF` 时由硬件置位；只能由软件清除。 |
| Count Value | [30:0] | rw | Count Value。所选事件的计数。 |

### Multi-Count Register 2（多功能计数寄存器 2）

`M2CNT` - Multi-Count Register 2，地址 `FC10H`，复位值：`0000 0000H`

| Field | Bits | Type | Description（中文） |
|---|---:|---|---|
| SOvf | 31 | rw | Sticky Overflow bit。当 count value `[30:0] = 31’h7FFF_FFFF` 时由硬件置位；只能由软件清除。 |
| Count Value | [30:0] | rw | Count Value。所选事件的计数。 |

### Multi-Count Register 3（多功能计数寄存器 3）

`M3CNT` - Multi-Count Register 3，地址 `FC14H`，复位值：`0000 0000H`

| Field | Bits | Type | Description（中文） |
|---|---:|---|---|
| SOvf | 31 | rw | Sticky Overflow bit。当 count value `[30:0] = 31’h7FFF_FFFF` 时由硬件置位；只能由软件清除。 |
| Count Value | [30:0] | rw | Count Value。所选事件的计数。 |
