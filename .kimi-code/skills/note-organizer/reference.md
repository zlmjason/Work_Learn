# Note Organizer — 详细用法

## 1. 工作流

```text
用户请求整理文件
    │
    ▼
1. 读取待整理文件（通常位于根目录或 00_Inbox_临时收集/）
    │
    ▼
2. 提取关键信息：标题、核心主题、涉及的技术栈层次
    │
    ▼
3. 对照 AGENTS.md 目录结构选择最合适的子目录
    │
    ▼
4. 按命名规则生成规范文件名
    │
    ▼
5. 执行 mv 移动文件
    │
    ▼
6. git status 确认
    │
    ▼
7. 向用户汇报新路径和命名依据
```

## 2. 目录与前缀映射表

| 主题层次 | 目标目录 | 命名前缀 | 示例 |
|----------|----------|----------|------|
| AURIX TC3xx 内核 | `01_Hardware_硬件层/01_Core/01_AURIX_TC3xx/` | `{MCU}_Core_` | `AURIX_TC3xx_Core_xxx.md` |
| ARM Cortex 内核 | `01_Hardware_硬件层/01_Core/02_ARM_Cortex/` | `ARM_{Core}_Core_` | `ARM_M7_Core_xxx.md` |
| 架构对比 | `01_Hardware_硬件层/01_Core/03_Comparison/` | `Core_Comparison_` | `Core_Comparison_xxx.md` |
| RAM / Flash / Cache / MPU | `01_Hardware_硬件层/02_Memory/` | `HW_Mem_` / `{MCU}_Mem_` | `HW_Mem_xxx.md` |
| Clock / Power / Reset / Bus / DMA / Interrupt | `01_Hardware_硬件层/03_System/` | `HW_Sys_` / `{MCU}_Sys_` | `HW_Sys_xxx.md` |
| Bootloader / BootROM / FOTA | `01_Hardware_硬件层/04_Boot/` | `HW_Boot_` | `HW_Boot_xxx.md` |
| 通讯外设 SPI/I2C/CAN/LIN/UART/Eth/FlexRay | `01_Hardware_硬件层/05_Peripherals/01_Communication/` | `HW_Periph_Comm_{协议}_` | `HW_Periph_Comm_CAN_xxx.md` |
| 定时器 GPT/PWM/ICU/WDG | `01_Hardware_硬件层/05_Peripherals/02_Timer/` | `HW_Periph_Timer_` | `HW_Periph_Timer_xxx.md` |
| IO GPIO/ADC/DAC | `01_Hardware_硬件层/05_Peripherals/03_IO/` | `HW_Periph_IO_` | `HW_Periph_IO_xxx.md` |
| 存储外设 | `01_Hardware_硬件层/05_Peripherals/04_Storage/` | `HW_Periph_Storage_` | `HW_Periph_Storage_xxx.md` |
| 多核 Lockstep/Resource/Intercore | `01_Hardware_硬件层/06_Multicore/` | `HW_MC_` / `{MCU}_MC_` | `HW_MC_xxx.md` |
| 调试 CoreSight/Trace/JTAG | `01_Hardware_硬件层/07_Debug/` | `HW_Debug_` | `HW_Debug_xxx.md` |
| 封装制造 | `01_Hardware_硬件层/08_Packaging/` | `HW_Packaging_` | `HW_Packaging_xxx.md` |
| AUTOSAR 通讯栈 | `02_Middleware_中间件层/01_AUTOSAR/01_Communication/` | `AUTOSAR_Comm_{协议}_` | `AUTOSAR_Comm_CAN_xxx.md` |
| AUTOSAR Memory | `02_Middleware_中间件层/01_AUTOSAR/02_Memory/` | `AUTOSAR_Mem_` | `AUTOSAR_Mem_xxx.md` |
| AUTOSAR IO | `02_Middleware_中间件层/01_AUTOSAR/03_IO/` | `AUTOSAR_IO_` | `AUTOSAR_IO_xxx.md` |
| AUTOSAR Timer | `02_Middleware_中间件层/01_AUTOSAR/04_Timer/` | `AUTOSAR_Timer_` | `AUTOSAR_Timer_xxx.md` |
| AUTOSAR Storage | `02_Middleware_中间件层/01_AUTOSAR/05_Storage/` | `AUTOSAR_Storage_` | `AUTOSAR_Storage_xxx.md` |
| AUTOSAR Diagnostics | `02_Middleware_中间件层/01_AUTOSAR/06_Diagnostics/` | `AUTOSAR_Diag_` | `AUTOSAR_Diag_xxx.md` |
| AUTOSAR System | `02_Middleware_中间件层/01_AUTOSAR/07_System/` | `AUTOSAR_Sys_` | `AUTOSAR_Sys_xxx.md` |
| AUTOSAR Safety | `02_Middleware_中间件层/01_AUTOSAR/08_Safety/` | `AUTOSAR_Safety_` | `AUTOSAR_Safety_xxx.md` |
| AUTOSAR MCU | `02_Middleware_中间件层/01_AUTOSAR/09_MCU/` | `AUTOSAR_MCU_` | `AUTOSAR_MCU_xxx.md` |
| FreeRTOS Kernel | `02_Middleware_中间件层/02_FreeRTOS/01_Kernel/` | `FreeRTOS_Kernel_` | `FreeRTOS_Kernel_xxx.md` |
| FreeRTOS Sync | `02_Middleware_中间件层/02_FreeRTOS/02_Synchronization/` | `FreeRTOS_Sync_` | `FreeRTOS_Sync_xxx.md` |
| FreeRTOS Memory | `02_Middleware_中间件层/02_FreeRTOS/03_Memory/` | `FreeRTOS_Mem_` | `FreeRTOS_Mem_xxx.md` |
| FreeRTOS Timing | `02_Middleware_中间件层/02_FreeRTOS/04_Timing/` | `FreeRTOS_Timing_` | `FreeRTOS_Timing_xxx.md` |
| FreeRTOS Port | `02_Middleware_中间件层/02_FreeRTOS/05_Port/` | `FreeRTOS_Port_` | `FreeRTOS_Port_xxx.md` |
| 功能安全 | `04_Safety_功能安全/` | `Safety_` | `Safety_xxx.md` |
| 工具链 | `05_Tools_工具链/` | `Tools_` | `Tools_xxx.md` |
| AI 工具链 / Agent | `91_Tools_AI工具链/` | 按子目录规则 | `Agent_xxx.md` / `Claude_xxx.md` 等 |
| 临时/未分类 | `00_Inbox_临时收集/` | 无固定前缀 | 保留原文件名或加日期前缀 |

## 3. 命名规则

1. **禁止空格**：用下划线 `_` 分隔。
2. **英文缩写大写**：`SPI`、`CAN`、`ADC`、`GPIO`、`MCU`、`IPC`、`CRC` 等。
3. **体现层次归属**：同一主题跨层次时文件名必须能区分，例如：
   - 硬件 SPI：`HW_Periph_Comm_SPI_xxx.md`
   - AUTOSAR SPI：`AUTOSAR_Comm_SPI_xxx.md`
4. **删除无意义后缀**：原文件名中的 `车规MCU视角_WhyWhatHow总结` 等可简化为更规范的主题词。
5. **保留版本/增强标识**：如果文件是增强版且与原文件共存，可在末尾加 `_IPC`、`_v2` 等后缀。

## 4. 决策示例

### 示例 1：ARM 与 AURIX 原子操作对比

- 原文件：`ARM与AURIX原子操作机制_车规MCU视角_WhyWhatHow总结.md`
- 主题：ARM Cortex-M7 vs AURIX TriCore 原子指令对比
- 层次：`01_Hardware_硬件层/01_Core/03_Comparison/`
- 前缀：`Core_Comparison_`
- 新文件名：`Core_Comparison_ARM_vs_AURIX_Atomic_Operations.md`

### 示例 2：增强 IPC 版

- 原文件：`ARM与AURIX原子操作机制_车规MCU视角_WhyWhatHow总结_增强IPC版.md`
- 主题：原子操作 + IPC 应用
- 层次：`01_Hardware_硬件层/01_Core/03_Comparison/`
- 前缀：`Core_Comparison_`
- 新文件名：`Core_Comparison_ARM_vs_AURIX_Atomic_and_IPC.md`

### 示例 3：AURIX SPI 规格

- 原文件：`aurix spi spec.md`
- 主题：AURIX SPI 外设
- 层次：`01_Hardware_硬件层/05_Peripherals/01_Communication/01_SPI/`
- 前缀：`HW_Periph_Comm_SPI_`
- 新文件名：`HW_Periph_Comm_SPI_AURIX_Specification.md`

## 5. 执行命令

```bash
mv "原文件名.md" "目标目录/规范文件名.md"
git status --short
```

## 6. 特殊情况处理

| 情况 | 处理 |
|------|------|
| 目标目录不存在 | 不要自动新建，先询问用户是否创建 |
| 目标位置已有同名文件 | 询问用户：覆盖 / 重命名 / 合并 |
| 文件内容跨多个层次 | 选择最核心主题对应的目录；如需拆分，建议用户 |
| 附件/图片 | 移动到 `99_Attachments_附件/` 对应子目录 |
| 临时草稿 | 保留在 `00_Inbox_临时收集/` |
