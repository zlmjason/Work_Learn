# TC3xx 程序运行模型（Port 前置学习主线）

## 核心问题

在精读/编写 FreeRTOS port 层之前，必须回答：

> **TriCore 的函数调用、中断进入、任务切换，在硬件上到底保存了什么、恢复了什么？CSA 链、PCXI/FCX/LCX、PSW.IS、A10/ISP 如何协同？**

如果这些机制不清楚，port.c 里的 `pxPortInitialiseStack`、`vPortSaveContext/LoadContext`、`vPortStartFirstTask` 就只是"看起来能跑的汇编"，无法判断对错。

## 结论

- 把「程序运行模型」作为 **SP Port 深潜的前置主线（EM）**，先于 SP2 临界区/首任务学习。
- 学习顺序按硬件依赖组织：**寄存器 → Upper/Lower Context → CSA → FCX/PCXI/LCX → CALL/RET → IRQ 入口 → BISR/SVLCX/RSLCX → Trap → 嵌套中断 → M7 对比 → 调试观察 → 容量预算**。
- 主教材是两份自包含 HTML（交互实验台 + 启动流程 C/汇编对照），官方依据是 Architecture vol1 Ch4/5/6 与 TC3xx UM part1 Ch16。
- 每个阶段以"能脱稿回答 + 能在调试器指出证据"为完成判据；最后用 7 个验证用例闭环。

## 背景

- 建立日期：2026-10-20。
- 芯片/工具链：TC397 TFT Kit、ADS + TASKING Lite、FreeRTOS V10.5.1（TASKING port）。
- 触发原因：port 层与目标芯片的程序运行模型强相关；用户决定先系统学习运行模型，再继续 SP2。
- 材料：
  - [AURIX TC3xx CSA 与栈交互实验台](./AURIX_TC3xx_CSA_Context_and_Stack_Interactive.html)（18 节，含总图、寄存器、CSA、三指针、CALL/RET、IRQ、嵌套、M7 对比、调试与 7 个用例）
  - [启动流程 C/汇编对照](./AURIX_Startup_C_Assembly.html)（`_START` → `core0_main`，含 Phase3 CSA 链表构建；每节带 **先想一想 / 举一反三 / 如果写错会怎样**，共 38 道思考题）
  - 官方手册章节索引：[[AURIX_TC3xx_Manual_Library_Index]]

## 关键机制

### 1. 学习路线（EM0–EM12）

| 阶段 | 主题 | 主材料（HTML 章节） | 核心问题 | 验证方式 |
|---|---|---|---|---|
| EM0 | 总图与寄存器 | §0–1 | 程序员可见寄存器有哪些？A0/A1/A8/A9 为什么特殊？ | 画出 A/D 寄存器分类图 |
| EM1 | Upper / Lower Context | §2 | 为什么分两组？各包含哪些寄存器？为什么不在异常入口一次保存全部？ | 默写两组寄存器列表 |
| EM2 | CSA 内存布局 | §3 | Upper/Lower CSA 的字段布局？CSA 指针为什么不是普通地址？ | 手工解码一个 PCXI 值 |
| EM3 | FCX / PCXI / LCX | §4、§6 | 三指针各自指向什么？为什么 PCXI 不是一个普通地址？ | 调试器读出三值并解释 |
| EM4 | 保存/恢复的链表本质 | §5 | 保存时硬件往哪挂？恢复时怎么取？ | 画出一次保存前后的链 |
| EM5 | CALL / RET | §7 | CALL 硬件保存什么？A10 普通栈参与吗？Lower 为什么不随 CALL 自动保存？ | 单层 CALL/RET 的 CSA 守恒实验 |
| EM6 | IRQ 入口与栈切换 | §8、§11 | A10、ISP、PSW.IS 如何配合？为什么先保存 A10 再切 ISP？ | IRQ 从 USTACK 切 ISTACK 实验 |
| EM7 | BISR / SVLCX / RSLCX | §9 | 三条指令的区别？典型 C ISR 为什么要存 Lower？ | BISR/RSLCX 配对实验 |
| EM8 | Trap 与 IRQ 的异同 | §10、§15 | Trap 特有信息？A11 返回地址差异？FCD/FCU/NEST 是什么？ | 对照表 + trap 入口观察 |
| EM9 | 嵌套中断 | §12–13 | 第二层 IRQ 进入时 CSA 链如何增长？RFE 如何回退？ | 嵌套 IRQ 实验 |
| EM10 | 与 Cortex-M7 对比 | §14 + [[Core_Comparison_Exception_CallStack_M7_vs_TC3xx]] | 两套异常模型的本质差异？最容易错误类比的地方？ | 口头对比 + 表格 |
| EM11 | 调试观察真实 CSA 链 | §16 | 断点打在哪？记录哪些寄存器？如何解码 PCXI？ | 在 ADS 中走一遍 |
| EM12 | 容量预算 | §18 | CSA 数量、ISTACK/USTACK 大小怎么估？ | 用 map 数据算一遍 |

### 2. 与 port.c 的映射

| port.c 函数/动作 | 运行模型概念 | 手册章节 |
|---|---|---|
| `pxPortInitialiseStack` 领 2 个 CSA、填 A4/A11/A10/PSW | Upper/Lower CSA 布局、PCXI 编码、FCX | Arch vol1 Ch4.1/4.3/4.8/4.10 |
| `vPortSaveContext` / `vPortLoadContext` | PCXI 链头、Upper/Lower 保存恢复、`ucCallDepth` | Arch vol1 Ch4.4/4.5/4.7 |
| `vPortStartFirstTask` 的 `rslcx` + `rfe` | 首次恢复、PSW.CSC 清零 | Arch vol1 Ch4.7；vol2 2.11 |
| `vPortSyscallYield` 的 trap class 6 | SYSCALL trap、trap 入口压栈深度 | Arch vol1 Ch6.3.7 |
| `vPortSystemTickHandler` / `portYIELD_FROM_ISR` | IRQ 入口、ISP 切换、上下文 SRN | Arch vol1 Ch5；UM part1 Ch16 |
| `uxCriticalNesting` 存栈顶 | 任务栈顶两字、上下文切换的软件部分 | 本工程 `port.c` |

### 3. 检查点（能脱稿回答才算过）

1. Upper Context 的 16 个字具体是哪些寄存器？Lower 呢？
2. CSA 的 64 字节里，前几个字分别是什么？
3. PCXI 为什么不是普通地址？段号/索引如何编码？
4. FCX、PCXI、LCX 三者分别在什么时刻改变？
5. 一次普通 CALL 硬件保存了哪些寄存器？A10 数据栈变了吗？
6. IRQ 入口为什么先保存 A10 再把它改成 ISP？PSW.IS 的作用是什么？
7. 典型 C ISR 为什么需要 `bisr` + `svlcx`/`rslcx`？极小 ISR 为什么可以省？
8. Trap 与 IRQ 的相同点/不同点？FCD 与 FCU 的本质差异？
9. 嵌套 IRQ 时 CSA 链如何增长、RFE 如何回退？
10. 调试器里如何从 PCXI 解码出一条真实 CSA 链？

### 4. 实践用例（对应 HTML §17）

| ID | 用例 | 目标 | 观察点 |
|---|---|---|---|
| E-EM-01 | 单层 CALL/RET 的 CSA 守恒 | 验证 CALL 领 CSA、RET 归还 | CALL 前后 FCX/PCXI |
| E-EM-02 | IRQ 从 USTACK 切到 ISTACK | 验证 A10/ISP/PSW.IS | 中断前后 A10、PSW.IS |
| E-EM-03 | 嵌套 IRQ 不重复加载 ISP | 验证 IS 已置位时不再切栈 | 第二层 IRQ 的 A10 |
| E-EM-04 | BISR/RSLCX 配对 | 验证 Lower Context 保存 | 指令前后 PCXI、CSA 内容 |
| E-EM-05 | 故意跳过 RSLCX | 观察链不平衡的后果 | 返回地址/链长度 |
| E-EM-06 | FCD 预警 | 观察 LCX 触发上下文耗尽 trap | LCX 与 trap class 3 |
| E-EM-07 | PSW.IS 与 A10 故意不一致 | 理解"IS 只是首次切栈开关" | 中断入口 A10 行为 |

### 5. 材料索引

- 交互实验台：[AURIX_TC3xx_CSA_Context_and_Stack_Interactive.html](./AURIX_TC3xx_CSA_Context_and_Stack_Interactive.html)
- 启动流程对照：[AURIX_Startup_C_Assembly.html](./AURIX_Startup_C_Assembly.html)
- 官方手册：[[AURIX_TC3xx_Manual_Library_Index]]
  - Architecture vol1 **Ch4**（Context Management）、**Ch5**（Interrupt System）、**Ch6**（Trap System）、**Ch8**（Address Map）
  - Architecture vol2 2.11（Context Instructions）、2.12.6（Trap Instructions）
  - TC3xx UM part1 **Ch16**（Interrupt Router/IR）
- 已有笔记：
  - [[FreeRTOS_Port_TC3xx_Context_Switch_CSA]]
  - [[FreeRTOS_Port_TC3xx_PortLayer_Full_Walkthrough]]
  - [[Core_Comparison_Exception_CallStack_M7_vs_TC3xx]]

## 应用场景

- **读 port.c**：每个函数都能对应到运行模型的硬件动作，不再"照抄汇编"。
- **调试切换**：能从 FCX/PCXI/LCX 与 CSA 链判断切换是否正常。
- **中断设计**：理解 ISR 的栈切换、嵌套、延迟来源。
- **故障分析**：FCD/FCU/NEST、CSA 耗尽、PSW.IS 配错等。
- **多核（S9）**：每核独立 CSA/FCX/PCXI 的基础。

## 关联笔记

- [[FreeRTOS_00_总体学习与实践方案]]（总纲；EM 作为 SP 前置）
- [[FreeRTOS_01_学习TODO]]（EM 知识点清单）
- [[FreeRTOS_02_实践TODO]]（EM 验证用例）
- [[FreeRTOS_Port_TC3xx_Context_Switch_CSA]]（SP1）
- [[FreeRTOS_Port_TC3xx_PortLayer_Full_Walkthrough]]（port.c 逐行）
- [[Core_Comparison_Exception_CallStack_M7_vs_TC3xx]]（M7 对比）
- [[AURIX_TC3xx_Manual_Library_Index]]（手册章节）

## 待补充问题

1. 交互实验台的 18 节内容需逐节做"能脱稿回答"验收；当前仅建立路线。
2. 7 个验证用例需在 ADS 调试器中逐个执行并记录数据。
3. 是否把 HTML §17 的用例扩展为可自动化脚本（后续结合 `aurix-build-analyze` 的核归属/CSA 检查）。
4. FCD/FCU/NEST 的具体 trap 向量与处理函数需在 TC397 上确认（Arch vol1 Ch6.3.4/Ch15）。

## 标签

#FreeRTOS #TC3xx #TC397 #程序运行模型 #CSA #上下文切换 #Port前置 #学习路线

## Agent 整理记录

- 2026-10-20 创建。依据用户提供的两份 HTML（CSA 交互实验台、启动流程 C/汇编对照）与官方手册章节索引建立 EM 主线；HTML 从知识库根目录移入本专区。
- 学习顺序按硬件依赖排列；检查点与验证用例摘自 HTML §17，并映射到本工程 port.c 与调试器观察点。
