# FreeRTOS × AURIX TC397 总体学习与实践方案

## 核心问题

本项目要回答的不是"读完 FreeRTOS"，而是：

> **在 AURIX TC397（TriCore TC1.6.2P，6 核）上，独立设计、实现、调试一个多任务实时系统，并把 RTOS 原理迁移到车规 AUTOSAR OS 语境。**

拆解为四个子问题：

1. FreeRTOS 的每个内核机制（任务/调度/同步/内存/中断/定时）解决什么问题、代价是什么？
2. 这些机制在 TriCore 上如何落地（CSA、STM、SRN 优先级方向）——与 ARM Cortex-M 说法差在哪？
3. 如何把内核机制、port 层实现、板级现象三者对上号，做到"看到现象能定位机制，读到代码能说出硬件动作"？
4. 哪些结论可以原样搬进 AUTOSAR OS / 车规项目，哪些必须修正？

## 结论

- **路线形态**：以公众号"Arm精选"九页知识长图为主线骨架，按问题驱动重排为 **S0–S9 十个阶段 + SP Port 深潜系列**。每阶段以"能力建成 + TC397 板级验证"为结束标志，不以页码或课时为标志。
- **工具链策略（2026-08-30 修订：单轨 ADS）**：全程 ADS + TASKING Lite。放弃 HighTec GCC + UDE 双轨——S0 排障证明官方例程 + 自有工程骨架足够顺滑，双轨的环境切换成本对零基础学习者不划算。原「移植到 HighTec」里程碑取消，其原理学习目标由 **SP Port 深潜系列**继承。
- **Port 深潜的价值**：port.c 承载上下文切换（CSA/PCXI）、tick 源（STM）、临界区、yield 触发——即调度器原理的全部实体；S0 排障已实战体验其中两条链路。
- **进度跟踪方式**：知识支点见 `FreeRTOS_01_学习TODO.md`，板级实验见 `FreeRTOS_02_实践TODO.md`；每完成一个支点，同步更新清单、落盘笔记、提交工程。

## 背景

### 1. 为什么学（项目背景）

目标岗位/能力方向是**车规 MCU 软件与系统工程师**：需要同时理解芯片硬件行为、RTOS/AUTOSAR 调度语义、以及二者的接口层（port / MCAL / OS）。

FreeRTOS 在这条能力链上的定位：

| 维度 | FreeRTOS 提供的训练 | 对车规工作的迁移价值 |
|---|---|---|
| 机制层 | 任务/调度/同步/内存/中断的最小完整实现，源码可读 | AUTOSAR OS 的 Task/Event/Alarm/Resource 概念同源 |
| 平台层 | port 层是"RTOS 语义 ↔ CPU 硬件"的翻译层 | 理解 OS 移植、上下文切换开销、中断延迟来源 |
| 工程层 | 排障、栈/堆预算、优先级设计、时序分析 | 直接对应 ECU 项目中的调度设计与稳定性问题 |
| 跨架构 | TriCore 与 Cortex-M/R52 的机制差异 | 多平台项目切换、架构选型评审 |

选择 TC397 + 实板而非纯理论的原因：**RTOS 的关键结论都依赖硬件证据**（上下文切换到底存了什么、中断延迟从哪来、栈和 CSA 怎么耗），没有板子就只能背结论。

### 2. 学习者上下文（2026-08-30 对话确认）

| 项 | 值 |
|---|---|
| 开发板 | AURIX TC397 TFT Kit（6 核，TC1.6.2P），板载调试器 |
| 工作工具链 | ~~HighTec GCC + PLS UDE~~ → 2026-08-30 修订：统一为 ADS + TASKING Lite |
| 学习工具链 | ADS（已安装）+ TASKING Lite；已有官方 TC375 FreeRTOS 工程 |
| FreeRTOS 基础 | 基本零基础 → 各阶段从概念起步，实践配足 |
| 目标 | 掌握原理 + 能独立做项目 |

### 3. 工程与环境（2026-10-19 核验）

**工程路径**：`C:\Users\11064\Desktop\TC397_Platform_Jason\ADS\FreeRTOS`（库外独立工程，不在本知识库内）

| 项 | 状态 |
|---|---|
| 芯片/器件层 | AURIX TC397（iLLD/Infra 使用 TC39B 器件层） |
| IDE/编译器 | AURIX Development Studio + TASKING Lite（cctc） |
| 内核版本 | FreeRTOS Kernel V10.5.1 |
| Port | `OS/FreeRTOS/portable/Tasking/TC3/`（port.c + portmacro.h）；GCC port 已从工作区移除，保留在 git 历史 `834d8f6` |
| 堆实现 | `heap_1.c`（其余 heap_2~5 排除编译） |
| 应用代码 | `App_Led1.c`（250ms 闪）、`App_Led2.c`（500ms 闪）、`Cpu0_Main.c`（建两任务 + 启动调度器 + 栈溢出 hook） |
| 板级映射 | LED1 = P13.0（D107），LED2 = P13.1（D108），均低有效 |
| 调试配置 | `FreeRTOS.launch`（ADS 调试会话） |
| Git 远端 | github.com/zlmjason/TC397_FreeRTOS（master） |
| 提交历史 | `834d8f6` 初始合入 OS 层；`f588fb5` S0 排障修复 |
| 已验证基线 | ✅ 双 LED 按预期闪烁；`pxCurrentTCB` 在多任务间轮换；`xTickCount` 递增；任务断点可命中 |

**Port 四件套**（SX 相关检查表，SP 系列主线）：

```text
① port.c           机制实现：切换/tick/临界区/首任务/回收
② portmacro.h      类型、宏、内联原语（portYIELD 等）
③ FreeRTOSConfig.h 硬件地址与参数（configSTM/configCONTEXT_SRC/优先级）
④ Ifx_Cfg.h        trap hook 接线（SYSCALL → vPortSyscallHandler）
```

S0 的实战结论：四件套缺任何一件都可能出现"编译链接全过、tick 正常、任务建成，但就是不调度"的隐性故障。

### 4. 素材来源

- 主线素材：公众号"Arm精选"《FreeRTOS 知识点全解析：从入门到进阶的九页知识长图》，用户以截图提供（9 页）。
- 素材角色：骨架与教学顺序参考；其内容为 **ARM Cortex-M 视角**（SysTick/NVIC/PendSV），TC3xx 落地需重映射（见「关键机制」）。
- 原始图片已归档：[99_Attachments_附件/FreeRTOS_九页知识长图_Arm精选/](../../99_Attachments_附件/FreeRTOS_九页知识长图_Arm精选/)（P01–P09，文件名含页码与主题）。
- 一手资料：FreeRTOS 官方源码（本工程内）、Infineon iLLD 与启动代码、TC3xx 用户手册、ARM Cortex-M7 架构手册。

### 5. 工具链查证（2026-08-30 WebSearch，✅/🟡/❓ 分级）

| 事实 | 状态 | 来源 |
|---|---|---|
| 官方合作 port 仅 TASKING 版：`FreeRTOS-Kernel-Partner-Supported-Ports/Tasking/AURIX_TC3xx` | ✅ | GitHub FreeRTOS 组织 |
| 官方 Demo `FreeRTOS-Partner-Supported-Demos/AURIX_TC375_ADS`（Blinky、Gpt12_Printf），Infineon 称小改可跑任意 TC3xx | ✅ | GitHub FreeRTOS 组织 |
| Infineon 官方例程 `iLLD_TC375_ADS_FreeRTOS_Basic`（两任务+一中断） | ✅ | Infineon/AURIX_code_examples |
| 存在 `aurix tc4xx tricore-gcc` port（PR #30，GCC 语法参考，代差需注意） | 🟡 | 同仓库 activity |
| TC1782 时代有 HighTec GCC + PLS UDE 官方 Demo（CSA 逻辑同源） | ✅（老） | freertos.org 文档存档 |
| TC397 SMP：无官方支持，社区有移植与 AMP 讨论 | ❓ | FreeRTOS 论坛 #18574/#23315 |

## 关键机制

### 1. 能力模型：三层目标

本项目的"学会"按三层判定，缺一层都不算完成：

| 层 | 能力 | 判定证据 |
|---|---|---|
| **概念层** | 能用自己的话讲清机制因果链（为什么需要它、代价是什么、边界在哪） | 复述验收：不看资料讲 3 分钟，经得起追问 |
| **平台层** | 能把机制映射到 TriCore 硬件动作（哪个寄存器、哪条指令、哪条链） | 能在调试器/代码中指出证据；能解释 ARM 与 TriCore 的差异 |
| **工程层** | 能用它做设计决策与排障（选型、预算、优先级、故障定位） | 独立完成实战项目；能用故障树定位人为注入的问题 |

### 2. FreeRTOS 能力地图（学习对象的分解）

```text
执行抽象 → 任务/TCB/状态机                    （S1）
决策机制 → 调度器：优先级/抢占/时间片/Tick      （S2）
协作机制 → 队列/信号量/互斥量/事件组/任务通知   （S3）
资源机制 → heap_1~5/任务栈/CSA 深度            （S4）
外部接口 → 中断管理/FromISR API/优先级边界      （S5）
时间机制 → 软件定时器/延时语义/漂移             （S6）
工程能力 → 系统设计实战/调试排查               （S7、S8）
平台机制 → port 层/多核 AMP/车规映射           （SP、S9）
```

概念依赖：任务 → 调度 → 同步 → 内存 → 中断 → 定时 → 实战 → 调试 → 进阶。与九页长图顺序一致（其顺序本身符合依赖关系，予以沿用）。

### 3. ARM → TriCore 重映射表（本路线相对九页长图的核心增量）

| 九页长图说法（ARM 视角） | TC3xx/TriCore 事实 | 学习价值 |
|---|---|---|
| SysTick 产生系统 Tick | TC3xx 无 SysTick，用每核 STM（System Timer）比较中断 | tick 源是可替换的硬件抽象 |
| NVIC 管理中断，优先级数值小=高 | SRN 优先级数值**大**=高，方向相反；CPU 用 CCPN 做动态阈值 | 移植/配置最易踩的坑 |
| PendSV/SVC 触发上下文切换 | SYSCALL Trap + CSA（硬件上下文保存区）/PCXI 链表 | 上下文切换半硬件化，机制本身值得精读 |
| 任务栈承载全部上下文 | 任务栈 + CSA 链两层；CSA 数量是 TC3xx 特有配置项 | 多一类"CSA 耗尽"故障模式 |
| 单核为主（SMP 新版另论） | TC397 六核，FreeRTOS 实际为 AMP（每核独立内核实例） | 车规多核的真实形态 |
| 未涉及 AUTOSAR | 工作主线为 AUTOSAR OS | 每阶段做车规对照，一鱼两吃 |

### 4. 双轨学习结构与依赖

```text
                    ┌──────────────────────────────────────────┐
                    │  S0 环境奠基（已完成 ✅）                  │
                    │  工程解剖 · 构建机制 · 启动链 · 板级验证   │
                    └───────────────┬──────────────────────────┘
                                    │
          ┌─────────────────────────┴─────────────────────────┐
          │                                                   │
┌─────────▼──────────┐                              ┌─────────▼──────────┐
│ A 轨：内核概念       │                              │ B 轨：平台实现 SP   │
│ S1 任务/TCB         │                              │ SP1 上下文切换 ✅   │
│ S2 调度             │                              │ SP2 临界区/首任务   │
│ S3 同步             │                              │ SP3 tick/中断路径   │
│ S4 内存             │                              │ SP4 栈/CSA 回收     │
│ S5 中断             │                              └─────────┬──────────┘
│ S6 时间             │                                        │
└─────────┬──────────┘                                        │
          └──────────────────────┬─────────────────────────────┘
                                 │
                    ┌────────────▼─────────────┐
                    │ C 轨：工程综合             │
                    │ S7 实战 · S8 调试 · S9 进阶│
                    └──────────────────────────┘
```

- **A 轨**解决"RTOS 语义是什么"；**B 轨**解决"在 TriCore 上到底怎么实现"。两轨交织，但各自可独立推进。
- **交织规则**：A 轨每学一个机制，B 轨有对应实现时优先补上（例如学完 S2 调度，回看 SP1 的 `vTaskSwitchContext` 调用点）。B 轨不阻塞 A 轨。
- **C 轨**只在 A/B 轨积累足够后进入；S7 综合实战是能力试金石。

### 5. 执行方法：六步循环与完成判据

每个知识支点按固定六步推进：

```text
① 对齐问题   这个支点要回答什么、为什么现在学、前置是什么
② 机制讲解   先心智模型，后细节；因果链优先于术语表
③ 代码/硬件  落到具体行号、寄存器、指令；不凭记忆讲
④ 板级实验   设计一个可观察实验；记录测量值与现象
⑤ 复述验收   学习者不看资料复述；偏差当场纠正，不附和
⑥ 沉淀闭环   笔记落盘 + 更新两份清单 + 工程 commit
```

**支点完成判据（四项全过）**：

1. 能脱稿讲清机制因果链；
2. 有代码证据或板级测量证据；
3. 笔记已落盘（对应目录 + 命名规范）；
4. 能回答"边界在哪、什么情况下不成立"。

> 纪律来源：LRN-20260831-001——课程讲授与笔记落盘必须同阶段完成，没落盘不算完成。

### 6. 工具链与 Port 深潜机制

- **单轨 ADS + TASKING**：环境零切换，所有阶段在同一工具链完成。
- **Port 深潜系列**：以"干什么 / 为什么 / 怎么干"三问系统拆解 port 四件套；GCC/TC3 port 保留在 git 历史（`834d8f6`）中作对照阅读材料。
- S0 排障已实战覆盖其中两条链路：include 路径即 port 选择机制、syscall yield 链（trap hook 缺失 → yield 变空操作）。

## 素材分级

| 级别 | 素材 | 用途 |
|---|---|---|
| 精读 | 《Mastering the FreeRTOS Real Time Kernel》（官方免费书）；FreeRTOS 源码 tasks.c / queue.c 关键章节；TASKING TC3xx port.c；iLLD 官方例程 | 机制与证据的主来源 |
| 支撑读 | 九页知识长图（主线骨架）；FreeRTOS 官网 API 文档；TC3xx 用户手册（章节索引见 [[AURIX_TC3xx_Manual_Library_Index]]） | 概念速查与硬件依据 |
| 略读 | FreeRTOS 论坛 TC397 多核/SMP 讨论；21ic 中文移植教程 | 移植期参考 |
| 暂缓 | SafeRTOS 内部、IoT 云平台集成 | 触发条件：工作出现对应需求 |

## 问题驱动学习路线

### 阶段总表

| 阶段 | 核心问题 | 能力目标 | 素材 | 深度 | TC397 实践（验证方式） | 输出物 |
|---|---|---|---|---|---|---|
| S0 环境奠基 ✅ | FreeRTOS 如何"长"在 TC3xx 上？工程由哪些部分组成？ | 会建/改/烧/调 FreeRTOS 工程 | 官方 TC375 例程 + 自有 TC397 空壳工程 | 精读 | 以 ADS/FreeRTOS（TC39B 空壳）为基座合入 OS 层（内核 V10.5.1 + Tasking port + heap_1），双 LED Blinky 跑通 | 无单独笔记（记录进 S1） |
| S1 任务 | TCB 里有什么？状态机怎么转？ | 解释任务生命周期，会建/删/挂起任务 | 九页 P2 + 官方书任务章 | 精读 | 双任务不同周期闪灯；挂起/恢复演示；调试器看 TCB | `01_Kernel/01_Tasks/FreeRTOS_Kernel_Task_...md` |
| S2 调度 | 谁决定运行谁？Tick 怎么驱动？ | 解释抢占/时间片/空闲任务/优先级反转 | 九页 P3 + 官方书调度章 | 精读 | 抢占演示；改 configTICK_RATE_HZ 测粒度；STM tick 源分析 | `01_Kernel/02_Scheduler/FreeRTOS_Kernel_...md` |
| S3 同步通信 | 队列/信号量/互斥量各解决什么？优先级继承如何工作？ | 能为场景选对原语 | 九页 P4 + queue.c | 精读 | 按键中断→二值信号量→任务；三任务优先级反转实验+互斥量修复（可测量对比） | `02_Synchronization/FreeRTOS_Sync_...md` |
| **SP Port 深潜** | port 层干什么、为什么、怎么干？ | 能逐行讲清 port 四件套（port.c / portmacro.h / FreeRTOSConfig.h / Ifx_Cfg.h hook）的机制 | 本工程 TASKING port 逐行精读 + git 历史（`834d8f6`）中 GCC port 对照阅读 | 精读 | 调试器观察 CSA 链 / PCXI / FCX、切换瞬间单步跟踪 | `05_Port/01_PortLayer/FreeRTOS_Port_TC3xx_...md` |
| S4 内存 | heap_1~5 怎么选？栈怎么估？CSA 深度怎么配？ | 会做内存预算，会抓栈溢出 | 九页 P5 + 官方书内存章 | 精读 | uxTaskGetStackHighWaterMark 实测；故意栈溢出触发 hook；CSA 耗尽实验 | `03_Memory/FreeRTOS_Mem_...md` |
| S5 中断 | 为什么必须 FromISR？优先级边界在哪？ | 会配中断优先级，会写安全 ISR | 九页 P6 + TC3xx 手册中断章 | 精读 | 定时器中断→任务通知；越界调 API 触发 configASSERT（反面验证） | `05_Port/02_Interrupts/FreeRTOS_Port_...md` |
| S6 时间管理 | 周期任务为什么会漂移？怎么消除？ | 会用 vTaskDelayUntil/软件定时器 | 九页 P9 局部 + 官方书 | 支撑读 | vTaskDelay vs vTaskDelayUntil 漂移对比实测 | `04_Timing/FreeRTOS_Timing_...md` |
| S7 综合实战 | 多任务系统怎么从需求走到代码？ | 独立完成任务划分/优先级/通信设计 | 九页 P7 温控器案例 | 精读 | TFT Kit 版智能温控器：EVADC 片内温度采集 + TFT 显示 + 按键设定 + GPIO 控制 | 实战总结笔记（位置随内容定） |
| S8 调试排查 | 系统崩了怎么定位？ | 掌握故障树排查法 + 工具链 | 九页 P8 | 精读 | 运行时间统计（configGENERATE_RUN_TIME_STATS+STM）；ADS/TASKING 调试器实操 | 调试方法笔记（FreeRTOS_Port_ 或 Tools_ 前缀） |
| S9 进阶+车规映射 | FreeRTOS 与 AUTOSAR OS 的概念如何对照？ | 能在两种 OS 语境间翻译概念 | 九页 P9 + AUTOSAR OS 规范选读 | 支撑读 | tickless idle 实验；双核 AMP 演示（core0+core1 各跑 FreeRTOS） | FreeRTOS vs AUTOSAR OS 对照笔记 |

### SP Port 深潜系列分解

| 子系列 | 核心问题 | 关键函数/机制 | 状态 |
|---|---|---|---|
| SP1 上下文切换 | 切任务在硬件上发生了什么？ | `pxPortInitialiseStack`、`vPortSave/LoadContext`、CSA/PCXI | ✅ 已讲并落盘 |
| SP2 临界区与首任务启动 | 第一个任务怎么开始？临界区为什么这么实现？ | `vPortStartFirstTask`、`vPortEnter/ExitCritical`、`portASSERT_IF_IN_ISR` | ⬜ 下一站 |
| SP3 tick 与中断路径 | tick 从哪来？ISR 级切换怎么触发？ | `vPortInitTickTimer`、`vPortSystemTickHandler`、`vPortSystemContextHandler`、SRN | ⬜ |
| SP4 栈与 CSA 回收 | 任务退出后资源怎么回收？ | 任务栈布局、`vPortReclaimCSA`、FCD trap | ⬜ |

## 应用场景

- **立即可用**：FreeRTOSConfig.h 调优、任务栈估算方法、FromISR 纪律、优先级反转识别——直接可用于日常涉及 RTOS 的评审与排障。
- **可复用方法**：实验驱动验证法（每个机制都用板级实验证实/证伪）、故障树式调试、跨架构重映射法（ARM 说法 → TriCore 事实的对照表方法可复用于 R52 等平台）。
- **长期洞察**：AUTOSAR OS 概念对照（S9）直接服务车规主线；AMP 多核理解对应 TC397 真实项目形态；SafeRTOS/SAFERTOS 选型判断力。

## 当前假设与待核实问题

| 假设/问题 | 目前依据 | 如何验证 | 状态 |
|---|---|---|---|
| TC397 TFT Kit LED1 = P13.0（D107）、LED2 = P13.1（D108），均低有效 | 官方 Blinky 例程 + 2026-08-30 上板确认双灯闪 | — | ✅ |
| GCC/TC3 port 已随 TC375 例程附带（Infineon 2023，内核 V10.5.1） | 2026-08-30 工程侦察直接确认 | — | ✅ |
| 工程工作区、HighTec 主工程均已就位 | 2026-08-30 工程侦察直接确认 | — | ✅ |
| 官方 TC375 Demo 换器件后可编译运行 | Infineon 官方表述 + S0 实操 | — | ✅ |
| TASKING port.c 的可读性与注释质量足够支撑逐行精读 | port.c 约 460 行，已通读 | SP 系列持续检验 | ✅ |
| TC4xx tricore-gcc port（PR #30） | 仓库 activity 记录 | 已无需核实：工具链改单轨 ADS | 关闭 |
| UDE 支持 FreeRTOS kernel awareness 视图 | PLS 产品线惯例 | 同上，工具链变更 | 关闭 |
| TC397 双核 AMP 两实例可行（无共享调度） | 论坛 AMP 讨论 | S9 实操 | ❓ |

## 学习进度与路线调整

| 日期 | 完成阶段 | 新认识 | 路线调整及原因 |
|---|---|---|---|
| 2026-08-30 | 路线建立 | 官方 port 仅 TASKING 版；九页长图为 ARM 视角需重映射 | 采用双轨方案 A；插入 SX 移植里程碑 |
| 2026-08-30 | 素材归档 | 九页长图原图入库 `99_Attachments_附件/FreeRTOS_九页知识长图_Arm精选/` | 无调整 |
| 2026-08-30 | S0 工程勘察 | GCC/TC3 port 已随例程附带；TC397 空壳工程就位；例程活跃堆实现为 heap_1；LED=P13.0(D107) | SX 素材与工作量重估 |
| 2026-08-30 | S0 代码合入 | 工程建立 git 并推送 GitHub（zlmjason/TC397_FreeRTOS，`834d8f6`） | 无调整 |
| 2026-08-30 | **S0 建成** ✅ | 排障两个真实 bug（port include 撞车；SYSCALL trap hook 缺失致 yield 变空操作、Tmr Svc 独占）；验收三条全过；提交 `f588fb5` | Port 深潜提前至 S0 后 |
| 2026-08-30 | 工具链决策：单轨 ADS | 放弃 HighTec + UDE；SX 转型为 SP Port 深潜系列 | 阶段表与假设表同步更新 |
| 2026-08-31 | SP1 落盘 | 补写 CSA 上下文切换笔记；LED1+LED2 上板确认全闪 | 新增纪律：讲授与落盘同阶段完成 |
| 2026-10-19 | **方案重构** | 工程与笔记状态核验；重新对齐学习/实践方案 | 路线文档升级为总体方案；新增学习/实践两份支点清单；支点记录按需创建 |

## 待补充问题

1. S9 的 AUTOSAR OS 对照深度：届时按工作涉及模块（Os/EcuM/BswM）裁剪。
2. SafeRTOS / 功能安全视角是否扩展为独立阶段（触发条件：工作出现对应需求）。
3. HighTec GCC + UDE 环境如需回归（触发条件：公司项目强制要求），恢复路径：SP 深潜内容照旧有效，另加 GCC port 集成实验（`git restore --source=834d8f6 -- OS/FreeRTOS/portable/GCC/`）。
4. 是否引入第二块板/多核实验环境（触发条件：S9 多核实践需要）。
5. **共享数据迁移到 LMU（暂缓，多核阶段再议）**：当前 FreeRTOS 堆与内核数据位于 DSRAM0（37,457 B：heap_1.o 32,772 B、libc heap 4,160 B、tasks/timers/port 等约 500 B），单核快速路径合理。触发条件：S9 双核 AMP 或出现跨核共享需求；届时改 LSL 将 `ucHeap` 与内核共享数据放入 LMU，并用 `analyze.py` 核归属检查复测。记录日期 2026-10-19。

## 关联笔记

- [[FreeRTOS_01_学习TODO]]（知识支点跟踪清单）
- [[FreeRTOS_02_实践TODO]]（板级实验跟踪清单）
- [[AURIX_TC3xx_Manual_Library_Index]]（官方手册索引：按任务查手册与章节号）
- [[FreeRTOS_Port_TC3xx_PortLayer_Full_Walkthrough]]（SP 主参考：port.c/portmacro.h 逐行注解 + 全流程图）
- [[FreeRTOS_Port_TC3xx_Context_Switch_CSA]]（SP1：任务切换 = 换 CSA 链）
- [[Core_Comparison_Exception_CallStack_M7_vs_TC3xx]]（SP 硬件地基：M7 vs TC3xx 异常模型与调用栈对比）
- [[Core_Comparison_CPU_Pipeline_M7_TC3xx_Engineering]]（M7 vs TC3xx 流水线工程对比）

## 标签

#FreeRTOS #AURIX #TC397 #TriCore #HighTec #ADS #学习路线 #目的驱动精读 #车规MCU #总体方案

## Agent 整理记录

- 2026-08-30 创建路线文档（原《学习路线与问题地图》），依据技能 `purpose-driven-book-study` 七步工作流。
- 2026-10-19 按用户要求重构为《总体学习与实践方案》：新增"为什么学/工程与环境/能力模型/双轨结构/执行方法与完成判据"章节；原路线、假设、进度内容全部保留；文件由 `FreeRTOS_00_学习路线与问题地图.md` 重命名而来（git mv，历史保留）。
- 2026-10-19 工程状态核验：路径、git 提交、port 版本、LED 映射、已验证基线均现场确认，非凭记忆。
