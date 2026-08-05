# MCU Note Creator — 详细参考

本文件是 `mcu-note-creator` Skill 的详细规范参考。完整项目规范见 [`AGENTS.md`](../../AGENTS.md)。

---

## 1. 决策流程

创建新笔记前，依次确认：

1. **主题属于哪个层次？**
   - Hardware（芯片、外设、系统、多核、调试、封装）
   - Middleware（AUTOSAR、FreeRTOS）
   - Application（业务逻辑、算法）
   - Safety（ISO 26262、E2E、Safety Monitor）
   - Tools（编译器、调试器、烧录、Trace、HIL/SIL）

2. **主题属于哪个子模块？**（如 Hardware / System / Clock）

3. **文件名前缀是什么？**（见下表）

4. **是否是临时/未整理内容？** → 先放 `00_Inbox_临时收集/`

5. **是否需要删除旧笔记？** → 禁止直接删除，先移入 `90_Archive_归档/`

---

## 2. 常用命名前缀速查

| 层次 | 前缀 | 示例 |
|------|------|------|
| Hardware / Core / AURIX | `{MCU}_Core_` | `AURIX_TC3xx_Core_Manual_Detailed_Mermaid.md` |
| Hardware / Core / ARM | `ARM_{Core}_Core_` | `ARM_M7_Core_Manual_Detailed_Mermaid.md` |
| Hardware / Memory | `HW_Mem_` 或 `{MCU}_Mem_` | `HW_Mem_RAM_Reset_Init_Report.md` |
| Hardware / System | `HW_Sys_` 或 `{MCU}_Sys_` | `AURIX_TC3xx_Sys_SCU_Software_Reset_Summary.md` |
| Hardware / Boot | `HW_Boot_` | `HW_Boot_Bootloader_Design.md` |
| Hardware / Peripherals / Comm | `HW_Periph_Comm_{协议}_` | `HW_Periph_Comm_SPI_Specification.md` |
| Hardware / Peripherals / Timer | `HW_Periph_Timer_` | `HW_Periph_Timer_GPT_Config.md` |
| Hardware / Peripherals / IO | `HW_Periph_IO_` | `HW_Periph_IO_ADC_Calibration.md` |
| Hardware / Multicore | `HW_MC_` 或 `{MCU}_MC_` | `AURIX_TC3xx_MC_Lockstep_Mechanism.md` |
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

**命名原则**：
- 用下划线 `_` 分隔，**禁止空格**
- 英文缩写统一大写：`SPI`、`CAN`、`ADC`、`GPIO`、`MPU`
- 同一主题跨层次时文件名必须能区分，例如 `HW_Periph_Comm_SafeSPI_...` vs `AUTOSAR_Safety_SafeSPI_...`

---

## 3. 常用目录速查

```
00_Inbox_临时收集/                 ← 临时/未整理内容
01_Hardware_硬件层/
  01_Core/
    01_AURIX_TC3xx/                ← TriCore、AURIX 专用
    02_ARM_Cortex/                 ← Cortex-M7、Cortex-R52
    03_Comparison/                 ← 架构对比
  02_Memory/                       ← RAM、Flash、Cache、MPU
  03_System/                       ← Clock、Power、Reset、Bus、DMA、Interrupt
  04_Boot/                         ← Bootloader、BootROM、Firmware Update
  05_Peripherals/
    01_Communication/              ← SPI/I2C/CAN/LIN/UART/Ethernet/FlexRay/Intercore
    02_Timer/                      ← GPT/PWM/ICU/WDG
    03_IO/                         ← GPIO/ADC/DAC
    04_Storage/                    ← Internal Flash/EEPROM Emulation
  06_Multicore/                    ← Lockstep/Resource/Intercore
  07_Debug/                        ← CoreSight/Trace/JTAG/CrossTrigger
  08_Packaging/                    ← 制造与封装
02_Middleware_中间件层/
  01_AUTOSAR/                      ← MCAL/BSW 各模块
  02_FreeRTOS/                     ← Kernel/Sync/Memory/Timing/Port
04_Safety_功能安全/                 ← ISO 26262/E2E/SafetyMonitor/Lockstep
05_Tools_工具链/                    ← Compiler/Debugger/Flash/Trace/HIL_SIL
90_Archive_归档/                   ← 归档草稿与历史版本
99_Attachments_附件/               ← 附件统一存放
```

---

## 4. 笔记模板（9 段式）

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

---

## 5. 写作风格

- **主要语言**：中文。技术术语保留英文，如 `Cortex-M7`、`SCU`、`SPI`、`MPU`。
- **标题层级**：`#` 用于文档标题，`##` 用于章节，`###` 用于小节。
- **代码块**：必须标注语言类型，如 ` ```c `、` ```bash `、` ```python `。
- **图表**：使用 Mermaid 语法。
- **双链**：保留 Obsidian 格式 `[[AURIX TC3xx]]`，不要破坏。

---

## 6. 创建步骤示例

**用户**："写一份 AURIX TC3xx SPI 从机模式配置笔记"

步骤：

1. 确定层次：Hardware / Peripherals / Communication / SPI
2. 目录：`01_Hardware_硬件层/05_Peripherals/01_Communication/01_SPI/`
3. 文件名：`AURIX_TC3xx_Periph_Comm_SPI_Slave_Mode_Config.md`
4. 生成 9 段式模板
5. 写入文件
6. （可选）在 `00_Inbox_临时收集/` 留草稿，整理后再归档到正式目录

---

## 7. 冲突处理

- **文件名已存在**：不要覆盖，检查内容后决定合并、重命名（加版本号/日期）或归档旧文件。
- **不确定目录**：先放入 `00_Inbox_临时收集/`，待分类明确后再迁移。
- **跨层次主题**：文件名必须体现层次，例如同一 SafeSPI 主题在 Hardware 层和 AUTOSAR 层应分别命名。
