# FreeRTOS × TC397 学习支点跟踪清单

## 核心问题

如何判断"某个 RTOS 知识点真的学会了"，而不是"看过/听过"？本项目需要一份可勾选、可验收、与笔记和板级实验一一对应的知识支点清单。

## 结论

- 学习按 **知识点级** 跟踪（不是阶段级），每个支点有唯一 ID、明确的状态、对应的笔记与实验。
- 一个支点只有满足四项判据才能标记 ✅：能脱稿讲清因果链、有代码或板级证据、笔记已落盘、能回答边界与反例。
- 状态只允许四种：⬜ 未开始 / 🔄 进行中 / ✅ 已掌握 / ⏸ 暂缓。
- 本清单与 `FreeRTOS_02_实践TODO.md` 通过 ID 互相引用：知识支点 → 对应实验；实验 → 验证的知识支点。

## 背景

- 总纲见 [[FreeRTOS_00_总体学习与实践方案]]。
- 路线共 S0–S9 十个阶段 + SP Port 深潜四个子系列。
- 2026-10-19 首次建立本清单；已完成部分按历史记录回填（S0、SP1）。
- 支点笔记按需创建（LRN-20260831-001：讲授与落盘同阶段完成），不在本清单中预建空文件。

## 关键机制

### 状态图例

| 符号 | 含义 | 判定标准 |
|---|---|---|
| ⬜ | 未开始 | 尚未系统学习 |
| 🔄 | 进行中 | 已讲解但未通过复述验收，或证据不全 |
| ✅ | 已掌握 | 四项判据全过（见下） |
| ⏸ | 暂缓 | 明确决定不学或推迟，需写触发条件 |

### 完成判据（四项全过）

1. 能脱稿讲清机制因果链（为什么需要、怎么工作、代价是什么）；
2. 有代码证据（具体行号/寄存器/指令）或板级测量证据（数值/波形/调试器观察）；
3. 笔记已落盘到对应目录，命名符合规范；
4. 能回答边界问题：什么条件下不成立、有什么反例、与 ARM 说法哪里不同。

### 进度总览

| 阶段 | 支点数 | ✅ | 🔄 | ⬜ |
|---|---:|---:|---:|---:|
| S0 环境奠基 | 6 | 6 | 0 | 0 |
| SP1 上下文切换 | 6 | 5 | 1 | 0 |
| SP2 临界区与首任务 | 5 | 0 | 0 | 5 |
| SP3 tick 与中断路径 | 5 | 0 | 0 | 5 |
| SP4 栈与 CSA 回收 | 4 | 0 | 0 | 4 |
| S1 任务 | 8 | 0 | 0 | 8 |
| S2 调度 | 7 | 0 | 0 | 7 |
| S3 同步通信 | 8 | 0 | 0 | 8 |
| S4 内存 | 7 | 0 | 0 | 7 |
| S5 中断 | 7 | 0 | 0 | 7 |
| S6 时间管理 | 6 | 0 | 0 | 6 |
| S7 综合实战 | 5 | 0 | 0 | 5 |
| S8 调试排查 | 5 | 0 | 0 | 5 |
| S9 进阶与车规映射 | 6 | 0 | 0 | 6 |
| **合计** | **85** | **11** | **1** | **73** |

### S0 环境奠基

| ID | 知识支点 | 状态 | 证据 / 笔记 |
|---|---|---|---|
| K-S0-01 | FreeRTOS 工程六层结构（应用/内核/port/驱动/启动链接/配置） | ✅ | S0 验收 + 总纲「工程与环境」 |
| K-S0-02 | ADS 构建物化链：`.cproject` → `.opt` / `subdir.mk` | ✅ | LRN-20260830-001 |
| K-S0-03 | Port 选择机制：include 路径与编译列表决定用哪个 port | ✅ | S0 排障记录（GCC/Tasking 撞车） |
| K-S0-04 | FreeRTOSConfig.h 核心配置项语义（tick/优先级/堆/栈检查） | ✅ | 总纲 + S0 实操 |
| K-S0-05 | 启动链：复位 → SSW → core0_main → 调度器启动 | ✅ | 工程 `Cpu0_Main.c` + 启动代码 |
| K-S0-06 | 最小双任务系统的板级验证方法 | ✅ | 双 LED 闪烁 + pxCurrentTCB 轮换 |

### SP1 上下文切换（Port 深潜第 1 课）

| ID | 知识支点 | 状态 | 证据 / 笔记 |
|---|---|---|---|
| K-SP1-01 | TriCore Upper/Lower Context 划分与硬件存取责任 | ✅ | [[FreeRTOS_Port_TC3xx_Context_Switch_CSA]] |
| K-SP1-02 | CSA、FCX、PCXI、LCX 三寄存器与链式管理 | ✅ | 同上 + [[FreeRTOS_Port_TC3xx_PortLayer_Full_Walkthrough]] |
| K-SP1-03 | `pxPortInitialiseStack` 伪造初始现场（A4 参数 / A11 入口 / A10 栈顶 / PSW） | ✅ | Walkthrough 3.1 节（port.c 103–162 行） |
| K-SP1-04 | `vPortSaveContext` / `vPortLoadContext` 与 `ucCallDepth` 语义 | ✅ | Walkthrough 3.7 节 |
| K-SP1-05 | CSA id → 物理地址换算（`pxPortCsaToAddress` 位运算） | 🔄 | 已讲解，尚未在调试器实操验证 |
| K-SP1-06 | Cortex-M7 vs TriCore 异常模型与调用栈对比 | ✅ | [[Core_Comparison_Exception_CallStack_M7_vs_TC3xx]] |

### SP2 临界区与首任务启动（Port 深潜第 2 课，下一站）

| ID | 知识支点 | 状态 | 计划笔记 |
|---|---|---|---|
| K-SP2-01 | `vPortStartFirstTask`：首个任务如何"无中生有"，PSW.CSC 为何清零 | ⬜ | `05_Port/01_PortLayer/` |
| K-SP2-02 | `vPortEnterCritical` / `vPortExitCritical` + `uxCriticalNesting` 嵌套语义 | ⬜ | 同上 |
| K-SP2-03 | `portASSERT_IF_IN_ISR` 与 ICR.CCPN 判定原理 | ⬜ | 同上 |
| K-SP2-04 | 两条切换路径对比：syscall trap（任务级）vs context SRN（ISR 级） | ⬜ | 同上 |
| K-SP2-05 | `portYIELD_FROM_ISR` 的挂起判断与 SETR 软件触发 | ⬜ | `05_Port/02_Interrupts/` |

### SP3 tick 与中断路径

| ID | 知识支点 | 状态 | 计划笔记 |
|---|---|---|---|
| K-SP3-01 | STM0 比较模式配置（CMCON / ICR / ISCR / CMP0） | ⬜ | `05_Port/02_Interrupts/` |
| K-SP3-02 | tick ISR 流程与"累加 CMP0 不漂移"的原理 | ⬜ | 同上 |
| K-SP3-03 | SRN 结构：SRPN / TOS / SRE / SRR / SETR | ⬜ | 同上 |
| K-SP3-04 | 中断优先级方向（数值大=高）与 CCPN 动态阈值 | ⬜ | 同上 |
| K-SP3-05 | 中断嵌套与 ISR 安全边界 | ⬜ | 同上 |

### SP4 栈与 CSA 回收

| ID | 知识支点 | 状态 | 计划笔记 |
|---|---|---|---|
| K-SP4-01 | TriCore 任务栈布局与最小栈深估算 | ⬜ | `03_Memory/` |
| K-SP4-02 | `vPortReclaimCSA` 链表回收机制 | ⬜ | `05_Port/01_PortLayer/` |
| K-SP4-03 | CSA 耗尽（FCD trap）与容量预算 | ⬜ | `03_Memory/` |
| K-SP4-04 | Port 四件套完整性检查表 | ⬜ | `05_Port/01_PortLayer/` |

### S1 任务

| ID | 知识支点 | 状态 | 计划笔记 |
|---|---|---|---|
| K-S1-01 | TCB 全字段与内存布局（含 TriCore 特有字段） | ⬜ | `01_Kernel/01_Tasks/` |
| K-S1-02 | 任务四态状态机（Running/Ready/Blocked/Suspended）与转换条件 | ⬜ | 同上 |
| K-S1-03 | `xTaskCreate` 全流程：栈与 TCB 分配、就绪链表挂入 | ⬜ | 同上 |
| K-S1-04 | `xTaskCreateStatic` 与静态分配对比 | ⬜ | 同上 |
| K-S1-05 | 任务删除与 IDLE 任务延迟回收 | ⬜ | 同上 |
| K-S1-06 | 挂起/恢复（`vTaskSuspend` / `vTaskResume`） | ⬜ | 同上 |
| K-S1-07 | 空闲任务与空闲钩子（`vApplicationIdleHook`） | ⬜ | 同上 |
| K-S1-08 | 任务优先级、句柄与调试器观察方法 | ⬜ | 同上 |

### S2 调度

| ID | 知识支点 | 状态 | 计划笔记 |
|---|---|---|---|
| K-S2-01 | 就绪链表 `pxReadyTasksLists` 与任务挂链方式 | ⬜ | `01_Kernel/02_Scheduler/` |
| K-S2-02 | 最高优先级任务选择算法与位图加速 | ⬜ | 同上 |
| K-S2-03 | 抢占式调度的触发点（tick / yield / 中断返回） | ⬜ | 同上 |
| K-S2-04 | 时间片轮转与 `configUSE_TIME_SLICING` | ⬜ | 同上 |
| K-S2-05 | `xTaskIncrementTick` 与延时链表唤醒 | ⬜ | 同上 |
| K-S2-06 | `vTaskSuspendAll` / `xTaskResumeAll` 挂起调度器 | ⬜ | 同上 |
| K-S2-07 | 优先级反转现象与代价（预告 S3） | ⬜ | 同上 |

### S3 同步通信

| ID | 知识支点 | 状态 | 计划笔记 |
|---|---|---|---|
| K-S3-01 | 队列结构与数据拷贝语义 | ⬜ | `01_Kernel/04_Queues/` |
| K-S3-02 | 阻塞与超时机制（tick 等待链表） | ⬜ | 同上 |
| K-S3-03 | 二值信号量：事件通知模式 | ⬜ | `02_Synchronization/01_Semaphores/` |
| K-S3-04 | 计数信号量：资源计数模式 | ⬜ | 同上 |
| K-S3-05 | 互斥量与优先级继承 | ⬜ | `02_Synchronization/02_Mutexes/` |
| K-S3-06 | 事件组与多位标志同步 | ⬜ | `02_Synchronization/03_EventGroups/` |
| K-S3-07 | 任务通知：轻量级同步替代方案 | ⬜ | `02_Synchronization/` |
| K-S3-08 | 流缓冲与消息缓冲 | ⬜ | `02_Synchronization/04_StreamBuffers/` |

### S4 内存

| ID | 知识支点 | 状态 | 计划笔记 |
|---|---|---|---|
| K-S4-01 | heap_1~5 实现策略与适用场景对比 | ⬜ | `03_Memory/01_Heap/` |
| K-S4-02 | heap_4 空闲块合并与碎片产生/消除 | ⬜ | 同上 |
| K-S4-03 | 栈深度估算与 `uxTaskGetStackHighWaterMark` | ⬜ | `03_Memory/02_Stack/` |
| K-S4-04 | 栈溢出检测两级机制与 hook | ⬜ | 同上 |
| K-S4-05 | 静态分配优先原则与工程取舍 | ⬜ | `03_Memory/` |
| K-S4-06 | 堆监控 API 与运行时预算 | ⬜ | `03_Memory/01_Heap/` |
| K-S4-07 | RAM 与 CSA 双资源预算方法 | ⬜ | `03_Memory/` |

### S5 中断

| ID | 知识支点 | 状态 | 计划笔记 |
|---|---|---|---|
| K-S5-01 | 为什么 ISR 内必须用 FromISR 版本 API | ⬜ | `05_Port/02_Interrupts/` |
| K-S5-02 | ISR 中可调用 API 全表与限制 | ⬜ | 同上 |
| K-S5-03 | 中断优先级配置边界（可调用 API 的最高优先级） | ⬜ | 同上 |
| K-S5-04 | `portYIELD_FROM_ISR` 语义与中断返回切换 | ⬜ | 同上 |
| K-S5-05 | 中断嵌套与临界区关系 | ⬜ | 同上 |
| K-S5-06 | 延迟处理模式（deferred interrupt processing） | ⬜ | 同上 |
| K-S5-07 | 常见错误：ISR 内阻塞、优先级越界、未清中断源 | ⬜ | 同上 |

### S6 时间管理

| ID | 知识支点 | 状态 | 计划笔记 |
|---|---|---|---|
| K-S6-01 | tick 语义、精度与系统时基的关系 | ⬜ | `04_Timing/01_Tick/` |
| K-S6-02 | `vTaskDelay` vs `vTaskDelayUntil` 与周期漂移 | ⬜ | `04_Timing/03_Delays/` |
| K-S6-03 | 软件定时器与 Tmr Svc 任务 | ⬜ | `04_Timing/02_SoftwareTimers/` |
| K-S6-04 | 定时器命令队列与回调执行上下文 | ⬜ | 同上 |
| K-S6-05 | 定时器精度边界与回调约束 | ⬜ | 同上 |
| K-S6-06 | Tickless idle 原理与低功耗取舍 | ⬜ | `04_Timing/01_Tick/` |

### S7 综合实战

| ID | 知识支点 | 状态 | 计划笔记 |
|---|---|---|---|
| K-S7-01 | 从需求到任务划分（职责单一、粒度、通信关系） | ⬜ | 实战总结 |
| K-S7-02 | 优先级分配原则与速率单调思想 | ⬜ | 同上 |
| K-S7-03 | 任务间通信与同步方案选型 | ⬜ | 同上 |
| K-S7-04 | 资源预算（栈/堆/CPU）与配置裁剪 | ⬜ | 同上 |
| K-S7-05 | 集成调试与验收测试设计 | ⬜ | 同上 |

### S8 调试排查

| ID | 知识支点 | 状态 | 计划笔记 |
|---|---|---|---|
| K-S8-01 | 故障树：崩溃/卡死/数据错乱/时序异常的排查路径 | ⬜ | `05_Port/` 或 `05_Tools_工具链/` |
| K-S8-02 | 运行时间统计（`configGENERATE_RUN_TIME_STATS` + STM） | ⬜ | 同上 |
| K-S8-03 | 栈水位、堆余量、任务状态快照的采集方法 | ⬜ | 同上 |
| K-S8-04 | 断言、日志与断点的组合使用 | ⬜ | 同上 |
| K-S8-05 | 常见故障案例库与复现手法 | ⬜ | 同上 |

### S9 进阶与车规映射

| ID | 知识支点 | 状态 | 计划笔记 |
|---|---|---|---|
| K-S9-01 | Tickless idle 实现细节与功耗收益 | ⬜ | `04_Timing/01_Tick/` |
| K-S9-02 | 多核 AMP：每核独立内核实例的资源划分 | ⬜ | `01_Hardware_硬件层/06_Multicore/` |
| K-S9-03 | FreeRTOS 与 AUTOSAR OS 概念对照（Task/Event/Alarm/Resource） | ⬜ | `02_Middleware/01_AUTOSAR/07_System/01_OS/` |
| K-S9-04 | 时间保护与空间保护（SafeT / MPU）在两种 OS 中的实现 | ⬜ | `04_Safety_功能安全/` |
| K-S9-05 | SafeRTOS / 安全认证路径与适用边界 | ⬜ | `04_Safety_功能安全/` |
| K-S9-06 | 车规项目的 RTOS 选型判断框架 | ⬜ | 总纲「应用场景」 |

## 应用场景

- **每次学习前**：查本清单确定当前支点与前置依赖。
- **每次学习后**：按四项判据更新状态；未过判据不得标 ✅。
- **月度回顾**：统计 🔄 滞留项，判断是讲解不清、证据不足还是笔记缺失。

## 关联笔记

- [[FreeRTOS_00_总体学习与实践方案]]（总纲）
- [[FreeRTOS_02_实践TODO]]（板级实验清单）
- [[FreeRTOS_Port_TC3xx_PortLayer_Full_Walkthrough]]（SP 主参考）
- [[FreeRTOS_Port_TC3xx_Context_Switch_CSA]]（SP1）

## 待补充问题

1. 支点数量会随学习深入调整（拆分过粗的、合并过细的），调整需在「Agent 整理记录」留痕。
2. S7/S8/S9 的支点需在进入该阶段前细化，当前为初稿。
3. 若后续引入 AUTOSAR OS 学习线，K-S9-03 起可独立成册。

## 标签

#FreeRTOS #TC397 #学习清单 #支点跟踪 #进度管理

## Agent 整理记录

- 2026-10-19 创建。按用户要求以知识点级粒度建立；已完成的 S0（6 项）与 SP1（6 项）按历史记录回填，其余为 ⬜。
- 状态判定严格遵循四项判据；K-SP1-05 因"已讲解但未实操验证"标为 🔄。
