# FreeRTOS Port 深潜 第 1 课：任务切换 = 换一条 CSA 链（TC3xx）

## 核心问题

任务切换落到硬件上到底发生什么？FreeRTOS 的 TriCore port 如何借助 CSA（Context Save Area）硬件机制实现切换？为什么同样的功能在 ARM Cortex-M 上做法完全不同？

## 结论

**TriCore 上"一个任务的上下文" ≈ 一条 CSA 链；切任务 = 换链头（PCXI）+ 存取 Lower Context。**

- Upper Context（PCXI/PSW/SP/返回地址/A12–A15/D8–D15）由**硬件自动**存取（CALL/中断/trap 时存，RET/RFE 时恢复），port 不需要管；
- Lower Context（A2–A7/D0–D7/A11）由 port 用 `svlcx`/`rslcx` 手动存取；
- 新任务的首次运行靠"伪造初始上下文"实现：创建任务时消耗 2 个 CSA，把任务函数入口写进 A11（返回地址位）、参数写进 A4，第一次 RFE 时 CPU "从中断返回"进任务函数；
- port 层是四件套：`port.c` + `portmacro.h` + `FreeRTOSConfig.h`（硬件地址/优先级）+ `Ifx_Cfg.h`（trap hook 接线）——S0 排障证明缺任何一件都会出隐性故障。

## 背景

- 本笔记是 FreeRTOS × TC397 学习路线「SP Port 深潜」系列第 1 课的落盘总结，路线总图见 [[FreeRTOS_00_学习路线与问题地图]]。
- 依托工程：`TC397_Platform_Jason/ADS/FreeRTOS`（git: zlmjason/TC397_FreeRTOS），FreeRTOS 内核 V10.5.1，TASKING port（`OS/FreeRTOS/portable/Tasking/TC3/port.c`），ADS + TASKING Lite。
- 学习契机：S0 排障（SYSCALL trap hook 缺失致 yield 空转）实战接触了 syscall 链路后，趁热系统拆解上下文切换机制。
- 文中行号对应 commit `f588fb5` 的 port.c。

## 关键机制

### 1. TriCore 上下文模型（硬件事实）

| 组 | 内容 | 存取责任 |
|---|---|---|
| Upper Context（64B） | PCXI、PSW、A10(SP)、A11(RA)、A12–A15、D8–D15 | 硬件自动（CALL/JI/中断/trap 存；RET/RFE 恢复） |
| Lower Context（64B） | PCXI、A11、A2–A7、D0–D7 | 软件手动（`svlcx` / `rslcx`） |

CSA 是 DSPR 中一串 64 字节的格子，由三个 CSFR 管理：

- `FCX`：空闲 CSA 链头（领新格子从这拿）
- `PCXI`：当前调用链头（每次 CALL/中断，硬件往链上挂一节）
- `LCX`：警戒线（链快耗尽时触发 trap——"CSA 耗尽"故障，S4 内存阶段细讲）

### 2. ARM vs TriCore 切换对比

| | ARM Cortex-M | TriCore（本 port） |
|---|---|---|
| 寄存器保存 | 软件把全部寄存器压任务栈 | Upper 已由硬件存入 CSA 链，软件只管 Lower |
| 切换核心动作 | 换栈指针 SP | 换 PCXI 链头 + rslcx + rfe |
| 栈上保存的切换信息 | 全部寄存器现场 | 仅 2 个字：lower CSA id + 临界区嵌套计数 |
| 触发机制 | PendSV 异常 | syscall trap（任务级）/ context SRN（ISR 级） |

### 3. 四函数分工（port.c 代码走读）

1. **出生 `pxPortInitialiseStack`**（103–162 行）：每任务消耗 2 个 CSA（lower+upper，从 FCX 链领取）。
   - `pxUpperCSA[2] = 栈顶`（A10=SP）；`pxUpperCSA[1] = portINITIAL_SYSTEM_PSW`（PSW 初值）
   - `pxLowerCSA[8] = pvParameters`（A4 = 第一个参数寄存器）；`pxLowerCSA[1] = pxCode`（A11 = 任务函数入口）
   - `pxLowerCSA[0] = portINITIAL_LOWER_PCXI | xUpperCsa`（PCXI 链回 upper）
   - 栈顶再压两字：`uxCriticalNesting=0` 和 lower CSA id
   - **任务不是被"调用"的，是被"恢复"出来的**——第一次 RFE 把伪造现场当成真现场恢复。
2. **存 `vPortSaveContext`**（315–355 行）：`mfcr(PCXI)` 拿当前链头；从 upper CSA 取回 SP 当真栈顶；把临界区嵌套计数和 lower CSA id 压栈；TCB 的 `pxTopOfStack` 指向它们。
   - `ucCallDepth` 分支（329–340 行）：在 syscall/中断里调用时，沿 CSA 链往上爬 `ucCallDepth-1` 层，找到"被打断任务"的真上下文——因为 trap/ISR 入口硬件又压了一层。
3. **选 `vTaskSwitchContext()`**：纯软件、平台无关，内核从就绪链表选下一个任务，拨动 `pxCurrentTCB`（S2 调度阶段细讲选择规则）。
4. **取+跳 `vPortLoadContext`**（278–313 行）：从新任务栈顶读回 lower CSA id 和临界区计数，`mtcr(PCXI, ...)` 指向新任务的链；随后 `rslcx`（恢复 lower）+ `rfe`（硬件沿链恢复 upper）→ CPU 在新任务里继续跑。

辅助：`pxPortCsaToAddress`（365–371 行）用 `__extru`/`__insert` 把 CSA id 换算为物理地址（segment<<28 | index<<6）——**CSA id 不是地址**，是 (segment, index) 打包值，调试时手工换算要用。

### 4. 与 S0 排障的联系（ucCallDepth=2）

`portYIELD() = __syscall(0)`（portmacro.h:117）→ Trap class 6 → iLLD trap 框架 → `IFX_CFG_CPU_TRAP_SYSCALL_CPU0_HOOK` → `vPortSyscallHandler(0)` → `vPortSyscallYield()` → `vPortSaveContext(configSYSCALL_CALL_DEPTH=2)`。

S0 的 bug：TC397 空壳工程的 Ifx_Cfg.h 缺 hook 定义 → iLLD 用默认空宏 → yield 变空操作 → Tmr Svc 无法阻塞、优先级 9 空转独占 CPU → 应用任务从未运行。修复 = Ifx_Cfg.h 补两行（extern 声明 + hook 宏）。工程提交 `f588fb5`。

### 5. 调试器观察法（已验证可用）

1. 寄存器窗口看 `FCX` / `PCXI` / `LCX`（CSFR）；
2. PCXI 值经 `pxPortCsaToAddress` 规则换算成地址，Memory 窗口顺链爬调用栈（每节头两字 = PCXI 链指针 + A11 返回地址）；
3. `pxCurrentTCB` 多次暂停采样 → 看到任务轮换 = 调度器工作的直接证据；
4. TCB 与栈都在 `ucHeap`（0x7000xxxx = CPU0 DSPR），栈大小与 configMINIMAL_STACK_SIZE 可互相印证。

## 应用场景

- **立即可用**：调试器里用 CSA 链爬取定位"任务是从哪一路调用过来的"；判断任务切换是否正常（pxCurrentTCB 采样）。
- **可复用方法**：四件套清单（port.c / portmacro.h / FreeRTOSConfig.h / Ifx_Cfg.h hook）是检查任何 RTOS 移植完整性的模板；"换链头而非压全栈"的思路帮助理解 TriCore 上一切上下文相关问题（中断嵌套、trap、函数调用深度）。
- **长期**：S9 多核 AMP 时每核各有独立 FCX/PCXI/CSA 池，本课机制直接迁移。

## 待补充问题

1. `vPortStartFirstTask`（257–276 行）的 PSW.CSC 清零细节与首任务启动全流程——第 2 课。
2. 临界区 `vPortEnter/ExitCritical`（374–399 行）与 `uxCriticalNesting` 嵌套语义的完整讨论——并入 S5 中断管理。
3. 任务删除时 CSA 链归还空闲池的机制（401 行起注释提到 IDLE 任务延迟回收）——S1 任务生命周期时补。
4. CSA 耗尽（LCX 警戒/trap）故障模式与容量估算——S4 内存阶段。

## 关联笔记

- [[FreeRTOS_00_学习路线与问题地图]]（路线总图，SP 系列归属）
- `01_Hardware_硬件层/01_Core/01_AURIX_TC3xx/`（TriCore 内核手册：CSA/PCXI/FCX 硬件章节）
- 工程仓库：github.com/zlmjason/TC397_FreeRTOS（commit `834d8f6` 初始合入、`f588fb5` 排障修复）

## 标签

#FreeRTOS #TC397 #TriCore #CSA #PCXI #上下文切换 #port层 #Port深潜

## Agent 整理记录

- 2026-08-30 对话首讲（第 1 课：机制讲解 + 代码走读 + 验证动作），当时未落盘。
- 2026-08-31 用户指正后补写本笔记（来源：对话讲授内容 + port.c 实读行号，均已核实）。
- 教训沉淀：阶段课程讲完即落盘，不留"只在对话里"的内容（路线 skill 步骤 6 要求）。
