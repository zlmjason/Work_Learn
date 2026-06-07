# Automotive MCU Overview — 车规级 MCU 通用架构

车规级 MCU（Microcontroller Unit）是汽车电子控制系统的核心计算单元，相比消费级/工业级 MCU，在可靠性、功能安全、工作温度范围、EMC 等方面有严格的要求。

## 主流车规 MCU 厂商与产品系列

| 厂商 | 系列 | 核心 | 典型应用 | 安全等级 |
|------|------|------|---------|---------|
| Infineon | AURIX TC2xx/TC3xx/TC4xx | TriCore (1.6/1.6.2/1.8) | 动力域、底盘域、ADAS | ASIL-D |
| NXP | S32K1xx/S32K3xx/S32G | Cortex-M4/M7/M33, Cortex-A53 | 车身域、网关、区域控制器 | ASIL-D |
| Renesas | RH850/F1x/F1L/U2A | RH850 G3K/G3M/G3H | 车身域、动力域、底盘域 | ASIL-D |
| Renesas | RA6T2/RA8 | Cortex-M33/M85 | 电机控制、通用车身 | ASIL-B/D |
| Texas Instruments | TMS570/RM4x | Cortex-R4F/R5F | 功能安全关键应用 | ASIL-D |
| STMicroelectronics | Stellar SR6 | Cortex-M7 + Cortex-R52 | 动力域、底盘域、域控制器 | ASIL-D |
| STMicroelectronics | SPC5 | Power Architecture e200z | 动力域、车身域 | ASIL-D |

## 车规 MCU 核心特征

### 1. 工作温度范围
- **Grade 0**: -40°C ~ +150°C（发动机舱、变速箱）
- **Grade 1**: -40°C ~ +125°C（驾驶舱、底盘）
- **Grade 2**: -40°C ~ +105°C（信息娱乐）

### 2. 功能安全支持
- 双核锁步（Lockstep）：两个核心同步执行，输出比较
- ECC（Error Correcting Code）：SRAM/Flash/Cache 的纠错
- BIST（Built-In Self Test）：上电/运行时的自检
- 时钟监控：PLL 失锁检测、时钟完整性检查
- 电源监控：POR（Power-On Reset）、BOR（Brown-Out Reset）
- MPU（Memory Protection Unit）：内存访问权限控制
- 看门狗：独立看门狗（IWDG）、窗口看门狗（WWDG）

### 3. 存储架构
| 类型 | 用途 | 特性 |
|------|------|------|
| Flash (NVM) | 程序代码、标定数据 | 100K 擦写周期，10年数据保持 |
| SRAM | 运行时数据、栈、堆 | 带 ECC，可分区 |
| TCM (Tightly Coupled Memory) | 实时关键代码/数据 | 确定性的单周期访问 |
| Cache | 指令/数据缓存 | 可配置为 SRAM 或 Cache |
| OTP (One-Time Programmable) | 芯片唯一标识、安全密钥 | 仅写一次 |
| Emulated EEPROM | 小容量非易失数据 | 通过 Flash 模拟 |

### 4. 电源管理
- 多电源域：核心域、外设域、I/O 域可独立开关
- 低功耗模式：Run / Sleep / Deep-Sleep / Standby
- 唤醒源：GPIO、RTC、CAN/LIN 报文、外部中断
- 电源序列：上电时序严格控制，避免 latch-up

### 5. 通信外设
- **CAN/CAN FD**: 车身网络主干，速率 125Kbps ~ 8Mbps
- **LIN**: 车门、座椅、灯光等低成本节点，19.2Kbps
- **FlexRay**: 底盘线控制动/转向，10Mbps，确定性时隙
- **Ethernet**: ADAS/网关/OTA，100Mbps/1Gbps + TSN
- **SPI**: 板级高速通信，传感器/执行器
- **I2C**: 低速板级通信，EEPROM/传感器
- **UART**: 调试、诊断、标定

## 测试验证核心关注点

### 硅前验证（Pre-Silicon）
- RTL 仿真：功能覆盖率、代码覆盖率
- UVM 验证平台：外设级、子系统级、SoC 级
- 形式验证：关键安全属性的数学证明
- 功耗分析：动态/静态功耗、电源完整性

### 硅后验证（Post-Silicon）
- 功能验证：所有外设寄存器读写、中断/DMA 功能
- 性能验证：主频、Flash 等待周期、Cache 命中率
- 功耗验证：各模式电流、唤醒时间
- 温度验证：高低温箱下的功能正确性
- EMC 验证：辐射发射、传导发射、抗扰度
- 可靠性验证：HTOL、ESD、Latch-up

### 软件分层测试
| 层级 | 内容 | 目标 |
|------|------|------|
| LL (Low Level) | 寄存器访问、时钟配置、中断使能 | 验证硬件接口正确性 |
| IM (Interface/Module) | 外设驱动抽象、回调机制 | 验证模块功能完整性 |
| TestCase | 应用级测试场景 | 验证用户需求满足度 |

## 常见陷阱

1. **Flash 等待周期**：主频提升后必须增加 Flash 等待周期，否则取指令出错
2. **时钟切换**：切换时钟源时必须等待新时钟稳定，否则死锁
3. **DMA 缓存一致性**：DMA 访问 SRAM 时，CPU Cache 可能不一致，需手动 invalidate/flush
4. **中断优先级反转**：低优先级中断持有资源，高优先级中断无法执行
5. **看门狗喂狗时机**：在初始化完成前喂狗，导致系统复位循环
6. **低功耗唤醒**：唤醒后未重新初始化时钟/外设，导致功能异常
