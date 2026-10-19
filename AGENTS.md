# MarkDown_Learn 项目工作指南

> 本文件为 AI 代理（Claude Code / Kimi Code 等）提供项目级工作规范。处理本仓库任何任务前，请先阅读本文件。
>
> **双入口同步**：`AGENTS.md`（Kimi Code 入口）与 `.claude/CLAUDE.md`（Claude Code 入口）内容完全一致。修改任意一份即可，git pre-commit hook 会自动以较新者同步另一份；不走 git 的修改请手动运行 `scripts/sync-guides.ps1`。

---

## 1. 项目概述

本项目是个人知识库，聚焦**车规 MCU 全技术栈**的知识沉淀，覆盖从芯片硬件、外设、中间件到应用层的完整层次：

| 层次 | 内容 |
|------|------|
| **硬件层 (Hardware)** | 车规 MCU（AURIX TC3xx、NXP S32E2）、ARM 内核（Cortex-M7/R52）、外设（SPI/I2C/CAN/LIN/UART/Ethernet/FlexRay/Timer/ADC/GPIO）、系统（SCU/总线/时钟/电源/DMA/中断）、存储（RAM/Flash/Cache/MPU）、多核、调试（CoreSight/Trace/JTAG）、制造封装 |
| **中间件层 (Middleware)** | AUTOSAR MCAL/BSW（CAN/LIN/SPI/Ethernet Stack、UDS、DEM/DET、OS/EcuM、E2E、SafeSPI）、FreeRTOS（任务/调度/同步/内存/定时器/移植） |
| **功能安全 (Safety)** | ISO 26262、E2E、Safety Monitor、Lockstep、看门狗安全 |
| **工具链 (Tools)** | 编译器（GCC/Tasking/HighTec）、调试器（Lauterbach/PLS）、烧录、Trace、HIL/SIL 测试 |
| **应用层 (Application)** | 预留业务逻辑、算法、系统集成 |

**核心目标**：以结构化、可维护的 Markdown 形式沉淀技术资料，支持长期查阅与知识迭代。

**覆盖领域：**
- **MCU 内核**：AURIX TC3xx（TriCore）、NXP S32E2（Cortex-R52）、ARM Cortex-M7
- **外设**：
  - 通讯：SPI/I2C/CAN/CAN-FD/LIN/UART/Ethernet/FlexRay、SafeSPI、Intercore
  - 定时器：GPT、PWM、ICU、WDG
  - IO：GPIO/DIO、ADC、DAC
  - 存储：Internal Flash、EEPROM Emulation
- **系统**：SCU、Clock、Power、Reset、Bus（SPB/SRI）、DMA、Interrupt
- **内存**：RAM、Flash、Cache、MPU
- **多核**：Lockstep、Resource Sharing、Intercore Communication
- **调试**：CoreSight、Trace（ETM/MTB）、JTAG/DAP、Cross Trigger
- **制造/封装**：IC 封装工艺、CP/FT 测试、WAT、可靠性
- **AUTOSAR**：
  - 通讯：CAN Stack（CanIf/CanTp/CanSm）、LIN、SPI、Ethernet、UDS、XCP/CCP
  - 存储：Flash Driver、EEPROM、NVRAM、Fee、Ea、NvM
  - IO：DIO、ADC、PWM、ICU
  - 诊断：DEM、DET、UDS Services、DTC、OBD
  - 系统：OS、EcuM、BswM、SchM、ComM、Nm
  - 安全：E2E、SafeSPI、SafeT、Safety WDG
- **FreeRTOS**：Tasks、Scheduler、Semaphores/Mutexes/EventGroups、Heap/Stack/MPU、Tick/Timers、Port/Interrupts/Hooks
- **功能安全**：ISO 26262、E2E、Safety Monitor、Lockstep
- **工具链**：GCC/Tasking/HighTec、Lauterbach/PLS、Trace32、HIL/SIL

---

## 2. 核心工作原则与协作规范

### 2.1 第一性原理

分析任何问题、设计方案、修改代码或生成文档时，**优先从问题最基础、最不可再拆解的事实、约束、目标和因果关系出发，逐层推导结论**，不直接套用经验结论、现成模板或表面相似案例。

#### 工作方式

1. **明确问题本质目标**
   - 用户真正想解决什么问题？交付物是什么？成功标准是什么？
   - 区分必须满足的内容 vs 可选优化

2. **拆解基础事实和硬约束**
   - 已知输入、技术边界、平台/工具链/接口/文件结构/规范要求
   - 哪些条件不可变？哪些假设需显式说明？

3. **区分事实、推断和假设**
   - 确定事实 → 直接使用
   - 合理推断 → 标明依据
   - 不确定信息 → 不臆造；说明缺失，在可继续范围内给出最稳妥方案

4. **从底层机制推导方案**
   - 不只说"通常这样做"，要解释**为什么**这样做
   - 说明方案如何满足目标、约束和边界条件
   - 多方案时比较适用条件、优缺点和风险

5. **避免机械套模板**
   - 不为完整而堆砌无关内容
   - 不照搬通用答案；每一部分必须服务于当前问题

6. **输出必须可执行**
   - 代码任务 → 可直接落地的文件、函数、接口、配置或修改点
   - 工程设计 → 清晰的模块划分、接口边界、状态机、错误处理和测试点
   - 文档任务 → 结构清楚，术语统一，内容能直接进入正式文档
   - 问题排查 → 验证步骤、判断依据和下一步动作

#### 回答原则

- 先判断问题本质，再给结论
- 先列约束，再设计方案
- 先保证正确性，再考虑简洁性
- 先满足核心功能，再扩展优化
- **不编造**不存在的接口、寄存器、文件、参数、API 或工具能力
- 不确定时明确指出，不用模糊措辞掩盖
- 复杂任务按 **"目标 → 约束 → 推导 → 方案 → 风险 → 验证"** 顺序输出

### 2.2 行动规范（人机协作边界）

1. **执行前可提出异议**
   - 用户下达指令时，若我发现明显风险、逻辑矛盾或存在更优方案，**应先说明问题和替代建议，再执行或等待确认**
   - 不盲目服从已知会导致数据丢失、安全漏洞、环境破坏的命令
   - 简单明确且无风险的指令直接执行，不提无关异议

2. **判断型任务：先分析，后等决策**
   - 用户要求"判断/决定/评估"时，**先独立完成完整分析**，给出：
     - 分析依据（事实 + 推断）
     - 各选项的利弊与风险
     - 推荐方案及理由
   - **最终决策权归用户**，我给出"建议做"而非"决定做"
   - 用户明确说"你决定"时，才直接执行

3. **方案变更时单独说明**
   - 执行过程中发现原方案不可行或有更优路径时，**暂停并清晰说明**：
     - 原方案的问题
     - 新方案的优势
     - 需要用户确认还是我可以直接调整
   - 不在用户不知情的情况下擅自更改既定方案

### 2.3 协作规范（六条思维纪律）

1. **先想后做**：非平凡任务先交 5 步以内计划，标出最没把握的 1-2 步
2. **分层推进**：对齐问题空间 → 枚举方案 → 只细化选定方案，不一次性甩成品
3. **分层表达**：输出按"一句话权衡 → 任务拆解 → 细节按需展开"组织
4. **讲得清楚才算做完**：复杂方案能向"新同事"讲清；配合用户复述直到顺为止
5. **思考外化**：复杂推理出表格/思维树，长文落盘，checkpoint 写文件
6. **不确定性分级**：收尾列"防跑偏三件事"，输出按 ✅确定/🟡模糊/❓未验证 分级

结果出错时按**三分法**定位根因（目标误解 / 约束漏了 / 思路偏了），再对症处理。

---

## 3. 文档规范

### 3.1 写作风格

- **主要语言**：中文。技术术语保留英文（如 `Cortex-M7`、`SCU`、`SPI`、`MPU`）。
- **标题层级**：`#` 用于文档标题，`##` 用于章节，`###` 用于小节。
- **代码块**：必须标注语言类型（如 ```` ```c ````、```` ```bash ````、```` ```python ````）。
- **图表**：使用 Mermaid 语法绘制架构图和流程图，确保语法正确。
- **文件命名**：使用下划线 `_` 作为分隔符，禁止空格。

### 3.2 文件组织

- 新增主题优先放入对应层次目录；如无合适目录，按技术栈层次新建。
- 文件命名规范：见下方「文件命名规则」。

```
MarkDown_Learn/
├── AGENTS.md              ← 项目工作指南（Kimi Code 入口，与 .claude/CLAUDE.md 内容一致、双向同步）
├── .kimi-code/            ← Kimi Code 项目配置
│   ├── README.md
│   ├── agents/            ← 自定义子代理（note-organizer、kb-reviewer）
│   └── skills/            ← 项目技能（18 个，.claude/skills/ 的镜像副本）
├── .claude/               ← Claude Code 配置与共享资料（双工具并存）
│   ├── CLAUDE.md          ← 项目工作指南（Claude Code 入口，与 AGENTS.md 内容一致、双向同步）
│   ├── settings.json      ← Claude Code 钩子配置（PostToolUse doc-review 等）
│   ├── hooks/             ← Claude Code 钩子脚本
│   ├── memory/            ← 记忆索引与文件分类速查表
│   ├── references/        ← 参考资料（knowledge-base，两套工具共享引用）
│   └── skills/            ← Claude Code 技能（源副本）
├── scripts/               ← 仓库维护脚本（sync-guides.ps1 等）
├── .learnings/            ← 持续改进日志
│   ├── ERRORS.md
│   ├── FEATURE_REQUESTS.md
│   └── LEARNINGS.md
├── 00_Inbox_临时收集/     ← 临时笔记（Obsidian 规则）
├── 01_Hardware_硬件层/    ← 芯片硬件层
│   ├── 01_Core/           ← 内核架构
│   │   ├── 01_AURIX_TC3xx/    ← TriCore、AURIX 专用
│   │   ├── 02_ARM_Cortex/     ← Cortex-M7、Cortex-R52
│   │   └── 03_Comparison/     ← 架构对比分析
│   ├── 02_Memory/         ← 存储子系统
│   │   ├── 01_RAM/            ← RAM、复位初始化
│   │   ├── 02_Flash/          ← Internal/External Flash
│   │   ├── 03_Cache/          ← Cache 一致性、预取
│   │   └── 04_MPU/            ← 内存保护单元
│   ├── 03_System/         ← 系统级模块
│   │   ├── 01_Clock/          ← 时钟树、PLL、OSC
│   │   ├── 02_Power/          ← 低功耗、电源管理
│   │   ├── 03_Reset/          ← 复位源、复位序列
│   │   ├── 04_Bus/            ← SPB、SRI、DMA
│   │   ├── 05_DMAMove/        ← DMA 控制器、通道配置
│   │   └── 06_Interrupt/      ← 中断路由、优先级、嵌套
│   ├── 04_Boot/           ← 启动流程
│   │   ├── 01_Bootloader/     ← 二级引导程序
│   │   ├── 02_BootROM/        ← 原厂 BootROM 流程
│   │   └── 03_Firmware_Update/← OTA、刷写协议
│   ├── 05_Peripherals/    ← 外设（按功能分类）
│   │   ├── 01_Communication/  ← 通讯外设
│   │   │   ├── 01_SPI/            ← SPI、QSPI、SafeSPI
│   │   │   ├── 02_I2C_IIC/        ← I2C、SMBus
│   │   │   ├── 03_CAN_CANFD/      ← CAN、CAN-FD
│   │   │   ├── 04_LIN/            ← LIN 总线
│   │   │   ├── 05_UART_USART/     ← UART、USART、SCI
│   │   │   ├── 06_Ethernet/       ← MAC、Switch、TSN
│   │   │   ├── 07_FlexRay/        ← FlexRay 总线
│   │   │   ├── 08_Intercore/      ← 核间通信（Spinlock、Mailbox）
│   │   │   └── 99_Protocol_协议分析/ ← 协议解码、时序分析
│   │   ├── 02_Timer/      ← 定时器外设
│   │   │   ├── 01_GPT/            ← 通用定时器
│   │   │   ├── 02_PWM/            ← 脉宽调制
│   │   │   ├── 03_ICU/            ← 输入捕获
│   │   │   └── 04_WDG_Watchdog/   ← 看门狗（独立/窗口）
│   │   ├── 03_IO/         ← IO 外设
│   │   │   ├── 01_GPIO_DIO/       ← 数字 IO、Port 控制
│   │   │   ├── 02_ADC/            ← 模数转换（SAR/Σ-Δ）
│   │   │   └── 03_DAC/            ← 数模转换
│   │   └── 04_Storage/    ← 存储外设
│   │       ├── 01_Internal_Flash/ ← 内部 Flash 控制器
│   │       ├── 02_EEPROM_Emulation/ ← EEPROM 仿真
│   │       └── 03_Fee_Flash_Emul/ ← Flash EEPROM Emulation
│   ├── 06_Multicore/      ← 多核系统
│   │   ├── 01_Lockstep/       ← 锁步核、冗余校验
│   │   ├── 02_Resource_Sharing/ ← 共享资源保护
│   │   └── 03_Intercore_Comm/   ← 核间通信机制
│   ├── 07_Debug/          ← 调试子系统
│   │   ├── 01_CoreSight/      ← CoreSight 架构、DAP
│   │   ├── 02_Trace/          ← ETM、MTB、Trace 解码
│   │   ├── 03_JTAG_DAP/       ← JTAG、SWD、DAP 协议
│   │   └── 04_CrossTrigger/   ← 交叉触发、断点同步
│   └── 08_Packaging/      ← 制造与封装
│       └── pictures/          ← 封装工艺图片
├── 02_Middleware_中间件层/ ← AUTOSAR + FreeRTOS
│   ├── 01_AUTOSAR/        ← AUTOSAR MCAL / BSW
│   │   ├── 01_Communication/  ← 通讯栈
│   │   │   ├── 01_CAN_CANFD/      ← Can/CanIf/CanTp/CanSm
│   │   │   ├── 02_LIN/            ← Lin/LinIf/LinTp
│   │   │   ├── 03_SPI/            ← Spi/SpiIf
│   │   │   ├── 04_Ethernet/       ← Eth/EthIf/EthSwt
│   │   │   ├── 05_FlexRay/        ← Fr/FrIf/FrTp
│   │   │   ├── 06_UDS_诊断通信/    ← UDS、ISO-TP、DoCAN
│   │   │   └── 07_XCP_CCP/        ← 标定协议
│   │   ├── 02_Memory/     ← 内存驱动
│   │   │   ├── 01_Flash_Driver/   ← Flash 驱动
│   │   │   ├── 02_EEPROM/         ← EEPROM 抽象
│   │   │   └── 03_NVRAM/          ← NVRAM 管理
│   │   ├── 03_IO/         ← IO 驱动
│   │   │   ├── 01_DIO/            ← 数字 IO
│   │   │   ├── 02_ADC/            ← ADC 驱动
│   │   │   ├── 03_PWM/            ← PWM 驱动
│   │   │   └── 04_ICU/            ← ICU 驱动
│   │   ├── 04_Timer/      ← 定时器驱动
│   │   │   ├── 01_GPT/            ← 通用定时器
│   │   │   └── 02_WDG/            ← WDG 驱动
│   │   ├── 05_Storage/    ← 存储服务
│   │   │   ├── 01_Fee/            ← Flash EEPROM Emulation
│   │   │   ├── 02_Ea/             ← EEPROM Abstraction
│   │   │   └── 03_NvM/            ← NVRAM Manager
│   │   ├── 06_Diagnostics/← 诊断栈
│   │   │   ├── 01_DEM/            ← 诊断事件管理
│   │   │   ├── 02_DET/            ← 开发错误追踪
│   │   │   ├── 03_UDS_Services/   ← UDS 服务实现
│   │   │   ├── 04_DTC/            ← DTC 管理
│   │   │   └── 05_OBD/            ← OBD 诊断
│   │   ├── 07_System/     ← 系统服务
│   │   │   ├── 01_OS/             ← OS（OSEK/AUTOSAR OS）
│   │   │   ├── 02_EcuM/           ← ECU 状态管理
│   │   │   ├── 03_BswM/           ← BSW 模式管理
│   │   │   ├── 04_SchM/           ← BSW 调度器
│   │   │   ├── 05_ComM/           ← 通讯管理
│   │   │   └── 06_Nm/             ← 网络管理
│   │   ├── 08_Safety/     ← 功能安全
│   │   │   ├── 01_E2E/            ← E2E 保护（E2E Profile）
│   │   │   ├── 02_WDG_Safety/     ← Safety Watchdog
│   │   │   ├── 03_SafeSPI/        ← SafeSPI 协议栈
│   │   │   ├── 04_SafeT/          ← SafeT（时间保护）
│   │   │   └── 05_Testing/        ← 安全测试、BIST
│   │   └── 09_MCU/        ← MCU 驱动
│   │       ├── 01_MCU_Driver/     ← MCU 通用驱动
│   │       ├── 02_Port_Driver/    ← Port 引脚配置
│   │       └── 03_GPT_Driver/     ← GPT 驱动
│   └── 02_FreeRTOS/       ← FreeRTOS 实时内核
│       ├── 01_Kernel/     ← 内核核心
│       │   ├── 01_Tasks/          ← 任务创建、状态、删除
│       │   ├── 02_Scheduler/      ← 调度器、上下文切换
│       │   ├── 03_Lists/          ← 任务列表、就绪队列
│       │   └── 04_Queues/         ← 队列、消息缓冲
│       ├── 02_Synchronization/ ← 同步机制
│       │   ├── 01_Semaphores/     ← 二值/计数信号量
│       │   ├── 02_Mutexes/        ← 互斥量、优先级继承
│       │   ├── 03_EventGroups/    ← 事件组
│       │   └── 04_StreamBuffers/  ← 流缓冲、消息缓冲
│       ├── 03_Memory/     ← 内存管理
│       │   ├── 01_Heap/           ← Heap 分配策略
│       │   ├── 02_Stack/          ← 栈溢出检测
│       │   └── 03_MPU/            ← MPU 保护
│       ├── 04_Timing/     ← 时序管理
│       │   ├── 01_Tick/           ← Tick 中断、时基
│       │   ├── 02_SoftwareTimers/ ← 软件定时器
│       │   └── 03_Delays/         ← 任务延时、阻塞
│       └── 05_Port/       ← 移植层
│           ├── 01_PortLayer/      ← Port 层实现
│           ├── 02_Interrupts/     ← 中断嵌套、临界区
│           └── 03_Hooks/          ← Hook 函数
├── 03_Application_应用层/  ← 预留：业务逻辑、算法、系统集成
├── 04_Safety_功能安全/     ← ISO 26262、功能安全
│   ├── 01_ISO26262/       ← ASIL、安全生命周期、FMEDA
│   ├── 02_E2E/            ← E2E 保护（跨层视角）
│   ├── 03_SafetyMonitor/  ← 安全监控器
│   └── 04_Lockstep/       ← 锁步核（跨层视角）
├── 05_Tools_工具链/        ← 开发工具链
│   ├── 01_Compiler_编译器/ ← GCC、Tasking、HighTec、GreenHills
│   ├── 02_Debugger_调试器/ ← Lauterbach、PLS、J-Link
│   ├── 03_Flash_烧录工具/  ← 烧录器、刷写工具
│   ├── 04_Trace_跟踪工具/  ← Trace32、ETM 解码
│   └── 05_HIL_SIL_测试/    ← HIL、SIL、单元测试
├── 90_Archive_归档/       ← 归档草稿与历史版本
└── 99_Attachments_附件/   ← 附件统一存放
```

#### 文件命名规则

文件名必须体现**层次归属**和**主题**，避免不同层次的同名文件混淆：

| 层次 | 命名前缀/格式 | 示例 |
|------|-------------|------|
| Hardware / Core / AURIX | `{MCU}_Core_` | `AURIX_TC3xx_Core_Manual_Detailed_Mermaid.md` |
| Hardware / Core / ARM | `ARM_{Core}_Core_` | `ARM_M7_Core_Manual_Detailed_Mermaid.md` |
| Hardware / Core / Comparison | `Core_Comparison_` | `Core_Comparison_Cortex-R52_vs_M7.md` |
| Hardware / Memory | `HW_Mem_` 或 `{MCU}_Mem_` | `HW_Mem_RAM_Reset_Init_Report.md` |
| Hardware / System | `HW_Sys_` 或 `{MCU}_Sys_` | `HW_Sys_SCU_Software_Reset_Summary.md` |
| Hardware / Boot | `HW_Boot_` | `HW_Boot_Bootloader_Design.md` |
| Hardware / Peripherals / Comm | `HW_Periph_Comm_{协议}_` | `HW_Periph_Comm_SPI_Specification.md` |
| Hardware / Peripherals / Timer | `HW_Periph_Timer_` | `HW_Periph_Timer_GPT_Config.md` |
| Hardware / Peripherals / IO | `HW_Periph_IO_` | `HW_Periph_IO_ADC_Calibration.md` |
| Hardware / Peripherals / Storage | `HW_Periph_Storage_` | `HW_Periph_Storage_Flash_Erase.md` |
| Hardware / Multicore | `HW_MC_` 或 `{MCU}_MC_` | `HW_MC_Lockstep_Mechanism.md` |
| Hardware / Debug | `HW_Debug_` | `HW_Debug_CoreSight_DAP.md` |
| Hardware / Packaging | `HW_Packaging_` | `HW_Packaging_Blind_Package_Auto_MCU.md` |
| AUTOSAR / Communication | `AUTOSAR_Comm_{协议}_` | `AUTOSAR_Comm_CAN_Stack_Overview.md` |
| AUTOSAR / Memory | `AUTOSAR_Mem_` | `AUTOSAR_Mem_Flash_Driver.md` |
| AUTOSAR / IO | `AUTOSAR_IO_` | `AUTOSAR_IO_PWM_Driver.md` |
| AUTOSAR / Timer | `AUTOSAR_Timer_` | `AUTOSAR_Timer_GPT_Driver.md` |
| AUTOSAR / Storage | `AUTOSAR_Storage_` | `AUTOSAR_Storage_NvM_Config.md` |
| AUTOSAR / Diagnostics | `AUTOSAR_Diag_` | `AUTOSAR_Diag_DEM_Event.md` |
| AUTOSAR / System | `AUTOSAR_Sys_` | `AUTOSAR_Sys_EcuM_States.md` |
| AUTOSAR / Safety | `AUTOSAR_Safety_` | `AUTOSAR_Safety_E2E_Profile.md` |
| AUTOSAR / MCU | `AUTOSAR_MCU_` | `AUTOSAR_MCU_Port_Config.md` |
| FreeRTOS / Kernel | `FreeRTOS_Kernel_` | `FreeRTOS_Kernel_Task_Scheduling.md` |
| FreeRTOS / Synchronization | `FreeRTOS_Sync_` | `FreeRTOS_Sync_Mutex_Priority.md` |
| FreeRTOS / Memory | `FreeRTOS_Mem_` | `FreeRTOS_Mem_Heap_Strategies.md` |
| FreeRTOS / Timing | `FreeRTOS_Timing_` | `FreeRTOS_Timing_Software_Timers.md` |
| FreeRTOS / Port | `FreeRTOS_Port_` | `FreeRTOS_Port_Critical_Section.md` |
| Safety | `Safety_` | `Safety_ISO26262_ASIL_D.md` |
| Tools | `Tools_` | `Tools_Compiler_Tasking_Optimization.md` |

**原则**：
1. 同一主题跨层次时，文件名必须能区分（如 `HW_Periph_Comm_SafeSPI_...` vs `AUTOSAR_Safety_SafeSPI_...`）
2. 禁止空格，用下划线 `_` 分隔
3. 英文缩写统一大写（`SPI`、`CAN`、`ADC`、`GPIO`）

---

## 4. 关键内容模式

### 4.1 内核手册

`01_Hardware_硬件层/01_Core/` 目录按架构细分（`01_AURIX_TC3xx/`、`02_ARM_Cortex/`、`03_Comparison/`），包含按 19 章大纲组织的 MCU 内核手册（`Automotive_MCU_Core_Manual_Outline_Section_Writing_Guide.md`）。章节涵盖：编程模型、特权模式、上下文管理、复位/启动、中断、异常、内存模型、缓存、保护机制、FPU/DSP、调试/跟踪、时序、多核、低功耗、移植指南。

编辑或创建内核文档时，遵循此大纲结构，并按 MCU 架构放入对应子目录（AURIX 放 `01_AURIX_TC3xx/`，ARM 放 `02_ARM_Cortex/`）。

### 4.2 SafeSPI 分析

`01_Hardware_硬件层/05_Peripherals/01_Communication/HW_Periph_Comm_SafeSPI_Origin_Background_13K_MCU_Support_Analysis.md` 提供了评估 MCU SPI 控制器是否符合 SafeSPI Rev 2.0 规范的完整框架。采用分层分析方法：

1. 物理/IO 层（电气参数）
2. SPI 传输层（CPOL/CPHA、帧大小、时序）
3. SafeSPI 逻辑层（帧格式、CRC、寻址）
4. 协议行为（帧内/帧外、故障管理）
5. 监听/监控能力

分析新 MCU 的 SafeSPI 支持性时，遵循此结构化评估模式。

---

## 5. 工具与技能

### 5.1 本地技能

技能以多文件目录形式存放，双工具各有一份、内容保持一致：Kimi Code 用 `.kimi-code/skills/`（可用 `/skill:<名称>` 手动调用），Claude Code 用 `.claude/skills/`（部分技能支持 `/<名称>` 斜杠命令）；两者均可由模型按 description 自动触发。新增/修改技能时，改完一边后同步另一边，保持内容一致。

| 技能 | 路径（Kimi Code 侧；Claude Code 对应 `.claude/skills/`） | 触发时机 |
|------|------|----------|
| docx-cn | `.kimi-code/skills/docx-cn/` | Word 文档处理（.docx） |
| find-skills | `.kimi-code/skills/find-skills/` | 搜索/安装外部技能 |
| context-compress | `.kimi-code/skills/context-compress/` | 上下文压缩与摘要（Kimi Code 手动 `/skill:context-compress`，Claude Code 手动 `/context-compress`，或 Hook 自动提醒） |
| mineru-pdf-parser | `.kimi-code/skills/mineru-pdf-parser/` | PDF/Word/PPT/Excel 转 Markdown |
| pdf | `.kimi-code/skills/pdf/` | PDF 处理指南 |
| self-improving-agent | `.kimi-code/skills/self-improving-agent/` | 持续改进日志（强制工作流） |
| summarize | `.kimi-code/skills/summarize/` | 内容提取/摘要 |
| autoresearch | `.kimi-code/skills/autoresearch/` | 有明确量化指标的自动迭代优化（性能、内存、测试通过率、构建时间等） |
| impeccable | `.kimi-code/skills/impeccable/` | 前端 UI 设计、重构、评审、打磨（页面、组件、Dashboard、表单等） |
| obsidian-vault | `.kimi-code/skills/obsidian-vault/` | 在 Obsidian 中搜索、创建、整理笔记 |
| note-organizer | `.kimi-code/skills/note-organizer/` | 按本规范整理 Markdown 笔记目录与命名 |
| skillify | `.kimi-code/skills/skillify/` | 将当前会话的可重复流程捕获为新的 skill |
| doc-review | `.kimi-code/skills/doc-review/` | Markdown 笔记规范检查 |
| mcu-note-creator | `.kimi-code/skills/mcu-note-creator/` | 按规范创建 MCU 笔记 |
| safespi-evaluator | `.kimi-code/skills/safespi-evaluator/` | SafeSPI Rev 2.0 支持性五层评估 |
| git-upload-push | `.kimi-code/skills/git-upload-push/` | 一键 git add/commit/push（直接推 master） |
| purpose-driven-book-study | `.kimi-code/skills/purpose-driven-book-study/` | 目的驱动型精读：按问题主线学书籍/标准/长文档，阶段化沉淀 |
| kb-workflow | `.kimi-code/skills/kb-workflow/` | 工作流编排层：阶段→技能流水线表与"用前重读"纪律 |

> **技能结构约定**：每个技能文件夹遵循多文件结构 — `SKILL.md`（入口与触发条件）、`reference.md`（详细用法）、`gotchas.md`（陷阱与失败模式）、`config.json`（配置）、`scripts/`（可执行脚本）。参考实现：`self-improving-agent`、`context-compress`。

### 5.2 自定义子代理

`.kimi-code/agents/` 下定义了项目级子代理，主 Agent 可在合适时机委派（独立上下文执行，结果回传）：

| 子代理 | 文件 | 用途 |
|--------|------|------|
| note-organizer | `.kimi-code/agents/note-organizer.md` | 批量整理 Inbox / 未归档笔记（移动 + 重命名），独立上下文执行不污染主会话 |
| kb-reviewer | `.kimi-code/agents/kb-reviewer.md` | 只读合规审查：按本规范检查笔记，输出分级报告 |

### 5.3 summarize（内容提取）

**位置**：`.kimi-code/skills/summarize/summarize.py`（Claude Code 镜像：`.claude/skills/summarize/summarize.py`，Windows 原生 Python 脚本）。

**关键限制**：用户无第三方 LLM API 密钥，脚本自动回退到内容提取模式。

**使用方式**：
```bash
# 仅提取内容（无 LLM 调用）—— 将输出复制到对话中让 AI 总结
py -3 .kimi-code/skills/summarize/summarize.py "https://example.com" --print-content

# 保存长内容到文件，然后在对话中引用
py -3 .kimi-code/skills/summarize/summarize.py "https://example.com" --print-content --output doc.md

# 本地 PDF 提取
py -3 .kimi-code/skills/summarize/summarize.py "path/to/file.pdf" --print-content
```

**依赖**：`requests`、`beautifulsoup4`（必需）；`PyPDF2`（PDF 支持）；`yt-dlp`（YouTube 支持）。

**Windows 包装器**：`%USERPROFILE%\.local\bin\summarize.cmd` 提供相同 CLI 接口。

### 5.4 PDF 处理

Python 版 PDF 工具包，定义见 pdf 技能的 `SKILL.md`（§5.1）：

| 任务 | 工具 |
|------|------|
| 提取文字 | `pdfplumber`（首选）、`pypdf`（备用） |
| 提取表格 | `pdfplumber` + `pandas` |
| 合并/拆分/旋转 | `pypdf` |
| 创建 PDF | `reportlab` |
| OCR 扫描件 | `pytesseract` + `pdf2image`（需 Tesseract-OCR 引擎，未安装） |

**已安装**：`pypdf`、`pdfplumber`、`reportlab`、`pandas`、`openpyxl`、`pytesseract`（仅 Python 库）。
**未安装**：Tesseract-OCR 引擎、poppler（`pdftoppm`）。

### 5.5 MinerU PDF 解析

mineru-pdf-parser 技能（§5.1）提供基于 MinerU 云端 API 的文档解析，支持 PDF/Word/PPT/Excel/图片转结构化 Markdown，保留标题层级、表格结构、公式、多栏排版。

- 触发条件：用户提到"PDF转Markdown"、"解析文档"、"提取文档内容"等
- 详细用法见该技能的 `SKILL.md`

---

## 6. 代理工作流

以下要求**不区分是否新会话**，每次接到用户任务时都必须执行。

### 6.1 任务开始前 — 回顾学习档案

1. **读取 `.learnings/` 目录下的三个文件**：
   - `.learnings/LEARNINGS.md` — 过往修正、洞察、最佳实践
   - `.learnings/ERRORS.md` — 已发生的错误与踩坑记录
   - `.learnings/FEATURE_REQUESTS.md` — 用户曾提出的功能/能力需求
2. **搜索与当前任务相关的条目**：
   - 使用 `grep` 或阅读文件，查找与当前主题（如 `TC3xx`、`SPI`、`内核` 等）相关的记录。
3. **如果发现相关记录**：
   - 在回复中简要提及（例如："根据之前的记录 `LRN-2026...`，我已知..."）。
   - 避免重复犯同样的错误。

### 6.2 任务进行中 — 实时记录

在任务执行过程中，一旦触发以下场景，**必须立即记录**，不要等到任务结束：

| 场景 | 记录文件 | 格式要求 |
|------|---------|---------|
| 命令/操作失败（非零退出码、异常、超时） | `.learnings/ERRORS.md` | `ERR-YYYYMMDD-XXX` 格式 |
| 用户纠正你的回答（"不对"、"应该是"、"你错了"） | `.learnings/LEARNINGS.md` | `LRN-YYYYMMDD-XXX`，category: `correction` |
| 用户提出当前不具备的能力（"我希望你能..."） | `.learnings/FEATURE_REQUESTS.md` | `FEAT-YYYYMMDD-XXX` |
| 发现更好的方法/模式（可以复用的经验） | `.learnings/LEARNINGS.md` | `LRN-YYYYMMDD-XXX`，category: `best_practice` |
| 外部工具/API 行为与预期不符 | `.learnings/ERRORS.md` | `ERR-YYYYMMDD-XXX`，注明集成细节 |
| 知识过时或盲区被填补 | `.learnings/LEARNINGS.md` | `LRN-YYYYMMDD-XXX`，category: `knowledge_gap` |

**记录格式**：遵循 self-improving-agent 技能 `SKILL.md`（§5.1）中的模板，包含：
- 标题 `## [ID] category/name`
- `**Logged**`、`**Priority**`、`**Status**`、`**Area**`
- `### Summary`、`### Details`、`### Suggested Action`、`### Metadata`

**禁止**：不要在记录中写入密钥、Token、密码、完整配置文件或命令输出的完整转录。使用摘要或脱敏片段。

### 6.3 任务结束后 — 总结与提升

1. **检查本次任务是否有值得记录的学习点**：
   - 如果任务中犯了错误、被纠正、或发现了可复用的模式，确保已记录。
2. **评估是否晋升（Promote）**：
   - 如果某条学习具有跨任务通用性（非一次性问题），将其精简后追加到本文件或项目文档的合适章节。
   - 晋升后，在原记录中更新 `**Status**: promoted`。
3. **月度 retro（每月一次，或 `.learnings/` 积累 10+ 条未处理记录时）**：
   - 按 `self-improving-agent` SKILL.md 的「月度回顾」流程执行：聚类复发问题 → 产出本指南 / skill 修订建议 → 用户确认后晋升并销账。

### 6.4 常见借口与反模式（Shortcuts to Resist）

以下"合理借口"在过往任务中反复导致返工。识别到自己产生这些想法时，按右栏执行：

| 借口 | 为什么错 / 正确做法 |
|------|---------------------|
| "先放 Inbox 以后再整理" | Inbox 只进不出就失去意义。可以临时存放，但同一会话内应完成归档（kb-workflow 流水线 A4），或明确告知用户待办 |
| "文件名大概对就行" | 命名规范就是为防跨层同名混淆，差一个前缀就失效。对照 §3.2 命名表逐字核对 |
| "直接改原笔记内容" | 违反 §9.1 第 3 条。保留原文，在下方新增"整理版"或"补充理解" |
| "这个 skill 上次读过，凭记忆用" | 上下文压缩后内容可能已丢失。每个阶段开始前重读对应 SKILL.md（见 kb-workflow「用前重读纪律」） |
| "用户需求够清楚，直接做" | 存在多方案、删除/重命名、批量改动时必须先确认（LRN-20260717-001）。一次性成功优先于速度 |
| "检查脚本大概能过，跳过 doc-review" | 一分钟的检查跳过后，归档返工要动 git 历史，成本翻倍（2026-08-06 起 Claude Code 侧已由 PostToolUse hook 自动执行） |
| "记录过 learning 就算改进了" | 记录≠改进。按 §6.3 月度 retro 把复发问题转化为本指南 / skill 的实际修订 |
| "指南只改了 AGENTS.md / CLAUDE.md 其中一份" | 两份内容必须一致。直接改任一份即可，git pre-commit hook 会以较新者自动同步另一份；不走 git 的修改需手动运行 `scripts/sync-guides.ps1` |

---

## 7. 环境依赖

| 工具/库 | 状态 | 说明 |
|---------|------|------|
| Node.js / npx | 已安装 | 用于技能发现（`npx skills`） |
| Python | 已安装 | 用于 PDF 处理和 summarize 脚本；⚠️ Git Bash 中 `python`/`python3` 为 WindowsApps 占位 stub（无法执行），一律用 `py -3`（ERR-20260806-001） |
| pypdf | 已安装 | — |
| pdfplumber | 已安装 | — |
| reportlab | 已安装 | — |
| pandas + openpyxl | 已安装 | — |
| pytesseract | 已安装（Python 库） | 需配合 Tesseract-OCR 引擎（暂不安装） |
| pdf2image | 已安装（Python 库） | 需配合 poppler 工具（暂不安装） |
| Tesseract-OCR | 暂缓 | OCR 扫描版 PDF 时才需要 |
| poppler (pdftoppm) | 暂缓 | PDF 转图片时才需要 |

**平台**：Windows 10 原生（无 WSL2），Shell 为 bash（Git Bash / MSYS2）。
**无构建系统**：本项目为文档项目，无编译、无 lint、无测试套件。

---

## 8. .kimi-code/ 与 .claude/ 目录说明

`.kimi-code/` 为 Kimi Code 项目配置区：

| 子目录 | 内容 |
|--------|------|
| `skills/` | 项目技能（完整清单与触发时机见 §5.1，`.claude/skills/` 的镜像副本） |
| `agents/` | 自定义子代理（见 §5.2） |

`.claude/` 为 Claude Code 配置区，同时存放两套工具**共享的参考资料**，处理相关主题时按需读取：

| 子目录 | 内容 |
|--------|------|
| `references/knowledge-base/` | MCU 架构、通信协议、诊断、外设测试、功能安全、区域架构等参考资料 |
| `memory/` | 记忆索引（`MEMORY.md`）与文件分类速查表（`file-classification-cheatsheet.md`） |
| `skills/` | Claude Code 技能（源副本，与 `.kimi-code/skills/` 内容保持一致） |
| `settings.json` / `hooks/` | Claude Code 钩子配置（PostToolUse doc-review 等） |

---

## 9. Obsidian 知识库管理规范

以下规则适用于管理本仓库对应的 Obsidian Vault，确保知识库的结构化、可维护性与安全性。

### 9.1 总原则

| 编号 | 规则 |
|------|------|
| 1 | 所有笔记使用 Markdown 格式。 |
| 2 | 不要随意删除已有笔记。删除前必须先移动到 `90_Archive_归档`，除非文件位于 `00_Test_Agent` 测试目录。 |
| 3 | 修改笔记前，优先保留原始内容，在下方新增"整理版"或"补充理解"。 |
| 4 | 不要破坏 Obsidian 双链格式，例如 `[[AURIX TC3xx]]`。 |
| 5 | 不要把所有内容塞进一个大文件，应按主题拆分。 |
| 6 | 附件统一放入 `99_Attachments_附件`。 |
| 7 | 新增临时内容先放入 `00_Inbox_临时收集`。 |
| 8 | 车规 MCU 相关内容放入 `01_MCU_车规MCU`。 |
| 9 | 生物医学、论文、动脉粥样硬化相关内容放入 `02_Biomed_动脉粥样硬化`。 |
| 10 | 投资、AI 产业链、个股跟踪内容放入 `03_AI产业链投资`。 |
| 11 | AI 工具、Agent、Claude Code / Kimi Code、Obsidian 相关内容放入 `91_Tools_AI工具链`。 |
| 12 | 笔记层（01-05、91 等主题目录）与 `99_Attachments_附件` 按**角色**分界，不按文件类型：消化后的产出（精读/伴读/总结/分析笔记、专题体系）进笔记层，按主题组织、持续迭代；原始素材（PDF 原件、MinerU 原始解析 full.md+images、图片）进 `99_Attachments_附件`，按资料来源组织、入库后不再改动。引用方向单向：笔记 → 附件。移动附件内任何文件前必须 grep 找全引用，移动后逐条校验链接可解析。 |

### 9.2 笔记格式

每篇知识型笔记尽量采用以下结构：

```markdown
# 标题

## 核心问题

## 结论

## 背景

## 关键机制

## 应用场景

## 关联笔记

## 待补充问题

## 标签

## Agent 整理记录
```

### 9.3 安全要求

| 编号 | 规则 |
|------|------|
| 1 | 批量修改前先列出计划。 |
| 2 | 不要一次性重命名大量文件。 |
| 3 | 不要修改 `.obsidian` 配置目录，除非明确要求。 |
| 4 | 不要删除附件，除非明确要求。 |

---

## 10. 更新记录

| 日期 | 更新内容 |
|------|---------|
| 2026-10-14 | **双入口统一 + 双向同步机制**：`AGENTS.md` 与 `.claude/CLAUDE.md` 合并为逐字节一致的同一份内容（泛化工具名引用；并入 CLAUDE 侧独有的 §2 核心工作原则、Obsidian 规则 12、`purpose-driven-book-study` 技能登记、`py -3` 警告，以及 Kimi 侧独有的 §5.2 自定义子代理、`.claude/memory/` 目录说明）；新增 `scripts/sync-guides.ps1` 与 git pre-commit hook——此后修改任一份，提交时自动以较新者同步另一份 |
| 2026-08-15 | 新增技能 `purpose-driven-book-study`（GPT 版 skill 内化为多文件格式：SKILL.md+reference+gotchas+config+模板，绑定本库命名/doc-review/附件规则/对话渲染限制；另产出 Kimi Code 自包含指令版 `references/kimi-code-instruction.md`；GPT 原件归档 `90_Archive_归档/`）；记录对话渲染限制（LRN-20260815-001：对话内禁 LaTeX/Mermaid，公式纯文本、图用 ASCII） |
| 2026-08-06 | 新增 PostToolUse hook 自动规范检查（过程检验硬护栏化）：`.claude/hooks/doc_review_on_md_edit.py` 在 Edit/Write 仓库内笔记后自动运行 doc-review 并将问题注入上下文（登记于 `.claude/settings.json`，排除附件/Inbox/归档等目录）；doc-review 校准：修复代码块闭合围栏误计 bug、必要章节 fail 限定 MCU 笔记层（新增 `strictTemplateDirs` 配置）、文件名前缀白名单补 `Agent_`/`AI_`、豁免 INDEX.md/README.md；§7 记录 Git Bash 须用 `py -3`（ERR-20260806-001） |
| 2026-08-06 | §9.1 新增规则 12：明确笔记层与 `99_Attachments_附件` 的角色边界（消化产出 vs 原始素材）、单向引用方向、移动附件的引用校验要求；`91_Tools_AI工具链` 新增 `02_Google_Agent_Whitepapers_Google白皮书`、`03_AI_Startup_AI原生创业`；附件按主题分为 `AI_Agent/`、`Memory_存储器/`、`IC_Design_芯片设计/` |
| 2026-08-04 | **Kimi Code 配置落地**：以 `.claude/CLAUDE.md` 为蓝本创建根 `AGENTS.md`；技能复制适配至 `.kimi-code/skills/`；新增 `.kimi-code/agents/` 两个自定义子代理（note-organizer、kb-reviewer）；`.claude/` 保留，references/memory 由两套工具共享引用 |
| 2026-08-04 | 借鉴 Jason_HPC_Work-main 工作区：新增 §2「核心工作原则与协作规范」，包含第一性原理、行动规范、协作规范（六条思维纪律） |
| 2026-07-26 | 新增「思维与协作纪律」：总原则三问、第一性原理（工作方式 6 步、回答原则）、人机协作边界 3 条、六条思维纪律、出错三分法；checkpoint 约定与 ERR 根因分类为新立项目约定 |
| 2026-07-19 | 借鉴 google/agents-cli 的 skill 工程模式（LRN-20260719-001）：新增 `kb-workflow` 编排技能（阶段→技能流水线表 + 用前重读纪律）；为 5 个技能描述补充负向触发边界；新增反模式表；月度 retro 闭环；技能表补齐遗漏登记 |
| 2026-07-05 | 新增本地技能 `note-organizer`：按目录与命名规范自动整理 Markdown 笔记；将两篇原子操作笔记归档至 `01_Hardware_硬件层/01_Core/03_Comparison/` |
| 2026-06-05 | 新增"Obsidian 知识库管理规范"；本地技能目录从 `skills/` 迁移至 `.claude/skills/`，新增 docx-cn、mineru-pdf-parser 登记 |
| 2026-06-05 | **工作区重构**：建立车规 MCU 技术栈分层架构（Hardware / Middleware / Application）；目录全英文化；Peripherals 按功能（Comm/Timer/IO/Storage）拆分；Core 按架构（AURIX/ARM/Comparison）细分；新增 AUTOSAR 和 FreeRTOS 完整目录框架；制定文件命名规范 |
| 2026-06-05 | **深度细分**：Hardware 层全部细化（Memory→RAM/Flash/Cache/MPU、System→Clock/Power/Reset/Bus/DMA/Interrupt、Boot→Bootloader/BootROM/FirmwareUpdate、Peripherals/Comm→SPI/I2C/CAN/LIN/UART/Ethernet/FlexRay/Intercore、Timer→GPT/PWM/ICU/WDG、IO→GPIO/ADC/DAC、Multicore→Lockstep/Resource/Intercore、Debug→CoreSight/Trace/JTAG/CrossTrigger）；新增 `04_Safety_功能安全`（ISO26262/E2E/SafetyMonitor/Lockstep）和 `05_Tools_工具链`（Compiler/Debugger/Flash/Trace/HIL_SIL）；AUTOSAR 全部细化到模块级；FreeRTOS 细化到子模块级；文件命名规则扩展至 28 条覆盖全部层次 |
| 2026-05-17 | 融合 CLAUDE.md 与 AGENTS.md，精简 .claude/ 目录适配知识库项目 |
| 2026-05-11 | 初始版本：整合 find-skills、pdf、self-improving-agent、summarize 四个技能 |

---

> **提示**：本文件由 AI 代理读取并遵循。如有冲突，以用户当前对话中的直接指令为准。
