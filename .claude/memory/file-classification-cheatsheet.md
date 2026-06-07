---
name: file-classification-cheatsheet
description: 工作区文件分类速查表——文件名前缀与目标目录的映射关系，用于确保新文件和整理操作归类正确
metadata:
  type: project
---

# 文件分类速查表

> 本速查表对应 `f:\Learn\MarkDown_Learn` 工作区的目录结构。
> **规则**：文件名前缀决定目标目录；跨层次同名主题必须严格区分前缀。

---

## 01_Hardware_硬件层

### 01_Core — 内核架构

| 文件名前缀 | 目标目录 |
|-----------|---------|
| `AURIX_TC3xx_Core_` | `01_Hardware_硬件层/01_Core/01_AURIX_TC3xx/` |
| `ARM_M7_Core_` / `ARM_R52_Core_` | `01_Hardware_硬件层/01_Core/02_ARM_Cortex/` |
| `Core_Comparison_` | `01_Hardware_硬件层/01_Core/03_Comparison/` |

### 02_Memory — 存储子系统

| 文件名前缀 | 目标目录 |
|-----------|---------|
| `HW_Mem_` / `{MCU}_Mem_` | `01_Hardware_硬件层/02_Memory/01_RAM/` |
| `HW_Mem_` / `{MCU}_Mem_Flash_` | `01_Hardware_硬件层/02_Memory/02_Flash/` |
| `HW_Mem_` / `{MCU}_Mem_Cache_` | `01_Hardware_硬件层/02_Memory/03_Cache/` |
| `HW_Mem_` / `{MCU}_Mem_MPU_` | `01_Hardware_硬件层/02_Memory/04_MPU/` |

### 03_System — 系统级模块

| 文件名前缀 | 目标目录 |
|-----------|---------|
| `HW_Sys_Clock_` / `{MCU}_Sys_Clock_` | `01_Hardware_硬件层/03_System/01_Clock/` |
| `HW_Sys_Power_` / `{MCU}_Sys_Power_` | `01_Hardware_硬件层/03_System/02_Power/` |
| `HW_Sys_Reset_` / `{MCU}_Sys_Reset_` | `01_Hardware_硬件层/03_System/03_Reset/` |
| `HW_Sys_Bus_` / `{MCU}_Sys_Bus_` | `01_Hardware_硬件层/03_System/04_Bus/` |
| `HW_Sys_DMA_` / `{MCU}_Sys_DMA_` | `01_Hardware_硬件层/03_System/05_DMAMove/` |
| `HW_Sys_Interrupt_` / `{MCU}_Sys_Interrupt_` | `01_Hardware_硬件层/03_System/06_Interrupt/` |

> 注：`AURIX_TC3xx_Sys_Bus_Overview.md` → `04_Bus/`，`AURIX_TC3xx_Sys_SCU_Software_Reset_Summary.md` → `03_Reset/`

### 04_Boot — 启动流程

| 文件名前缀 | 目标目录 |
|-----------|---------|
| `HW_Boot_Bootloader_` | `01_Hardware_硬件层/04_Boot/01_Bootloader/` |
| `HW_Boot_BootROM_` | `01_Hardware_硬件层/04_Boot/02_BootROM/` |
| `HW_Boot_FirmwareUpdate_` | `01_Hardware_硬件层/04_Boot/03_Firmware_Update/` |

### 05_Peripherals — 外设（按功能分类）

#### 01_Communication — 通讯外设

| 文件名前缀 | 目标目录 |
|-----------|---------|
| `HW_Periph_Comm_SPI_` | `01_Hardware_硬件层/05_Peripherals/01_Communication/01_SPI/` |
| `HW_Periph_Comm_I2C_` | `01_Hardware_硬件层/05_Peripherals/01_Communication/02_I2C_IIC/` |
| `HW_Periph_Comm_CAN_` | `01_Hardware_硬件层/05_Peripherals/01_Communication/03_CAN_CANFD/` |
| `HW_Periph_Comm_LIN_` | `01_Hardware_硬件层/05_Peripherals/01_Communication/04_LIN/` |
| `HW_Periph_Comm_UART_` | `01_Hardware_硬件层/05_Peripherals/01_Communication/05_UART_USART/` |
| `HW_Periph_Comm_Ethernet_` | `01_Hardware_硬件层/05_Peripherals/01_Communication/06_Ethernet/` |
| `HW_Periph_Comm_FlexRay_` | `01_Hardware_硬件层/05_Peripherals/01_Communication/07_FlexRay/` |
| `HW_Periph_Comm_Intercore_` | `01_Hardware_硬件层/05_Peripherals/01_Communication/08_Intercore/` |
| `HW_Periph_Comm_Protocol_` | `01_Hardware_硬件层/05_Peripherals/01_Communication/99_Protocol_协议分析/` |

#### 02_Timer — 定时器外设

| 文件名前缀 | 目标目录 |
|-----------|---------|
| `HW_Periph_Timer_GPT_` | `01_Hardware_硬件层/05_Peripherals/02_Timer/01_GPT/` |
| `HW_Periph_Timer_PWM_` | `01_Hardware_硬件层/05_Peripherals/02_Timer/02_PWM/` |
| `HW_Periph_Timer_ICU_` | `01_Hardware_硬件层/05_Peripherals/02_Timer/03_ICU/` |
| `HW_Periph_Timer_WDG_` | `01_Hardware_硬件层/05_Peripherals/02_Timer/04_WDG_Watchdog/` |

#### 03_IO — IO 外设

| 文件名前缀 | 目标目录 |
|-----------|---------|
| `HW_Periph_IO_GPIO_` | `01_Hardware_硬件层/05_Peripherals/03_IO/01_GPIO_DIO/` |
| `HW_Periph_IO_ADC_` | `01_Hardware_硬件层/05_Peripherals/03_IO/02_ADC/` |
| `HW_Periph_IO_DAC_` | `01_Hardware_硬件层/05_Peripherals/03_IO/03_DAC/` |

#### 04_Storage — 存储外设

| 文件名前缀 | 目标目录 |
|-----------|---------|
| `HW_Periph_Storage_Flash_` | `01_Hardware_硬件层/05_Peripherals/04_Storage/01_Internal_Flash/` |
| `HW_Periph_Storage_EEPROM_` | `01_Hardware_硬件层/05_Peripherals/04_Storage/02_EEPROM_Emulation/` |
| `HW_Periph_Storage_FEE_` | `01_Hardware_硬件层/05_Peripherals/04_Storage/03_Fee_Flash_Emul/` |

### 06_Multicore — 多核系统

| 文件名前缀 | 目标目录 |
|-----------|---------|
| `HW_MC_Lockstep_` / `{MCU}_MC_Lockstep_` | `01_Hardware_硬件层/06_Multicore/01_Lockstep/` |
| `HW_MC_Resource_` / `{MCU}_MC_Resource_` | `01_Hardware_硬件层/06_Multicore/02_Resource_Sharing/` |
| `HW_MC_Intercore_` / `{MCU}_MC_Intercore_` | `01_Hardware_硬件层/06_Multicore/03_Intercore_Comm/` |

### 07_Debug — 调试子系统

| 文件名前缀 | 目标目录 |
|-----------|---------|
| `HW_Debug_CoreSight_` | `01_Hardware_硬件层/07_Debug/01_CoreSight/` |
| `HW_Debug_Trace_` | `01_Hardware_硬件层/07_Debug/02_Trace/` |
| `HW_Debug_JTAG_` | `01_Hardware_硬件层/07_Debug/03_JTAG_DAP/` |
| `HW_Debug_CrossTrigger_` | `01_Hardware_硬件层/07_Debug/04_CrossTrigger/` |

### 08_Packaging — 制造与封装

| 文件名前缀 | 目标目录 |
|-----------|---------|
| `HW_Packaging_` | `01_Hardware_硬件层/08_Packaging/` |

---

## 02_Middleware_中间件层

### 01_AUTOSAR — AUTOSAR MCAL / BSW

#### 01_Communication — 通讯栈

| 文件名前缀 | 目标目录 |
|-----------|---------|
| `AUTOSAR_Comm_CAN_` | `02_Middleware_中间件层/01_AUTOSAR/01_Communication/01_CAN_CANFD/` |
| `AUTOSAR_Comm_LIN_` | `02_Middleware_中间件层/01_AUTOSAR/01_Communication/02_LIN/` |
| `AUTOSAR_Comm_SPI_` | `02_Middleware_中间件层/01_AUTOSAR/01_Communication/03_SPI/` |
| `AUTOSAR_Comm_Ethernet_` | `02_Middleware_中间件层/01_AUTOSAR/01_Communication/04_Ethernet/` |
| `AUTOSAR_Comm_FlexRay_` | `02_Middleware_中间件层/01_AUTOSAR/01_Communication/05_FlexRay/` |
| `AUTOSAR_Comm_UDS_` | `02_Middleware_中间件层/01_AUTOSAR/01_Communication/06_UDS_诊断通信/` |
| `AUTOSAR_Comm_XCP_` | `02_Middleware_中间件层/01_AUTOSAR/01_Communication/07_XCP_CCP/` |

#### 02_Memory — 内存驱动

| 文件名前缀 | 目标目录 |
|-----------|---------|
| `AUTOSAR_Mem_FlashDriver_` | `02_Middleware_中间件层/01_AUTOSAR/02_Memory/01_Flash_Driver/` |
| `AUTOSAR_Mem_EEPROM_` | `02_Middleware_中间件层/01_AUTOSAR/02_Memory/02_EEPROM/` |
| `AUTOSAR_Mem_NVRAM_` | `02_Middleware_中间件层/01_AUTOSAR/02_Memory/03_NVRAM/` |

#### 03_IO — IO 驱动

| 文件名前缀 | 目标目录 |
|-----------|---------|
| `AUTOSAR_IO_DIO_` | `02_Middleware_中间件层/01_AUTOSAR/03_IO/01_DIO/` |
| `AUTOSAR_IO_ADC_` | `02_Middleware_中间件层/01_AUTOSAR/03_IO/02_ADC/` |
| `AUTOSAR_IO_PWM_` | `02_Middleware_中间件层/01_AUTOSAR/03_IO/03_PWM/` |
| `AUTOSAR_IO_ICU_` | `02_Middleware_中间件层/01_AUTOSAR/03_IO/04_ICU/` |

#### 04_Timer — 定时器驱动

| 文件名前缀 | 目标目录 |
|-----------|---------|
| `AUTOSAR_Timer_GPT_` | `02_Middleware_中间件层/01_AUTOSAR/04_Timer/01_GPT/` |
| `AUTOSAR_Timer_WDG_` | `02_Middleware_中间件层/01_AUTOSAR/04_Timer/02_WDG/` |

#### 05_Storage — 存储服务

| 文件名前缀 | 目标目录 |
|-----------|---------|
| `AUTOSAR_Storage_Fee_` | `02_Middleware_中间件层/01_AUTOSAR/05_Storage/01_Fee/` |
| `AUTOSAR_Storage_Ea_` | `02_Middleware_中间件层/01_AUTOSAR/05_Storage/02_Ea/` |
| `AUTOSAR_Storage_NvM_` | `02_Middleware_中间件层/01_AUTOSAR/05_Storage/03_NvM/` |

#### 06_Diagnostics — 诊断栈

| 文件名前缀 | 目标目录 |
|-----------|---------|
| `AUTOSAR_Diag_DEM_` | `02_Middleware_中间件层/01_AUTOSAR/06_Diagnostics/01_DEM/` |
| `AUTOSAR_Diag_DET_` | `02_Middleware_中间件层/01_AUTOSAR/06_Diagnostics/02_DET/` |
| `AUTOSAR_Diag_UDS_` | `02_Middleware_中间件层/01_AUTOSAR/06_Diagnostics/03_UDS_Services/` |
| `AUTOSAR_Diag_DTC_` | `02_Middleware_中间件层/01_AUTOSAR/06_Diagnostics/04_DTC/` |
| `AUTOSAR_Diag_OBD_` | `02_Middleware_中间件层/01_AUTOSAR/06_Diagnostics/05_OBD/` |

#### 07_System — 系统服务

| 文件名前缀 | 目标目录 |
|-----------|---------|
| `AUTOSAR_Sys_OS_` | `02_Middleware_中间件层/01_AUTOSAR/07_System/01_OS/` |
| `AUTOSAR_Sys_EcuM_` | `02_Middleware_中间件层/01_AUTOSAR/07_System/02_EcuM/` |
| `AUTOSAR_Sys_BswM_` | `02_Middleware_中间件层/01_AUTOSAR/07_System/03_BswM/` |
| `AUTOSAR_Sys_SchM_` | `02_Middleware_中间件层/01_AUTOSAR/07_System/04_SchM/` |
| `AUTOSAR_Sys_ComM_` | `02_Middleware_中间件层/01_AUTOSAR/07_System/05_ComM/` |
| `AUTOSAR_Sys_Nm_` | `02_Middleware_中间件层/01_AUTOSAR/07_System/06_Nm/` |

#### 08_Safety — 功能安全

| 文件名前缀 | 目标目录 |
|-----------|---------|
| `AUTOSAR_Safety_E2E_` | `02_Middleware_中间件层/01_AUTOSAR/08_Safety/01_E2E/` |
| `AUTOSAR_Safety_WDG_` | `02_Middleware_中间件层/01_AUTOSAR/08_Safety/02_WDG_Safety/` |
| `AUTOSAR_Safety_SafeSPI_` | `02_Middleware_中间件层/01_AUTOSAR/08_Safety/03_SafeSPI/` |
| `AUTOSAR_Safety_SafeT_` | `02_Middleware_中间件层/01_AUTOSAR/08_Safety/04_SafeT/` |
| `AUTOSAR_Safety_Testing_` | `02_Middleware_中间件层/01_AUTOSAR/08_Safety/05_Testing/` |

#### 09_MCU — MCU 驱动

| 文件名前缀 | 目标目录 |
|-----------|---------|
| `AUTOSAR_MCU_Driver_` | `02_Middleware_中间件层/01_AUTOSAR/09_MCU/01_MCU_Driver/` |
| `AUTOSAR_MCU_Port_` | `02_Middleware_中间件层/01_AUTOSAR/09_MCU/02_Port_Driver/` |
| `AUTOSAR_MCU_GPT_` | `02_Middleware_中间件层/01_AUTOSAR/09_MCU/03_GPT_Driver/` |

### 02_FreeRTOS — FreeRTOS 实时内核

#### 01_Kernel — 内核核心

| 文件名前缀 | 目标目录 |
|-----------|---------|
| `FreeRTOS_Kernel_Tasks_` | `02_Middleware_中间件层/02_FreeRTOS/01_Kernel/01_Tasks/` |
| `FreeRTOS_Kernel_Scheduler_` | `02_Middleware_中间件层/02_FreeRTOS/01_Kernel/02_Scheduler/` |
| `FreeRTOS_Kernel_Lists_` | `02_Middleware_中间件层/02_FreeRTOS/01_Kernel/03_Lists/` |
| `FreeRTOS_Kernel_Queues_` | `02_Middleware_中间件层/02_FreeRTOS/01_Kernel/04_Queues/` |

#### 02_Synchronization — 同步机制

| 文件名前缀 | 目标目录 |
|-----------|---------|
| `FreeRTOS_Sync_Semaphores_` | `02_Middleware_中间件层/02_FreeRTOS/02_Synchronization/01_Semaphores/` |
| `FreeRTOS_Sync_Mutexes_` | `02_Middleware_中间件层/02_FreeRTOS/02_Synchronization/02_Mutexes/` |
| `FreeRTOS_Sync_EventGroups_` | `02_Middleware_中间件层/02_FreeRTOS/02_Synchronization/03_EventGroups/` |
| `FreeRTOS_Sync_StreamBuffers_` | `02_Middleware_中间件层/02_FreeRTOS/02_Synchronization/04_StreamBuffers/` |

#### 03_Memory — 内存管理

| 文件名前缀 | 目标目录 |
|-----------|---------|
| `FreeRTOS_Mem_Heap_` | `02_Middleware_中间件层/02_FreeRTOS/03_Memory/01_Heap/` |
| `FreeRTOS_Mem_Stack_` | `02_Middleware_中间件层/02_FreeRTOS/03_Memory/02_Stack/` |
| `FreeRTOS_Mem_MPU_` | `02_Middleware_中间件层/02_FreeRTOS/03_Memory/03_MPU/` |

#### 04_Timing — 时序管理

| 文件名前缀 | 目标目录 |
|-----------|---------|
| `FreeRTOS_Timing_Tick_` | `02_Middleware_中间件层/02_FreeRTOS/04_Timing/01_Tick/` |
| `FreeRTOS_Timing_SoftwareTimers_` | `02_Middleware_中间件层/02_FreeRTOS/04_Timing/02_SoftwareTimers/` |
| `FreeRTOS_Timing_Delays_` | `02_Middleware_中间件层/02_FreeRTOS/04_Timing/03_Delays/` |

#### 05_Port — 移植层

| 文件名前缀 | 目标目录 |
|-----------|---------|
| `FreeRTOS_Port_PortLayer_` | `02_Middleware_中间件层/02_FreeRTOS/05_Port/01_PortLayer/` |
| `FreeRTOS_Port_Interrupts_` | `02_Middleware_中间件层/02_FreeRTOS/05_Port/02_Interrupts/` |
| `FreeRTOS_Port_Hooks_` | `02_Middleware_中间件层/02_FreeRTOS/05_Port/03_Hooks/` |

---

## 其他层次

| 文件名前缀 | 目标目录 |
|-----------|---------|
| `Safety_` | `04_Safety_功能安全/` → `01_ISO26262`/`02_E2E`/`03_SafetyMonitor`/`04_Lockstep` |
| `Tools_` | `05_Tools_工具链/` → `01_Compiler`/`02_Debugger`/`03_Flash`/`04_Trace`/`05_HIL_SIL` |

---

## 高风险易错场景

### 1. 同名主题跨层次

| 主题 | Hardware 层文件名 | AUTOSAR 层文件名 |
|------|------------------|-----------------|
| SafeSPI | `HW_Periph_Comm_SafeSPI_...` | `AUTOSAR_Safety_SafeSPI_...` |
| E2E | `HW_MC_` / `HW_Debug_`（不涉及） | `AUTOSAR_Safety_E2E_...` |
| Flash | `HW_Mem_Flash_...` / `HW_Periph_Storage_Flash_...` | `AUTOSAR_Mem_FlashDriver_...` / `AUTOSAR_Storage_Fee_...` |
| WDG | `HW_Periph_Timer_WDG_...` | `AUTOSAR_Timer_WDG_...` / `AUTOSAR_Safety_WDG_...` |

**原则**：看文件名前缀，不是看标题。

### 2. System 子目录混淆

文件内容核心主题决定归属：
- 讲时钟树、PLL、OSC → `01_Clock`
- 讲低功耗、电源管理 → `02_Power`
- 讲复位源、复位序列 → `03_Reset`
- 讲总线拓扑、仲裁 → `04_Bus`
- 讲 DMA 控制器、通道配置 → `05_DMAMove`
- 讲中断路由、优先级、嵌套 → `06_Interrupt`

### 3. 命名不规范的新文件

如果用户给的文件名没有遵循前缀规则，我应该：
1. 先按内容判断归属
2. 建议重命名（或自动重命名）为规范前缀
3. 再移动到目标目录

---

## 更新记录

| 日期 | 更新内容 |
|------|---------|
| 2026-06-05 | 初始版本：基于 CLAUDE.md 目录规范和文件命名规则建立完整映射表 |
