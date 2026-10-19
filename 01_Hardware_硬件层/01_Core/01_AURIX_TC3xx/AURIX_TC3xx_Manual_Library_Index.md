# AURIX TC3xx 官方手册库索引（TC397 工作版）

## 核心问题

手头有大量 AURIX 官方 PDF（TC2xx/TC3xx 架构手册、用户手册、数据手册、开发板手册）。做具体任务时该查哪一本、哪一章？哪些是当前 FreeRTOS × TC397 工作真正需要的，哪些可以暂时忽略？

## 结论

- **P0 必用 7 份**：TriCore 架构手册 vol1/vol2、TC3xx 用户手册 part1/part2、TC39x-B 用户手册、TC39xB 数据手册、Application Kit TC3X7 板级手册。
- **家族手册 + TC39x-B 附录互补**：家族手册给通用模块（STM/SRC/Port/SCU），TC39x-B 附录给芯片专属差异；两份都要有。
- **大文件不入 git**：原始 PDF 保留在 `D:\TriCore_Manunal`；仅 33 页的板级手册复制到 `99_Attachments_附件/AURIX_TC3xx/`（S7 频繁查阅）。
- **与当前工作无关**：TC2xx 全目录、TC38x 用户手册（除非做 TC387）、TriBoard 手册（不是 TFT Kit）、产品宣传册、HighTec 生成 Hex 小技巧。

## 背景

- 资料来源：`D:\TriCore_Manunal`（用户本地资料库）。
- 核验日期：2026-10-19。标题、页数、章节号均从 PDF 首面/目录实际读取，不是按文件名推测。
- 当前工程：TC397 TFT Kit + ADS/TASKING Lite + FreeRTOS V10.5.1。
- 板级手册副本：[Application Kit TC3X7 Manual V2.0](../../../99_Attachments_附件/AURIX_TC3xx/Infineon-ApplicationKitManual_TC3X7-UM-v02_00-EN.pdf)

## 关键机制

### 1. P0 手册清单

| # | 文档 | 本地路径（D:\TriCore_Manunal\） | 页数 | 内容 |
|---|---|---|---:|---|
| 1 | TriCore TC1.6.2 Core Architecture Manual vol1 | `TC3xx_UserManual/TC3xx Architecture vol1.pdf` | 206 | 上下文管理、CSA、中断系统、Trap、内存模型、地址映射 |
| 2 | TriCore TC1.6.2 Core Architecture Manual vol2 | `TC3xx_UserManual/TC3xx Architecture vol2.pdf` | 482 | 指令集（含上下文存取/陷阱指令）、多核与调试相关内容 |
| 3 | AURIX TC3xx User Manual part1 | `TC3xx_UserManual/TC3xx User Manual part1.pdf` | 2080 | 内存映射、SCU/WDT、时钟、Ports、中断路由器 |
| 4 | AURIX TC3xx User Manual part2 | `TC3xx_UserManual/TC3xx User Manual part2.pdf` | 3561 | STM、GTM、EVADC、QSPI、通信外设 |
| 5 | AURIX TC39x-B User Manual | `TC3xx_UserManual/infineon-aurix-tc39x-usermanual-en.pdf` | 1159 | TC39x-B 专属补充（家族手册的芯片差异附录） |
| 6 | TC39xB Data Sheet | `TC3xx_UserManual/TC39xB_DS.pdf` | 519 | 引脚、封装、电气参数、时钟 |
| 7 | Application Kit TC3X7 Manual V2.0 | `TC3xx_开发板资料/Infineon-ApplicationKitManual_TC3X7-UM-v02_00-EN.pdf` | 33 | 板级 LED/按键/TFT/EVADC/接插件（**已复制进附件区**） |

### 2. 按任务查手册（章节号已核对目录）

| 任务 | 首选文档 | 章节 |
|---|---|---|
| Port 上下文切换 / CSA / PCXI | Architecture vol1 | **Ch4 Context Management**：4.1 Context Types、4.1.1 Context Save Area、4.3 CSAs and Context Lists、4.4 Context Switching with Interrupts and Traps、4.5 Context Switching for Function Calls、4.7 Save/Restore Examples、4.8 Context Management Registers、4.9 Accessing CSA Memory、4.10 CSA Placement |
| 上下文存取指令（`svlcx` / `rslcx` / `rfe`） | Architecture vol2 | 2.11 Context Related Instructions（2.11.2 Context Loading and Storing） |
| 中断进入/退出、向量表、ICR | Architecture vol1 | **Ch5 Interrupt System**：5.1.1 ICR、5.1.2 CPU operation on interrupt request、5.1.3 Entering ISR、5.2 Exiting ISR、5.3 Interrupt Vector Table |
| Trap / SYSCALL | Architecture vol1 | **Ch6 Trap System**：6.3.4 Context Management（Class 3）、6.3.7 System Call（Class 6）；vol2 2.12.6 Trap Instructions |
| 中断路由 / SRN / SRPN / TOS / SETR | TC3xx UM part1 | **Ch16 Interrupt Router (IR)**（16.5.1 SRC Index Number、16.13 Registers） |
| STM tick / 比较中断 | TC3xx UM part2 | **Ch27 System Timer (STM)** |
| 内存映射 / DSPR / PSPR / LMU | TC3xx UM part1 | **Ch2 Memory Maps (MEMMAP)**；Arch vol1 **Ch8 Address Map and Memory Configuration** |
| SCU / 复位 / WDG | TC3xx UM part1 | **Ch9 SCU**（9.4 Watchdog Timers） |
| 时钟树 / PLL / CCU | TC3xx UM part1 | **Ch10 Clocking System** |
| Port / LED / 引脚复用 | TC3xx UM part1 | **Ch14 General Purpose I/O Ports and Peripheral I/O Lines (Ports)** |
| EVADC（S7 温度采集） | TC3xx UM part2 | **Ch32 Enhanced Versatile Analog-to-Digital Converter (EVADC)** |
| GTM（PWM/定时） | TC3xx UM part2 | **Ch28 GTM** |
| QSPI | TC3xx UM part2 | **Ch37 QSPI** |
| 板级 LED/按键/TFT/接插件 | Application Kit TC3X7 Manual | 全文（33 页，附件区可开） |
| 引脚/封装/电气 | TC39xB Data Sheet | 按需 |
| TC397 专属寄存器差异 | TC39x-B User Manual | 附录部分（配合家族手册查） |

### 3. P1 · 备用（按需再查）

| 文档 | 路径 | 页数 | 说明 |
|---|---|---:|---|
| AURIX 2G Spec 汇编 | `TC3xx_UserManual/AURIX 2G Spec Tong.pdf` | 5794 | 大型规格汇编；家族手册找不到时做全文搜索，不适合顺序读 |
| TriBoard TC3X7 Manual | `TC3xx_开发板资料/TC3X7开发板说明.pdf` | 51 | 针对 TriBoard TC3X7（V1.0），不是 TFT Kit；有 TriBoard 时才用 |
| TC38x User Manual | `TC3xx_UserManual/Infineon-AURIX_TC38x-UserManual-v02_00-EN.pdf` | 1082 | TC38x 专属；做 TC387 时再用 |
| Online Engineering Tools Getting Started | `TC3xx_开发板资料/Infineon-Online_Engineering_Tools-GettingStarted-v01_00-CN.pdf` | — | ADS/工具入门；优先级低 |

### 4. P2 · 当前 RTOS 线不需要

| 资料 | 原因 |
|---|---|
| `TC2xx/` 整个目录（275 手册、TC29x UM/DS、TC297 板说明） | TC2xx 平台，与 TC397 无关（TriCore 架构概念重叠，但寄存器/模块不同） |
| `Infineon-TC2x7_ApplicationKitManual-UM-v01_00-EN.pdf` | TC2x7 板子 |
| `Infineon-TriCore_Family_BR-ProductBrochure...pdf` | 产品宣传册，无技术细节 |
| `AURIX_Training_FunctionSafety.pdf` | 功能安全培训，归入功能安全线（ISO 26262），不是 RTOS 线 |
| `MCAL_MSC模块使用手册_一汽.docx` | AUTOSAR MCAL MSC 模块，后续 AUTOSAR 线使用 |
| `TC3xx_开发板资料/070cac083ab949289d93c0703e582f00.pdf` | 2 页 HighTec 生成 Hex 小技巧；当前用 ADS |

### 5. 使用纪律

1. **先查章节号再读**：本页的"按任务查手册"表优先；家族手册与 TC39x 附录对照读。
2. **区分规范性与二手资料**：FreeRTOS port.c 的注释、论坛说法与 UM/架构手册冲突时，以官方手册为准，并在笔记中标注版本与章节。
3. **笔记引用格式**：`[文档简称] Ch.X.Y（p.N）`，例如 `[TC3xx UM part2] Ch27.4（STM 比较模式）`。
4. **版本跟踪**：手册换版时更新本表页数与章节号，并在「Agent 整理记录」留痕。

## 应用场景

- **Port 深潜**：CSA/切换查 Architecture vol1 Ch4；中断/Trap 查 Ch5/Ch6；寄存器定义查 Ch3。
- **S2/S5/S6**：STM 查 UM part2 Ch27；中断路由查 part1 Ch16。
- **S7 综合实战**：板级连接查 Application Kit 手册；EVADC 查 UM part2 Ch32；Port 查 part1 Ch14。
- **S9 多核**：Architecture vol2 + UM 多核章节（章号待补）。
- **日常排障**：先查本索引定位章节，再回到 `.map`/调试器验证。

## 关联笔记

- [[AURIX_TC3xx_Core_Manual_Detailed_Mermaid]]（TC3xx 内核手册整理）
- [[FreeRTOS_Port_TC3xx_Context_Switch_CSA]]（CSA/上下文切换，对应 Architecture vol1 Ch4）
- [[FreeRTOS_Port_TC3xx_PortLayer_Full_Walkthrough]]（port.c 逐行注解）
- [[HW_Boot_AURIX_TC3xx_SSW_START_to_coreX_main]]（启动流程）
- [[TC3xx_Mem_RAM_DSPR_Structure_Bus_Interface_CPU_Mapping]]（DSPR 结构）
- [[Core_Comparison_Exception_CallStack_M7_vs_TC3xx]]（跨架构异常模型对比）
- 板级手册：[Application Kit TC3X7 Manual V2.0](../../../99_Attachments_附件/AURIX_TC3xx/Infineon-ApplicationKitManual_TC3X7-UM-v02_00-EN.pdf)

## 待补充问题

1. UM 中多核（Multi-core）章节的具体章号——S9 前补。
2. 板级手册中 LED/按键/TFT/EVADC 的引脚与通道对应——S7 前补。
3. TC39xB 数据手册的引脚复用表与板级实际连接核对——S7 前补。
4. 各手册封面版本号（vXX_XX）登记到本表，便于版本跟踪。

## 标签

#AURIX #TC3xx #TC397 #手册索引 #参考资源 #FreeRTOS

## Agent 整理记录

- 2026-10-19 创建。依据 `D:\TriCore_Manunal` 实际文件核验标题/页数；章节号来自各 PDF 目录页（Architecture vol1 Ch4/5/6、UM part1 Ch2/9/10/14/16、UM part2 Ch27/28/32/37）。
- 大文件保留在 D 盘，仅将 33 页板级手册复制到 `99_Attachments_附件/AURIX_TC3xx/`。
