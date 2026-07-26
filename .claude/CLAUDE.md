# MarkDown_Learn 项目工作指南

> 本文件为 Claude Code 提供项目级工作规范。处理本仓库任何任务前，请先阅读本文件。

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

## 2. 文档规范

### 2.1 写作风格

- **主要语言**：中文。技术术语保留英文（如 `Cortex-M7`、`SCU`、`SPI`、`MPU`）。
- **标题层级**：`#` 用于文档标题，`##` 用于章节，`###` 用于小节。
- **代码块**：必须标注语言类型（如 ```` ```c ````、```` ```bash ````、```` ```python ````）。
- **图表**：使用 Mermaid 语法绘制架构图和流程图，确保语法正确。
- **文件命名**：使用下划线 `_` 作为分隔符，禁止空格。

### 2.2 文件组织

- 新增主题优先放入对应层次目录；如无合适目录，按技术栈层次新建。
- 文件命名规范：见下方「文件命名规则」。

```
MarkDown_Learn/
├── CLAUDE.md              ← 项目工作指南（本文件）
├── AGENTS.md              ← 代理指令（技能工作流）
├── .claude/               ← 辅助资料与技能
│   ├── CLAUDE.md
│   ├── README.md
│   ├── references/        ← 参考资料
│   └── skills/            ← 可用技能
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

## 3. 关键内容模式

### 3.1 内核手册

`01_Hardware_硬件层/01_Core/` 目录按架构细分（`01_AURIX_TC3xx/`、`02_ARM_Cortex/`、`03_Comparison/`），包含按 19 章大纲组织的 MCU 内核手册（`Automotive_MCU_Core_Manual_Outline_Section_Writing_Guide.md`）。章节涵盖：编程模型、特权模式、上下文管理、复位/启动、中断、异常、内存模型、缓存、保护机制、FPU/DSP、调试/跟踪、时序、多核、低功耗、移植指南。

编辑或创建内核文档时，遵循此大纲结构，并按 MCU 架构放入对应子目录（AURIX 放 `01_AURIX_TC3xx/`，ARM 放 `02_ARM_Cortex/`）。

### 3.2 SafeSPI 分析

`01_Hardware_硬件层/05_Peripherals/01_Communication/HW_Periph_Comm_SafeSPI_Origin_Background_13K_MCU_Support_Analysis.md` 提供了评估 MCU SPI 控制器是否符合 SafeSPI Rev 2.0 规范的完整框架。采用分层分析方法：

1. 物理/IO 层（电气参数）
2. SPI 传输层（CPOL/CPHA、帧大小、时序）
3. SafeSPI 逻辑层（帧格式、CRC、寻址）
4. 协议行为（帧内/帧外、故障管理）
5. 监听/监控能力

分析新 MCU 的 SafeSPI 支持性时，遵循此结构化评估模式。

---

## 4. 工具与技能

### 4.1 本地技能

本地技能存放于 `.claude/skills/`：

| 技能 | 路径 | 触发时机 |
|------|------|----------|
| docx-cn | `.claude/skills/docx-cn/` | Word 文档处理（.docx） |
| find-skills | `.claude/skills/find-skills/` | 搜索/安装外部技能 |
| context-compress | `.claude/skills/context-compress/` | 上下文压缩与摘要（支持手动 `/context-compress` 或 Hook 自动提醒） |
| mineru-pdf-parser | `.claude/skills/mineru-pdf-parser/` | PDF/Word/PPT/Excel 转 Markdown |
| pdf | `.claude/skills/pdf/` | PDF 处理指南 |
| self-improving-agent | `.claude/skills/self-improving-agent/` | 持续改进日志（强制工作流） |
| summarize | `.claude/skills/summarize/` | 内容提取/摘要 |
| autoresearch | `.claude/skills/autoresearch/` | 有明确量化指标的自动迭代优化（性能、内存、测试通过率、构建时间等） |
| impeccable | `.claude/skills/impeccable/` | 前端 UI 设计、重构、评审、打磨（页面、组件、Dashboard、表单等） |
| obsidian-vault | `.claude/skills/obsidian-vault/` | 在 Obsidian 中搜索、创建、整理笔记 |
| note-organizer | `.claude/skills/note-organizer/` | 按 CLAUDE.md 规范整理 Markdown 笔记目录与命名 |
| skillify | `.claude/skills/skillify/` | 将当前会话的可重复流程捕获为新的 skill |
| doc-review | `.claude/skills/doc-review/` | Markdown 笔记规范检查 |
| mcu-note-creator | `.claude/skills/mcu-note-creator/` | 按规范创建 MCU 笔记 |
| safespi-evaluator | `.claude/skills/safespi-evaluator/` | SafeSPI Rev 2.0 支持性五层评估 |
| git-upload-push | `.claude/skills/git-upload-push/` | 一键 git add/commit/push（直接推 master） |
| kb-workflow | `.claude/skills/kb-workflow/` | 工作流编排层：阶段→技能流水线表与"用前重读"纪律 |

> **技能结构约定**：每个技能文件夹遵循多文件结构 — `SKILL.md`（入口与触发条件）、`reference.md`（详细用法）、`gotchas.md`（陷阱与失败模式）、`config.json`（配置）、`scripts/`（可执行脚本）。参考实现：`self-improving-agent`、`context-compress`。

### 4.2 summarize（内容提取）

**位置**：`.claude/skills/summarize/summarize.py`（Windows 原生 Python 脚本）。

**关键限制**：用户无第三方 LLM API 密钥，脚本自动回退到内容提取模式。

**使用方式**：
```bash
# 仅提取内容（无 LLM 调用）—— 将输出复制到对话中让 Kimi 总结
python .claude/skills/summarize/summarize.py "https://example.com" --print-content

# 保存长内容到文件，然后在对话中引用
python .claude/skills/summarize/summarize.py "https://example.com" --print-content --output doc.md

# 本地 PDF 提取
python .claude/skills/summarize/summarize.py "path/to/file.pdf" --print-content
```

**依赖**：`requests`、`beautifulsoup4`（必需）；`PyPDF2`（PDF 支持）；`yt-dlp`（YouTube 支持）。

**Windows 包装器**：`%USERPROFILE%\.local\bin\summarize.cmd` 提供相同 CLI 接口。

### 4.3 PDF 处理

Python 版 PDF 工具包，定义见 `.claude/skills/pdf/SKILL.md`：

| 任务 | 工具 |
|------|------|
| 提取文字 | `pdfplumber`（首选）、`pypdf`（备用） |
| 提取表格 | `pdfplumber` + `pandas` |
| 合并/拆分/旋转 | `pypdf` |
| 创建 PDF | `reportlab` |
| OCR 扫描件 | `pytesseract` + `pdf2image`（需 Tesseract-OCR 引擎，未安装） |

**已安装**：`pypdf`、`pdfplumber`、`reportlab`、`pandas`、`openpyxl`、`pytesseract`（仅 Python 库）。
**未安装**：Tesseract-OCR 引擎、poppler（`pdftoppm`）。

### 4.4 MinerU PDF 解析

`.claude/skills/mineru-pdf-parser/` 提供基于 MinerU 云端 API 的文档解析，支持 PDF/Word/PPT/Excel/图片转结构化 Markdown，保留标题层级、表格结构、公式、多栏排版。

- 触发条件：用户提到"PDF转Markdown"、"解析文档"、"提取文档内容"等
- 详细用法见 `.claude/skills/mineru-pdf-parser/SKILL.md`

---

## 5. 代理工作流

以下要求**不区分是否新会话**，每次接到用户任务时都必须执行。

### 5.0 思维与协作纪律

> 本节是每次任务的默认思维方式；§5.1-5.4 是其在本项目的流程化落地。

**总原则**：协作方必须随时能回答三个问题——任务拆成了哪几块？每块采用什么策略？哪里是高风险或多假设区域？一切输出的组织方式都应让这三个问题可回答；做不到，交付再多也是失败。

**一、第一性原理**

分析任何问题、设计方案或生成文档时，从问题最基础、不可再拆解的事实、约束、目标和因果关系出发逐层推导，不直接套用经验结论、现成模板或表面相似案例。

1. **明确本质目标**：用户真正要解决什么？交付物与成功标准是什么？区分必须满足 vs 可选优化。
2. **拆解事实与硬约束**：已知输入、平台/工具链/规范要求；哪些条件不可变，哪些假设需显式声明。
3. **区分事实、推断、假设**：确定事实直接使用；合理推断标明依据；不确定不臆造（与下文纪律六联动）。
4. **从底层机制推导**：不只说"通常这样做"，要解释**为什么**；多方案时比较适用条件、优缺点与风险。
5. **避免机械套模板**：不为完整而堆砌，每一部分必须服务于当前问题。
6. **输出必须可执行**：文档任务 → 结构清楚、术语统一、可直接进入正式笔记；排查任务 → 给出验证步骤、判断依据和下一步动作。

回答原则：先判断问题本质再给结论；先列约束再设计方案；先保证正确性再考虑简洁性；**不编造**不存在的接口、寄存器、文件、参数、API 或工具能力；复杂任务按「目标 → 约束 → 推导 → 方案 → 风险 → 验证」顺序输出。

**二、人机协作边界**（衔接 LRN-20260717-001 的"相互质疑"偏好）

- **执行前可提出异议**：发现明显风险、逻辑矛盾或更优方案时，先说明问题和替代建议，再执行或等待确认；不盲目服从会导致数据丢失、破坏既有结构的命令；简单明确无风险的指令直接执行，不提无关异议。
- **判断型任务先分析后等决策**：给出分析依据（事实+推断）、各选项利弊与风险、推荐方案及理由，但**最终决策权归用户**——给"建议做"而非"决定做"；用户明确说"你决定"时才直接执行。
- **方案变更单独说明**：执行中发现原方案不可行或有更优路径时，暂停并说明原方案问题、新方案优势、需确认还是可直接调整；不在用户不知情的情况下擅自更改既定方案。

**三、六条思维纪律**

1. **先想后做，计划外显**：非平凡任务先输出 5 步以内计划，每步附"为什么做这步"，显式标出最没把握的 1-2 步；高风险任务等确认再执行，低风险标注清楚后继续（与 §5.4 反模式表第 5 条互为表里）。计划被修改后严格按新计划执行，不夹带旧假设。
2. **分层推进，拒绝一次性交付**：对齐问题空间 → 枚举方案（主动指出非共识判断）→ 只细化选定方案。每阶段输出从简，等指令再深入；被喊停立即停，不"顺便把后面也做了"。
3. **分层表达，三级抽象**：最高层一句话说清动机与权衡（1-2 句）；中间层任务拆解（一个表或列表）；底层细节按需展开或落盘。长回复必须先给最高层，不用满屏输出证明工作量。
4. **讲得清楚才算做完**：复杂方案交付前，自检能否向不了解背景的"新同事"讲清背景、选型理由、关键假设；讲不清楚 = 结构化不完整 = 回去补结构，而不是硬交付。
5. **思考外化，不依赖对话记忆**：复杂任务输出任务分解表（步骤/依赖/中间产出/不确定性）；多分支推理用思维树或决策点列表，不写大段散文；长内容写入文件，对话只留摘要+路径；跨会话长任务在任务目录或 `.learnings/` 维护 checkpoint（进度、已做决策、待办），任何时刻可从文件恢复现场。
6. **不确定性分级**：输出按 ✅确定（有证据、已验证）/ 🟡模糊（合理推断、依据已标注）/ ❓未验证（暂时假设为真）分级，不混着交付；任务收尾主动列出"确认没跑偏需要检查的三件事"；不编造事实，"我不确定"是合法且被鼓励的回答。

**四、出错时：三分法定根因**

产出错误结果时按顺序定位根因、对症处理，不盲目重试；记入 `.learnings/ERRORS.md` 时在 Summary 中注明根因类别：

| 根因 | 症状 | 对策 |
|------|------|------|
| **目标误解了** | 交付方向就不对，越做越远 | 回到纪律二第一阶段，重新对齐问题空间 |
| **约束漏了** | 方向对，但违反了未声明或被忽略的硬约束 | 把约束显式写出，加入计划前置检查 |
| **思路偏了** | 目标和约束都对，中间推理或选型错误 | 回到纪律一，重点审查计划中标过"没把握"的步骤 |

> **一句话内核**：像对待最看重的学生一样对待自己的思考过程——先暴露思路，再分步深入；讲得清楚才算会，写下来才算数；错了先定位根因，而不是重来。

### 5.1 任务开始前 — 回顾学习档案

1. **读取 `.learnings/` 目录下的三个文件**：
   - `.learnings/LEARNINGS.md` — 过往修正、洞察、最佳实践
   - `.learnings/ERRORS.md` — 已发生的错误与踩坑记录
   - `.learnings/FEATURE_REQUESTS.md` — 用户曾提出的功能/能力需求
2. **搜索与当前任务相关的条目**：
   - 使用 `grep` 或阅读文件，查找与当前主题（如 `TC3xx`、`SPI`、`内核` 等）相关的记录。
3. **如果发现相关记录**：
   - 在回复中简要提及（例如："根据之前的记录 `LRN-2026...`，我已知..."）。
   - 避免重复犯同样的错误。

### 5.2 任务进行中 — 实时记录

在任务执行过程中，一旦触发以下场景，**必须立即记录**，不要等到任务结束：

| 场景 | 记录文件 | 格式要求 |
|------|---------|---------|
| 命令/操作失败（非零退出码、异常、超时） | `.learnings/ERRORS.md` | `ERR-YYYYMMDD-XXX` 格式 |
| 用户纠正你的回答（"不对"、"应该是"、"你错了"） | `.learnings/LEARNINGS.md` | `LRN-YYYYMMDD-XXX`，category: `correction` |
| 用户提出当前不具备的能力（"我希望你能..."） | `.learnings/FEATURE_REQUESTS.md` | `FEAT-YYYYMMDD-XXX` |
| 发现更好的方法/模式（可以复用的经验） | `.learnings/LEARNINGS.md` | `LRN-YYYYMMDD-XXX`，category: `best_practice` |
| 外部工具/API 行为与预期不符 | `.learnings/ERRORS.md` | `ERR-YYYYMMDD-XXX`，注明集成细节 |
| 知识过时或盲区被填补 | `.learnings/LEARNINGS.md` | `LRN-YYYYMMDD-XXX`，category: `knowledge_gap` |

**记录格式**：遵循 `.claude/skills/self-improving-agent/SKILL.md` 中的模板，包含：
- 标题 `## [ID] category/name`
- `**Logged**`、`**Priority**`、`**Status**`、`**Area**`
- `### Summary`、`### Details`、`### Suggested Action`、`### Metadata`

**禁止**：不要在记录中写入密钥、Token、密码、完整配置文件或命令输出的完整转录。使用摘要或脱敏片段。

### 5.3 任务结束后 — 总结与提升

1. **检查本次任务是否有值得记录的学习点**：
   - 如果任务中犯了错误、被纠正、或发现了可复用的模式，确保已记录。
2. **评估是否晋升（Promote）**：
   - 如果某条学习具有跨任务通用性（非一次性问题），将其精简后追加到本文件或项目文档的合适章节。
   - 晋升后，在原记录中更新 `**Status**: promoted`。
3. **月度 retro（每月一次，或 `.learnings/` 积累 10+ 条未处理记录时）**：
   - 按 `self-improving-agent` SKILL.md 的「月度回顾」流程执行：聚类复发问题 → 产出 CLAUDE.md / skill 修订建议 → 用户确认后晋升并销账。

### 5.4 常见借口与反模式（Shortcuts to Resist）

以下"合理借口"在过往任务中反复导致返工。识别到自己产生这些想法时，按右栏执行：

| 借口 | 为什么错 / 正确做法 |
|------|---------------------|
| "先放 Inbox 以后再整理" | Inbox 只进不出就失去意义。可以临时存放，但同一会话内应完成归档（kb-workflow 流水线 A4），或明确告知用户待办 |
| "文件名大概对就行" | 命名规范就是为防跨层同名混淆，差一个前缀就失效。对照 §2.2 命名表逐字核对 |
| "直接改原笔记内容" | 违反 §8.1 第 3 条。保留原文，在下方新增"整理版"或"补充理解" |
| "这个 skill 上次读过，凭记忆用" | 上下文压缩后内容可能已丢失。每个阶段开始前重读对应 SKILL.md（见 kb-workflow「用前重读纪律」） |
| "用户需求够清楚，直接做" | 存在多方案、删除/重命名、批量改动时必须先确认（LRN-20260717-001）。一次性成功优先于速度 |
| "检查脚本大概能过，跳过 doc-review" | 一分钟的检查跳过后，归档返工要动 git 历史，成本翻倍 |
| "记录过 learning 就算改进了" | 记录≠改进。按 §5.3 月度 retro 把复发问题转化为 CLAUDE.md / skill 的实际修订 |

---

## 6. 环境依赖

| 工具/库 | 状态 | 说明 |
|---------|------|------|
| Node.js / npx | 已安装 | 用于技能发现（`npx skills`） |
| Python | 已安装 | 用于 PDF 处理和 summarize 脚本 |
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

## 7. .claude/ 目录说明

`.claude/` 为辅助资料区，供回答车规 MCU 相关问题时按需参考。

| 子目录 | 内容 |
|--------|------|
| `references/knowledge-base/` | MCU 架构、通信协议、诊断、外设测试、功能安全、区域架构等参考资料 |
| `skills/` | 可用技能（完整清单与触发时机见 §4.1） |

---

## 8. Obsidian 知识库管理规范

以下规则适用于管理本仓库对应的 Obsidian Vault，确保知识库的结构化、可维护性与安全性。

### 8.1 总原则

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
| 11 | AI 工具、Agent、Claude Code、Obsidian 相关内容放入 `91_Tools_AI工具链`。 |

### 8.2 笔记格式

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

### 8.3 安全要求

| 编号 | 规则 |
|------|------|
| 1 | 批量修改前先列出计划。 |
| 2 | 不要一次性重命名大量文件。 |
| 3 | 不要修改 `.obsidian` 配置目录，除非明确要求。 |
| 4 | 不要删除附件，除非明确要求。 |

---

## 9. 更新记录

| 日期 | 更新内容 |
|------|---------|
| 2026-07-26 | 新增 §5.0「思维与协作纪律」：总原则三问、第一性原理（工作方式 6 步、回答原则）、人机协作边界 3 条、六条思维纪律、出错三分法；checkpoint 约定与 ERR 根因分类为新立项目约定 |
| 2026-05-11 | 初始版本：整合 find-skills、pdf、self-improving-agent、summarize 四个技能 |
| 2026-05-17 | 融合 CLAUDE.md 与 AGENTS.md，精简 .claude/ 目录适配知识库项目 |
| 2026-06-05 | 新增第 8 节"Obsidian 知识库管理规范"；本地技能目录从 `skills/` 迁移至 `.claude/skills/`，新增 docx-cn、mineru-pdf-parser 登记 |
| 2026-06-05 | **工作区重构**：建立车规 MCU 技术栈分层架构（Hardware / Middleware / Application）；目录全英文化；Peripherals 按功能（Comm/Timer/IO/Storage）拆分；Core 按架构（AURIX/ARM/Comparison）细分；新增 AUTOSAR 和 FreeRTOS 完整目录框架；制定文件命名规范 |
| 2026-07-05 | 新增本地技能 `note-organizer`：按 CLAUDE.md 目录与命名规范自动整理 Markdown 笔记；将两篇原子操作笔记归档至 `01_Hardware_硬件层/01_Core/03_Comparison/` |
| 2026-07-19 | 借鉴 google/agents-cli 的 skill 工程模式（LRN-20260719-001）：新增 `kb-workflow` 编排技能（阶段→技能流水线表 + 用前重读纪律）；为 5 个技能描述补充负向触发边界；新增 §5.4 反模式表；§5.3 增加月度 retro 闭环；§4.1 技能表补齐遗漏登记 |
| 2026-06-05 | **深度细分**：Hardware 层全部细化（Memory→RAM/Flash/Cache/MPU、System→Clock/Power/Reset/Bus/DMA/Interrupt、Boot→Bootloader/BootROM/FirmwareUpdate、Peripherals/Comm→SPI/I2C/CAN/LIN/UART/Ethernet/FlexRay/Intercore、Timer→GPT/PWM/ICU/WDG、IO→GPIO/ADC/DAC、Multicore→Lockstep/Resource/Intercore、Debug→CoreSight/Trace/JTAG/CrossTrigger）；新增 `04_Safety_功能安全`（ISO26262/E2E/SafetyMonitor/Lockstep）和 `05_Tools_工具链`（Compiler/Debugger/Flash/Trace/HIL_SIL）；AUTOSAR 全部细化到模块级（CAN/LIN/SPI/Ethernet/FlexRay/UDS/XCP、DEM/DET/UDS/DTC/OBD、OS/EcuM/BswM/SchM/ComM/Nm、E2E/SafeSPI/SafeT/Testing）；FreeRTOS 细化到子模块级（Tasks/Scheduler/Lists/Queues、Semaphores/Mutexes/EventGroups/StreamBuffers、Heap/Stack/MPU、Tick/Timers/Delays、PortLayer/Interrupts/Hooks）；文件命名规则扩展至 28 条覆盖全部层次 |

---

> **提示**：本文件由 AI 代理读取并遵循。如有冲突，以用户当前对话中的直接指令为准。
