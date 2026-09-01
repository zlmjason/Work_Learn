# FreeRTOS × AURIX TC397 目的驱动学习路线与问题地图

## 核心问题

本路线要回答的不是"读完 FreeRTOS"，而是：

> **在 AURIX TC397（TriCore TC1.6.2P，6 核）上，独立设计、实现、调试一个多任务实时系统，并把 RTOS 原理迁移到车规 AUTOSAR OS 语境。**

拆解为四个子问题：

1. FreeRTOS 的每个内核机制（任务/调度/同步/内存/中断/定时）解决什么问题、代价是什么？
2. 这些机制在 TriCore 上如何落地（CSA、STM、SRN 优先级方向）——与 ARM Cortex-M 说法差在哪？
3. 没有现成 HighTec GCC port 时，如何把 TASKING port 适配过来并验证正确性？
4. 哪些结论可以原样搬进 AUTOSAR OS / 车规项目，哪些必须修正？

## 结论

- **路线形态**：以公众号"Arm精选"九页知识长图为主线骨架，按问题驱动重排为 **11 个里程碑**（S0–S9 + SX 移植里程碑），每阶段以"能力建成 + TC397 板级验证"为结束标志，不以页码为标志。
- **工具链策略（2026-08-30 修订：单轨 ADS）**：全程 ADS + TASKING Lite。用户拍板放弃 HighTec GCC + UDE 双轨——S0 排障证明官方例程 + 自有工程骨架足够顺滑，双轨的环境切换成本对零基础学习者不划算。原 SX「移植到 HighTec」里程碑**取消**，其原理学习目标由「Port 深潜」系列继承：不动手移植，改为逐行吃透现有 TASKING port + 对照阅读 git 历史中的 GCC port。
- **Port 深潜的价值不变**：port.c 承载上下文切换（CSA/PCXI）、tick 源（STM）、临界区、yield 触发——即调度器原理的全部实体；S0 排障已实战体验其中两条链路。

## 背景

### 素材来源

- 主线素材：公众号"Arm精选"《FreeRTOS 知识点全解析：从入门到进阶的九页知识长图》，用户以截图提供（9 页）。
- 素材角色：骨架与教学顺序参考；其内容为 **ARM Cortex-M 视角**（SysTick/NVIC/PendSV），TC3xx 落地需重映射（见「关键机制」）。
- 原始图片已归档：[99_Attachments_附件/FreeRTOS_九页知识长图_Arm精选/](../../99_Attachments_附件/FreeRTOS_九页知识长图_Arm精选/)（P01–P09，文件名含页码与主题）。

### 学习者上下文（2026-08-30 对话确认）

| 项 | 值 |
|---|---|
| 开发板 | AURIX TC397 TFT Kit（6 核，TC1.6.2P），板载调试器 |
| 工作工具链 | ~~HighTec GCC + PLS UDE~~ → 2026-08-30 修订：统一为 ADS + TASKING Lite |
| 学习工具链 | ADS（已安装）+ TASKING Lite；已有官方 TC375 FreeRTOS 工程 |
| FreeRTOS 基础 | 基本零基础 → 各阶段从概念起步，实践配足 |
| 目标 | 掌握原理 + 能独立做项目 |

### 工具链查证（2026-08-30 WebSearch，✅/🟡/❓ 分级）

| 事实 | 状态 | 来源 |
|---|---|---|
| 官方合作 port 仅 TASKING 版：`FreeRTOS-Kernel-Partner-Supported-Ports/Tasking/AURIX_TC3xx` | ✅ | GitHub FreeRTOS 组织 |
| 官方 Demo `FreeRTOS-Partner-Supported-Demos/AURIX_TC375_ADS`（Blinky、Gpt12_Printf），Infineon 称小改可跑任意 TC3xx | ✅ | GitHub FreeRTOS 组织 |
| Infineon 官方例程 `iLLD_TC375_ADS_FreeRTOS_Basic`（两任务+一中断） | ✅ | Infineon/AURIX_code_examples |
| 存在 `aurix tc4xx tricore-gcc` port（PR #30，GCC 语法参考，代差需注意） | 🟡 | 同仓库 activity |
| TC1782 时代有 HighTec GCC + PLS UDE 官方 Demo（CSA 逻辑同源） | ✅（老） | freertos.org 文档存档 |
| TC397 SMP：无官方支持，社区有移植与 AMP 讨论 | ❓ | FreeRTOS 论坛 #18574/#23315 |

## 关键机制

### 1. FreeRTOS 能力地图（学习对象的分解）

```text
执行抽象 → 任务/TCB/状态机                    （S1）
决策机制 → 调度器：优先级/抢占/时间片/Tick      （S2）
协作机制 → 队列/信号量/互斥量/事件组/任务通知   （S3）
资源机制 → heap_1~5/任务栈/CSA 深度            （S4）
外部接口 → 中断管理/FromISR API/优先级边界      （S5）
时间机制 → 软件定时器/延时语义/漂移             （S6）
工程能力 → 系统设计实战/调试排查               （S7、S8）
平台机制 → port 层/多核 AMP/车规映射           （SX、S9）
```

概念依赖：任务 → 调度 → 同步 → 内存 → 中断 → 定时 → 实战 → 调试 → 进阶。与九页长图顺序一致（其顺序本身符合依赖关系，予以沿用）。

### 2. ARM → TriCore 重映射表（本路线相对九页长图的核心增量）

| 九页长图说法（ARM 视角） | TC3xx/TriCore 事实 | 学习价值 |
|---|---|---|
| SysTick 产生系统 Tick | TC3xx 无 SysTick，用每核 STM（System Timer）比较中断 | tick 源是可替换的硬件抽象 |
| NVIC 管理中断，优先级数值小=高 | SRN 优先级数值**大**=高，方向相反；CPU 取 PCPN 阈值 | 移植/配置最易踩的坑 |
| PendSV/SVC 触发上下文切换 | SYSCALL Trap + CSA（硬件上下文保存区）/PCXI 链表 | 上下文切换半硬件化，机制本身值得精读 |
| 任务栈承载全部上下文 | 任务栈 + CSA 链两层；CSA 数量是 TC3xx 特有配置项 | 多一类"CSA 耗尽"故障模式 |
| 单核为主（SMP 新版另论） | TC397 六核，FreeRTOS 实际为 AMP（每核独立内核实例） | 车规多核的真实形态 |
| 未涉及 AUTOSAR | 工作主线为 AUTOSAR OS | 每阶段做车规对照，一鱼两吃 |

### 3. 工具链与 Port 深潜机制（2026-08-30 修订）

- **单轨 ADS + TASKING**：环境零切换，所有阶段在同一工具链完成。
- 原 SX 的"移植"动作取消，其原理目标由 **Port 深潜系列**继承（S0 后插入，已开课）：以"干什么 / 为什么 / 怎么干"三问系统拆解 port 四件套（port.c + portmacro.h + FreeRTOSConfig.h + Ifx_Cfg.h hook）；GCC/TC3 port 保留在 git 历史（`834d8f6`）中作对照阅读材料。
- S0 排障已实战覆盖其中两条链路：include 路径即 port 选择机制、syscall yield 链（trap hook 缺失 → yield 变空操作）。

## 素材分级

| 级别 | 素材 | 用途 |
|---|---|---|
| 精读 | 《Mastering the FreeRTOS Real Time Kernel》（官方免费书）；FreeRTOS 源码 tasks.c / queue.c 关键章节；TASKING TC3xx port.c；iLLD 官方例程 | 机制与证据的主来源 |
| 支撑读 | 九页知识长图（主线骨架）；FreeRTOS 官网 API 文档；TC3xx 用户手册（STM / 中断 / CSA 章节） | 概念速查与硬件依据 |
| 略读 | FreeRTOS 论坛 TC397 多核/SMP 讨论；21ic 中文移植教程 | 移植期参考 |
| 暂缓 | SafeRTOS 内部、IoT 云平台集成 | 触发条件：工作出现对应需求 |

## 问题驱动学习路线

| 阶段 | 核心问题 | 能力目标 | 素材 | 深度 | TC397 实践（验证方式） | 输出物 |
|---|---|---|---|---|---|---|
| S0 环境奠基 | FreeRTOS 如何"长"在 TC3xx 上？工程由哪些部分组成？ | 会建/改/烧/调 FreeRTOS 工程 | 官方 TC375 例程 + 自有 TC397 空壳工程 | 精读 | 以 ADS/FreeRTOS（TC39B 空壳）为基座合入 OS 层（内核 V10.5.1 + Tasking port + heap_1），双 LED Blinky 跑通 | 无单独笔记（记录进 S1） |
| S1 任务 | TCB 里有什么？状态机怎么转？ | 解释任务生命周期，会建/删/挂起任务 | 九页 P2 + 官方书任务章 | 精读 | 双任务不同周期闪灯；挂起/恢复演示；调试器看 TCB | `01_Kernel/01_Tasks/FreeRTOS_Kernel_Task_...md` |
| S2 调度 | 谁决定运行谁？Tick 怎么驱动？ | 解释抢占/时间片/空闲任务/优先级反转 | 九页 P3 + 官方书调度章 | 精读 | 抢占演示；改 configTICK_RATE_HZ 测粒度；STM tick 源分析 | `01_Kernel/02_Scheduler/FreeRTOS_Kernel_...md` |
| S3 同步通信 | 队列/信号量/互斥量各解决什么？优先级继承如何工作？ | 能为场景选对原语 | 九页 P4 + queue.c | 精读 | 按键中断→二值信号量→任务；三任务优先级反转实验+互斥量修复（可测量对比） | `02_Synchronization/FreeRTOS_Sync_...md` |
| **SP Port 深潜**（原 SX 移植里程碑转型，已开课） | port 层干什么、为什么、怎么干？ | 能逐行讲清 port 四件套（port.c / portmacro.h / FreeRTOSConfig.h / Ifx_Cfg.h hook）的机制 | 本工程 TASKING port 逐行精读 + git 历史（`834d8f6`）中 GCC port 对照阅读 | 精读 | 调试器观察 CSA 链 / PCXI / FCX、切换瞬间单步跟踪（第 1 课上下文切换已讲） | `05_Port/01_PortLayer/FreeRTOS_Port_TC3xx_...md` |
| S4 内存 | heap_1~5 怎么选？栈怎么估？CSA 深度怎么配？ | 会做内存预算，会抓栈溢出 | 九页 P5 + 官方书内存章 | 精读 | uxTaskGetStackHighWaterMark 实测；故意栈溢出触发 hook；CSA 耗尽实验 | `03_Memory/FreeRTOS_Mem_...md` |
| S5 中断 | 为什么必须 FromISR？优先级边界在哪？ | 会配中断优先级，会写安全 ISR | 九页 P6 + TC3xx 手册中断章 | 精读 | 定时器中断→任务通知；越界调 API 触发 configASSERT（反面验证） | `05_Port/02_Interrupts/FreeRTOS_Port_...md` |
| S6 时间管理 | 周期任务为什么会漂移？怎么消除？ | 会用 vTaskDelayUntil/软件定时器 | 九页 P9 局部 + 官方书 | 支撑读 | vTaskDelay vs vTaskDelayUntil 漂移对比实测 | `04_Timing/FreeRTOS_Timing_...md` |
| S7 综合实战 | 多任务系统怎么从需求走到代码？ | 独立完成任务划分/优先级/通信设计 | 九页 P7 温控器案例 | 精读 | TFT Kit 版智能温控器：EVADC 片内温度采集 + TFT 显示 + 按键设定 + GPIO 控制 | 实战总结笔记（位置随内容定） |
| S8 调试排查 | 系统崩了怎么定位？ | 掌握故障树排查法 + 工具链 | 九页 P8 | 精读 | 运行时间统计（configGENERATE_RUN_TIME_STATS+STM）；ADS/TASKING 调试器实操 | 调试方法笔记（FreeRTOS_Port_ 或 Tools_ 前缀） |
| S9 进阶+车规映射 | FreeRTOS 与 AUTOSAR OS 的概念如何对照？ | 能在两种 OS 语境间翻译概念 | 九页 P9 + AUTOSAR OS 规范选读 | 支撑读 | tickless idle 实验；双核 AMP 演示（core0+core1 各跑 FreeRTOS） | FreeRTOS vs AUTOSAR OS 对照笔记 |

## 应用场景

- **立即可用**：FreeRTOSConfig.h 调优、任务栈估算方法、FromISR 纪律、优先级反转识别——直接可用于日常涉及 RTOS 的评审与排障。
- **可复用方法**：实验驱动验证法（每个机制都用板级实验证实/证伪）、故障树式调试、跨架构重映射法（ARM 说法 → TriCore 事实的对照表方法可复用于 R52 等平台）。
- **长期洞察**：AUTOSAR OS 概念对照（S9）直接服务车规主线；AMP 多核理解对应 TC397 真实项目形态；SafeRTOS/SAFERTOS 选型判断力。

## 当前假设与待核实问题

| 假设/问题 | 目前依据 | 如何验证 | 状态 |
|---|---|---|---|
| TC397 TFT Kit LED1 = P13.0（D107）、LED2 = P13.1（均低有效） | 官方 Blinky 例程 + 2026-08-30 上板确认双灯闪 | — | ✅ |
| GCC/TC3 port 已随 TC375 例程附带（Infineon 2023，内核 V10.5.1），SX 无需汇编翻译 | 2026-08-30 工程侦察直接确认 | SX 时与 TASKING port 逐行对照 | ✅ |
| S0 基座 ADS/FreeRTOS（TC39B 空壳）、SX 目标 Hightec/TC397_Jason_Project_Master 均已就位 | 2026-08-30 工程侦察直接确认 | S0/SX 实操 | ✅ |
| 官方 TC375 Demo 换器件后可直接编译 | Infineon 官方表述 | S0 实操 | ✅（官方声称）/ 🟡（本板未试） |
| TASKING port.c 汇编占比决定 SX 工作量 | port.c 约 460 行 | SX 开工时通读评估 | 🟡 |
| TC4xx tricore-gcc port（PR #30） | 仓库 activity 记录 | 已无需核实：SX 移植取消，工具链改单轨 ADS（2026-08-30） | 关闭 |
| UDE 支持 FreeRTOS kernel awareness 视图 | PLS 产品线惯例 | 同上，工具链变更，关闭 | 关闭 |
| TC397 双核 AMP 两实例可行（无共享调度） | 论坛 AMP 讨论 | S9 实操 | ❓ |

## 学习进度与路线调整

| 日期 | 完成阶段 | 新认识 | 路线调整及原因 |
|---|---|---|---|
| 2026-08-30 | 路线建立 | 官方 port 仅 TASKING 版；九页长图为 ARM 视角需重映射 | 采用双轨方案 A；插入 SX 移植里程碑 |
| 2026-08-30 | 素材归档 | 九页长图原图入库 `99_Attachments_附件/FreeRTOS_九页知识长图_Arm精选/` | 无调整 |
| 2026-08-30 | S0 工程勘察 | GCC/TC3 port 已随例程附带（SX 从"汇编翻译"降级为"集成验证"）；TC397 空壳工程与 HighTec 主工程就位；例程活跃堆实现为 heap_1；LED=P13.0(D107) | SX 素材与工作量重估，阶段划分不变 |
| 2026-08-30 | S0 代码合入 | 工程已建 git 并推送 GitHub（zlmjason/TC397_FreeRTOS，initial commit `834d8f6`）：OS 层+双任务闪灯代码就位，待 ADS 界面配置编译 | 无调整 |
| 2026-08-30 | **S0 建成** ✅ | 排障两个真实 bug（port include 撞车；SYSCALL trap hook 缺失致 yield 变空操作、Tmr Svc 独占）；验收三条全过；提交 `f588fb5` | **port 深潜（SX 核心）提前至 S0 后**：刚调通 syscall 链路，学习动机与上下文最新鲜；S1 概念随讲随补 |
| 2026-08-30 | 工具链决策：单轨 ADS | 用户拍板放弃 HighTec + UDE；SX 移植里程碑转型为 SP Port 深潜系列（第 1 课：上下文切换 / CSA 机制已讲） | 「关键机制 §3」双轨段改写；SX/S8 行同步更新；两条 HighTec 相关假设关闭 |

## 待补充问题

1. ~~九页长图原图归档~~ → 已完成（2026-08-30），见「背景 - 素材来源」。
2. S9 的 AUTOSAR OS 对照深度：届时按工作涉及模块（Os/EcuM/BswM）裁剪。
3. SafeRTOS / 功能安全视角是否扩展为独立阶段（触发条件：工作出现对应需求）。
4. HighTec GCC + UDE 环境如需回归（触发条件：公司项目强制要求），恢复路径：SP 深潜内容照旧有效，另加 GCC port 集成实验（`git restore --source=834d8f6 -- OS/FreeRTOS/portable/GCC/`）。

## 关联笔记

- [[Core_Comparison_CPU_Pipeline_M7_TC3xx_Engineering]]（M7 vs TC3xx 流水线工程对比，跨架构对照方法同源）
- `01_Hardware_硬件层/01_Core/01_AURIX_TC3xx/`（TriCore 内核手册，CSA/中断/异常章节为 S2/S5/SX 硬件依据）
- `01_Hardware_硬件层/00_SoC_Design_Book_精读/`（目的驱动精读方法论的参考实现）
- 各阶段输出笔记（随进度补充链接）

## 标签

#FreeRTOS #AURIX #TC397 #TriCore #HighTec #UDE #ADS #学习路线 #目的驱动精读 #车规MCU

## Agent 整理记录

- 2026-08-30 创建。依据技能 `purpose-driven-book-study`（七步工作流步骤 2–3），经用户四问确认（板子/工具链/基础/目标）与方案 A 拍板后落盘。
- 查证来源：GitHub FreeRTOS/FreeRTOS-Kernel-Partner-Supported-Ports、FreeRTOS/FreeRTOS-Partner-Supported-Demos、Infineon/AURIX_code_examples、FreeRTOS 论坛（#18574、#23315）、freertos.org TC1782 Demo 存档、21ic 移植教程。
- 命名说明：路线文档位于 FreeRTOS 层根目录，采用 `FreeRTOS_00_` 前缀（层内总览性质，子模块阶段笔记按 `FreeRTOS_Kernel_/Sync_/Mem_/Timing_/Port_` 前缀落入对应子目录）。
