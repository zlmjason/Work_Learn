# SafeSPI 来源、背景与 MCU SPI 支持性分析

> 目标：梳理 SafeSPI 的 **Why / What / How**，并基于 **13K** MCU SPI 规格书（V1.8）逐项评估 SafeSPI 机制的可实现性。电气参数待 13K Pad Datasheet 补充验证。

---

## 0. 核心结论

**SafeSPI 不是 AUTOSAR SPI，也不是普通 SPI 的简单别名。**

更准确的定位是：

> **SafeSPI 是一个面向汽车安全应用的 over-SPI 协议/接口规范。它基于传统 SPI 四线物理接口，但进一步约束电气时序、帧格式、寻址、CRC、故障管理和 Monitor/Listener 监听方式。**

基于当前 MCU SPI 规格书（V1.8）的逐项分析结论：

| 层级 | 支持性 | 说明 |
|---|---|:---|
| **物理层 / IO 电气层** | ⚠️ **待验证** | 该 MCU SPI 控制器接口时钟可达 50 MHz，理论上有支持 10 MHz SafeSPI 的时钟能力。但 VIO、VIH/VIL、VOH/VOL、MISO 三态、输入电容、漏电流、驱动强度、slew rate 等**必须结合 MCU Pad Datasheet 确认**。软件无法补救电气参数不达标问题。 |
| **SPI 传输层** | ✅ **Master 可实现** | CPOL=0/1、CPHA=0/1、MSB/LSB 均可配置；32 bit 帧直接支持；48 bit 帧可通过**连续帧模式（SCONF.LAST=0）**拼接实现，需验证 CS 保持期间无额外 SCONF 开销插入总线；CS 延迟（LEAD/TRAIL/IDLE）可配；DMA 和中断支持完备。 |
| **SPI 传输层** | ⚠️ **Slave 条件可实现** | Slave 模式支持 4 种 {CPOL,CPHA} 组合；TX FIFO 预装载支持 out-of-frame。**但 Slave in-frame 响应对 MISO valid / disable lag 有 ns 级要求，当前规格书未给出 Slave 输出时序参数，需 Silicon 验证。** MISO 在 CS 高电平时的三态行为未明确描述。 |
| **SafeSPI 逻辑层** | ✅ **Master 端软件可实现；Slave 端条件实现** | 32/48 bit frame 打包/解析、CRC、TA/SA 地址、D 位、error indication / fault management、out-of-frame pipeline 均属于 SafeSPI 协议语义，不是普通 SPI IP 原生硬件功能。作为 Master 可由软件协议层实现；作为 Slave 则还受 MISO high-Z、响应预装载和输出时序约束。 |
| **Monitor / Listener 模式** | ❌ **不支持** | 该 SPI IP 无专用 passive sniff / monitor 模式，无法同时以外部 SCK 采样 MOSI+MISO 并做 frame reconstruction。 |
| **硬件安全机制** | ⚠️ **部分支持** | 有奇偶校验（仅 Slave 模式）、波特率错误检测、看门狗、TX/RX FIFO 溢出欠载检测。**但无硬件 CRC、无硬件地址过滤/比较。** |

**推荐判断口径：**

```text
该 MCU 作为 SafeSPI Master：
    可实现，但 48-bit 帧需通过连续帧模式拼接，需验证总线波形无间隙。
    CRC、TA/SA 地址管理、D 位解析、CRC3/CRC8、error indication / fault management 由软件协议层实现。

该 MCU 作为 SafeSPI Slave：
    out-of-frame 可评估，前提是确认 MISO 三态时序和 CS deassert 后输出关闭延迟。
    in-frame 不建议，ns 级响应时间对软件不友好，且缺少 Slave 输出时序 characterization。

该 MCU 作为 SafeSPI Monitor / Listener：
    不可实现，需要额外硬件（FPGA/Safety ASIC/专用 Monitor IP）。
```

---

## 1. SafeSPI 的来源与背景

### 1.1 文档来源

SafeSPI 技术规范：

```text
SafeSPI - Serial Peripheral Interface for Automotive Safety
Technical Specification
SafeSPI_Draft.docx
Rev 2.0
26 March 2021
```

文档结构：

```text
1 Introduction
2 Overview about SPI communication
3 Physical Layer Specification
  3.1 Voltage levels and capacitances
  3.2 Timing specifications
4 Logical Layer
  4.1 General layer description
  4.2 Logical layer implementation variants
  4.3 32Bit Frame
  4.4 48Bit Frame
  4.5 48Bit and 32Bit support in same Slave
  4.6 Example for target/source address
5 Change history
```

这说明 SafeSPI 同时约束：SPI 电气/时序、帧结构、32/48 bit 数据格式、CRC、fault management、master/slave/monitor 行为。

### 1.2 为什么需要 SafeSPI？

普通 SPI 的“不标准化”问题：

| 问题 | 说明 |
|---|---|
| 协议选项太多 | CPOL/CPHA、bit order、CS 行为、帧长、dummy cycle 都可能不同 |
| 每个器件私有协议 | 传感器、SBC、ASIC、EEPROM、Watchdog 都可能定义自己的帧格式 |
| 软件适配成本高 | 每接一个器件，就要写一套私有解析逻辑 |
| 安全监控困难 | 独立 safety monitor 不可能理解所有私有 SPI 协议 |
| 互操作性差 | 不同供应商器件之间难以形成标准接口生态 |

在汽车安全应用里，常见架构：

```text
                          ┌──────────────────────┐
                          │ Safing / Monitor ASIC │
                          │ 只监听，不驱动总线      │
                          └──────────┬───────────┘
                                     │
MCU Master ───── CS/SCK/MOSI/MISO ─┼──── Sensor / Interface ASIC
                                     │
                                     └──── Other Slave
```

SafeSPI 的出现是为了：
- 标准化安全传感器接口；
- 让独立 safety monitor 能硬件解析 SPI 数据；
- 降低供应链适配成本。

---

## 2. WHY：SafeSPI 解决什么问题？

### 2.1 协议标准化

普通 SPI 没统一定义：帧长、地址位、数据位、CRC、response 方式、多 slave 寻址、fault 编码、monitor 识别方式等。SafeSPI 通过标准化逻辑层解决。

### 2.2 功能安全与独立监控

在 airbag、碰撞检测、惯性传感器、底盘安全等场景中，独立 safing device 需要：
- 当 MCU 软件失效时，仍能独立看到传感器数据；
- 当 SPI 数据异常时，能进行独立判断；
- 避免安全决策完全依赖 MCU 软件链路。

### 2.3 供应链互操作

- 支持标准化安全传感器接口；
- 降低和外部 safety ASIC / sensor 的适配成本；
- 有利于客户做平台化。

---

## 3. WHAT：SafeSPI 到底是什么？

### 3.1 分层理解

```text
┌─────────────────────────────────────────────┐
│ SafeSPI Logical Layer                        │
│ - 32-bit / 48-bit frame                      │
│ - in-frame / out-of-frame                    │
│ - TA/SA / data / status / D bit / CRC3/CRC8  │
│ - fault management                           │
├─────────────────────────────────────────────┤
│ SPI Transfer Constraint                      │
│ - CPOL / CPHA                                │
│ - MSB first                                  │
│ - CS behavior                                │
│ - SCK frequency and timing                   │
├─────────────────────────────────────────────┤
│ Physical / IO Layer                          │
│ - VIO 3.0~3.6 V                              │
│ - VIH / VIL / VOH / VOL                      │
│ - load capacitance                           │
│ - MISO high-Z / leakage / rise-fall time     │
└─────────────────────────────────────────────┘
```

### 3.2 SafeSPI 物理接口

标准 SPI 四线：

| 信号 | 方向 | 说明 |
|---|---|---|
| SCK | Master → Slave / Monitor | 主时钟 |
| CS | Master → Slave / Monitor | 片选，低有效 |
| MOSI | Master → Slave / Monitor | 主发从收 |
| MISO | Slave → Master / Monitor | 从发主收 |

### 3.3 物理层要求基线（待 MCU Datasheet 验证）

> **以下参数摘自 SafeSPI Rev 2.0 规范，需与 MCU Pad 电气特性表逐项核对。**

| 编号 | 参数 | SafeSPI 要求 | 当前 MCU 状态 |
|:---|:---|:---|:---|
| PHY-01 | VIO | **3.0 V ~ 3.6 V** | ❓ 待 Datasheet 确认 |
| PHY-02 | 器件输入/输出电容 | **≤ 10 pF** | ❓ 待 Datasheet 确认 |
| PHY-03 | 总线负载电容 (Wide) | **10 pF ~ 100 pF** | ❓ 板级设计决定 |
| PHY-04 | 总线负载电容 (Narrow) | **30 pF ~ 100 pF** | ❓ 板级设计决定 |
| PHY-05 | 输入低电平 VIL | **0 ~ 0.3 × VIO** | ❓ 待 Pad 参数确认 |
| PHY-06 | 输入高电平 VIH | **0.7 × VIO ~ VIO** | ❓ 待 Pad 参数确认 |
| PHY-07 | 输出低电平 VOL | **0 ~ 0.1 × VIO** | ❓ 待 Pad 参数确认 |
| PHY-08 | 输出高电平 VOH | **0.9 × VIO ~ VIO** | ❓ 待 Pad 参数确认 |
| PHY-09 | 输入迟滞 | **≥ 0.1 × VIO** | ❓ 待 Pad 参数确认 |
| PHY-10 | MISO high-Z 漏电流 | **-10 µA ~ +10 µA** | ❓ 待 Pad 参数确认 |
| PHY-11 | CS 上拉 | **60 kΩ ~ 140 kΩ** 或等效电流源 | ❓ 板级或 Pad 内置确认 |
| PHY-12 | MOSI/SCK/MISO 下拉 | **60 kΩ ~ 140 kΩ** 或等效电流源 | ❓ 板级或 Pad 内置确认 |

**关键结论：**

```text
如果 Pad 电气参数不满足 SafeSPI，软件基本无法真正补齐。
```

可补救手段（只能缓解，不能替代合规）：
- 降低 SPI baudrate；
- 配置 Pad drive strength；
- 配置 slew rate；
- 增加外部上下拉；
- 增加串阻；
- 优化 PCB 走线和负载；
- 外接 buffer/level shifter。

### 3.4 时序要求基线（待验证）

> SafeSPI Rev 2.0 的 timing 分为两类：一类是 **从 Master 视角对 Slave/Listener 的要求**，另一类是 **从 Slave 视角对 Master/Listener 的要求**。原文中只列了 A~F，容易漏掉 SCK 频率、SCK 高/低电平时间、sequential transfer delay 等 Master 侧要求。

**Slave / Listener 侧相关要求（Master 视角）：**

| 编号 | 参数 | 符号 | SafeSPI 要求 | 当前 MCU 状态 |
|:---|:---|:---|:---|:---|
| TIM-S01 | MISO data valid after CS↓ | A | **≤ 40 ns** | ❓ Slave 输出时序未给出 |
| TIM-S02 | MISO data valid after SCK edge | B | **≤ 32 ns** | ❓ Slave 输出时序未给出 |
| TIM-S03 | MOSI data hold time | C | **≥ 20 ns** | ❓ Master 输出时序需结合 Pad/波形确认 |
| TIM-S04 | MISO rise/fall time | D | **2 ns ~ 9 ns** | ❓ Pad slew rate / drive strength 待确认 |
| TIM-S05 | MISO disable lag (CS↑→high-Z) | E | **≤ 50 ns** | ❓ Slave 三态时序未给出 |
| TIM-S06 | MOSI data setup time | F | **≥ 10 ns** | ❓ Master 输出时序需结合 Pad/波形确认 |

**Master / Listener 侧相关要求（Slave 视角）：**

| 编号 | 参数 | SafeSPI 要求 | 当前 MCU 状态 |
|:---|:---|:---|:---|
| TIM-M01 | SCK operating frequency | **0.095 MHz ~ 10.5 MHz** | ✅ SPI 时钟上限高于 10.5 MHz，需配置到 SafeSPI 允许范围 |
| TIM-M02 | SCK disable lead time | **≥ 10 ns** | ❓ 需结合 CS/SCK 波形确认 |
| TIM-M03 | SCK enable lead time | **≥ 40 ns** | ❓ 可通过 CS lead 配置，但需波形确认 |
| TIM-M04 | SCK rise/fall time | **2 ns ~ 9 ns** | ❓ Pad slew rate 待确认 |
| TIM-M05 | SCK high time | **≥ 37 ns** | ⚠️ 10 MHz 下理论可满足，需确认占空比 |
| TIM-M06 | SCK low time | **≥ 37 ns** | ⚠️ 10 MHz 下理论可满足，需确认占空比 |
| TIM-M07 | SCK enable lag time | **≥ 20 ns** | ❓ 需波形确认 |
| TIM-M08 | SCK disable lag time | **≥ 10 ns** | ❓ 需波形确认 |
| TIM-M09 | Sequential transfer delay, out-of-frame write | **≥ 750 ns** | ❓ 需配置/实测连续帧间隔 |
| TIM-M10 | Sequential transfer delay, out-of-frame read | **≥ 450 ns** | ❓ 需配置/实测连续帧间隔 |
| TIM-M11 | Sequential transfer delay, in-frame | **≥ 200 ns** | ❓ 需配置/实测连续帧间隔 |
| TIM-M12 | MOSI rise/fall time | **2 ns ~ 9 ns** | ❓ Pad slew rate 待确认 |
| TIM-M13 | MISO data setup time | **≥ 5 ns** | ❓ Slave/Listener 采样关系需验证 |
| TIM-M14 | MISO data hold time | 稳定到下一个 SCK shift edge | ❓ Slave 输出与 Master 采样需验证 |
| TIM-M15 | MOSI valid time | **≤ 10 ns** | ❓ Master 输出时序需验证 |
| TIM-M16 | CS rise/fall time | **2 ns ~ 9 ns** | ❓ Pad slew rate 待确认 |

注意：这里的 **D** 是 timing 图中的 **MISO rise/fall time**，不是 SafeSPI 逻辑帧中的 **D bit**。

### 3.5 SPI Mode

| SafeSPI 语义 | SPI 配置 | 说明 |
|---|---|---|
| Out-of-frame | CPOL = 0, CPHA = 0 | response 在下一帧返回 |
| In-frame | CPOL = 0, CPHA = 1 | response 在当前帧返回 |

该 MCU SPI 支持：CPOL=0/1, CPHA=0/1（Master 通过 CHCTLi.SCKPOL/SCKPHASE 配置；Slave 支持 4 种组合）。

### 3.6 32-bit 与 48-bit Frame

| 帧类型 | 支持模式 | MCU 支持性 |
|---|---|:---|
| 32-bit frame | in-frame + out-of-frame | ✅ **直接支持**。SCONF.DATCNT 最大配置 31 对应 32 位，BYTE=0。 |
| 48-bit frame | out-of-frame only | ⚠️ **条件支持**。单帧最大 32 位，需通过**连续帧模式（SCONF.LAST=0）**拼接两帧（如 32+16）实现。需验证 CS 保持期间无 SCONF 重载字插入总线、无 SCK gap。 |

关键信息：
- 32-bit 变体支持 out-of-frame 和 in-frame；48-bit 变体**只定义 out-of-frame**；
- SafeSPI 帧内地址不是“16-bit target address / 8-bit source address”，而是 **TA9:0 / SA9:0**；32-bit in-frame 变体只使用 **TA9:5 / SA9:5**；
- D bit 是 **response frame format / sensor data indication**：D=1 表示 sensor data；D=0 表示 non-sensor data，例如 status data 或 configuration readback；
- 32-bit sensor data 最多 16 bit；48-bit sensor data 最多 20 bit；
- 32-bit 使用 **3-bit CRC**，48-bit 使用 **8-bit CRC**；CRC 计算覆盖范围随 frame format 不同，并不是“覆盖整个帧”。该 MCU 无 SafeSPI 专用硬件 CRC，需软件或通用 CRC 外设辅助实现。

### 3.7 In-frame 与 Out-of-frame

**In-frame：** Slave 在当前帧内返回响应。延迟低，但对 Slave 硬件要求高（MISO 需及时输出）。

**Out-of-frame：** Slave 在下一帧返回上一帧结果。延迟多一帧，但 Master/Slave 实现都更容易。

对该 MCU 而言：
- **Master out-of-frame**：✅ 完全可行，软件维护 pipeline 即可；
- **Slave out-of-frame**：⚠️ 可行，但需提前预装载 TX FIFO，且需验证 MISO 三态时序；
- **Slave in-frame**：⚠️ 高风险。规格书未给出 Slave 输出延迟 characterization，且 in-frame 要求 Slave 在第二个 SCK 沿前准备好数据，软件干预窗口极窄。

---

## 4. HOW：SafeSPI 如何工作？

### 4.1 通信架构

```text
                          ┌─────────────────────┐
                          │ Monitor / Safing ASIC│
                          │ CS/SCK/MOSI/MISO in │
                          └──────────┬──────────┘
                                     │
┌────────────┐      SCK/CS/MOSI/MISO│      ┌──────────────┐
│ MCU Master │──────────────────────┼─────►│ Sensor Slave │
└────────────┘                      │      └──────────────┘
                                     │
                                     └─────► Other Slave / ASIC
```

### 4.2 SafeSPI Master 软件流程

```text
配置 SPI Mode / Baudrate / CS (CHCTLi + SCONF + SSCFG)
        ↓
构造 MOSI SafeSPI Frame (32/48 bit)
        ↓
软件计算 CRC
        ↓
启动 SPI Transfer (MIX_PUSH / SCONF_PUSH + DATA_PUSH)
        ↓
接收 MISO Frame (RX_POP)
        ↓
校验 CRC / D bit / 地址 / 状态位
        ↓
处理 out-of-frame pipeline
        ↓
上报 sensor data 或 fault
```

### 4.3 48-bit Frame 拼接方案（该 MCU）

由于单帧最大 32 位，48-bit SafeSPI 帧建议采用以下硬件拼接方案：

**方案：连续帧模式（推荐）**

```text
FIFO 写入序列：
  1. SCONF1: DATCNT=31 (32位), LAST=0, MSB=1, BYTE=0, SS=目标片选
  2. DATA1:   32-bit SafeSPI 帧高 32 位
  3. SCONF2: DATCNT=15 (16位), LAST=1, MSB=1, BYTE=0, SS=同一目标
  4. DATA2:   16-bit SafeSPI 帧低 16 位

总线行为：
  CS 在整个过程中保持低电平（SCONF1.LAST=0 保持，SCONF2.LAST=1 释放）
  MOSI 连续输出 32 + 16 = 48 位数据
```

**必须验证的事项：**
- SCONF1 和 DATA1 之间、DATA1 和 SCONF2 之间、SCONF2 和 DATA2 之间是否有额外时钟间隙；
- SCONF 配置字本身是否出现在 MOSI 总线上（13K 的 QSPI 架构中 BACON/SCONF 不发送到总线，仅内部配置，但需实测确认）；
- CS 低电平持续时间是否覆盖完整的 48 个 SCK 周期。

### 4.4 Fault Management

SafeSPI 文档中的 fault management 更准确地说是 **错误响应 / error indication 规则示例**，不是统一固定的 fault code 表。不同帧格式和不同寻址方式下，Slave 的响应方式不同。

规范中明确涉及的典型错误包括：

- MOSI CRC Error；
- SCK cycle count 不等于 32 或 48；
- TA9:8 slave address 不匹配（common CS 地址选择场景）；
- TA7:0 内部地址 / command 不支持；
- Module internal error。

对应的 error indication 可能是以下形式之一，而不一定是单独的“fault frame”：

| 场景 | SafeSPI 规范中的典型处理方式 |
|---|---|
| 32-bit in-frame MOSI CRC Error | Slave 可将 CR2:0 的最后一位取反，使响应 CRC 故意错误 |
| common CS + 非本 Slave 地址 | MISO high-Z，避免多个 Slave 同时驱动 MISO |
| dedicated CS + CRC/clock/address error | MISO 返回 error indication |
| 48-bit FixedSensorFrame 通信错误 | 可通过 **CE bit** 指示上一 MOSI frame 的 communication error |
| sensor data 异常 | 可通过 **S1:0 / S0** status bits 表示 sensor error 或 init state |
| 内部模块错误 | 优先返回 error indication；无法返回时可 high-Z / no answer |

该 MCU 可提供部分底层 SPI 错误检测：
- TX FIFO 欠载（Master 模式）；
- RX FIFO 溢出；
- 波特率错误（Baud Rate Error）；
- 阶段超时（Phase Timeout）；
- SLSI 取消选择（Slave 模式）。

但这些不是 SafeSPI 语义层 fault。SafeSPI 层仍需软件处理：CRC3/CRC8 校验、TA/SA 匹配、D bit 分类、S1:S0/S0/CE 解析、out-of-frame request-response pipeline 匹配、错误计数、retry/降级策略以及 DEM/DET/DTC 上报。

## 5. SafeSPI 与 AUTOSAR SPI 的关系

AUTOSAR SPI Handler/Driver 负责“如何调用 MCU SPI 外设完成传输”。SafeSPI 负责“SPI 上传输的数据帧如何定义、CRC 如何计算、fault 如何管理、monitor 如何监听”。

AUTOSAR SPI 的 Channel / Job / Sequence 模型可以承载 SafeSPI Master：

| AUTOSAR SPI 概念 | SafeSPI 用法 |
|---|---|
| Channel | 一个 32-bit/48-bit frame，或构成 frame 的数据元素 |
| Job | 同一 CS 下的一次 SafeSPI 事务 |
| Sequence | 多个 SafeSPI frame 的连续访问序列 |
| EB buffer | SafeSPI 软件层提供 Tx/Rx buffer |

AUTOSAR SPI 标准层面只处理 Master mode、full-duplex mode。用 AUTOSAR SPI 实现 SafeSPI Master 合理；实现 SafeSPI Slave 不是标准能力。

---

## 6. 基于 MCU SPI 规格书的 SafeSPI 支持性评估

### 6.1 MCU SPI 关键能力摘要（来自规格书 V1.8）

| 能力 | 规格 |
|---|---|
| 工作模式 | Master / Slave / Mixed（CTL0.MOD） |
| 数据长度 | 2~32 位可配（SCONF.DATCNT），BYTE=1 时支持字节模式扩展 |
| CPOL/CPHA | Master 可配；Slave 支持 {0,0}/{0,1}/{1,0}/{1,1} 四种 |
| 位序 | MSB/LSB 可配（SCONF.MSB），支持字节序转换（CHCTLi.BIGEND） |
| 片选 | Master 16 路输出（spi_slso0-15）；Slave 7 路输入（spi_slsi1-7） |
| FIFO | 4x32bit TX FIFO，4x32bit RX FIFO |
| DMA | 支持短帧/XXL/连续帧/自动连续等多种 DMA 传输模式 |
| 时序控制 | LEAD/TRAIL/IDLE 延迟可配（SCONF.LCNT/TCNT/ICNT + 预分频） |
| 时钟 | 接口时钟 fSCLKO/fSCLKI 最高 50 MHz |
| 错误检测 | 奇偶校验（仅 Slave）、波特率错误、TX 欠载、RX 溢出、阶段超时、SLSI 取消选择 |
| 其他 | Loopback、OCDS 调试、Move 自动连续模式、休眠/暂停状态管理 |

### 6.2 MCU 作为 SafeSPI Master

| 检查项 | SafeSPI 需求 | MCU 规格书支持情况 | 判定 |
|---|---|---|---|
| SPI Master mode | 必须 | ✅ CTL0.MOD=00 支持 Master | **可实现** |
| CPOL=0, CPHA=0 | out-of-frame | ✅ CHCTLi.SCKPOL=0, SCKPHASE=0 | **可实现** |
| CPOL=0, CPHA=1 | in-frame | ✅ CHCTLi.SCKPOL=0, SCKPHASE=1 | **可实现** |
| MSB first | SafeSPI 要求 | ✅ SCONF.MSB=1, CHCTLi.BIGEND 可配 | **可实现** |
| SCK ~10 MHz | 目标速率 | ✅ 最高 50 MHz，通过 PDIV(1-256) × BAUDPREDIV(1-64) × (ACNT+BCNT+CCNT) 分频可配到 10 MHz 附近 | **可实现** |
| 32-bit frame | 32-bit SafeSPI | ✅ SCONF.DATCNT=31 (32位), BYTE=0 | **可实现** |
| 48-bit frame | 48-bit SafeSPI | ⚠️ 单帧最大 32 位，需连续帧模式拼接（32+16）。需验证 CS 保持和总线无间隙。 | **条件可实现** |
| CS 保持 | frame 边界关键 | ✅ SCONF.LAST=0 保持 CS，LAST=1 释放 CS | **可实现** |
| CS delay | setup/hold 相关 | ✅ LEAD/TRAIL/IDLE 可配，有独立预分频 | **可实现** |
| DMA | 周期采样效率 | ✅ 支持多种 DMA 模式 | **可实现** |
| CRC | 32-bit CRC3 / 48-bit CRC8，且覆盖范围随帧格式不同 | ❌ 无 SafeSPI 专用硬件 CRC；仅有 Slave 奇偶校验，不能等同 SafeSPI CRC | **软件/通用CRC外设辅助实现** |
| fault management | error indication 规则，不是固定 fault code | ⚠️ 有底层错误标志（underrun/overrun/baud error/timeout），但 SafeSPI 的 S1:S0/S0/CE/high-Z/CRC错误响应需软件处理 | **软件实现** |
| out-of-frame pipeline | 上一帧请求，下一帧返回逻辑响应 | ✅ Master 端无需专用硬件，软件维护 request-response 对应关系即可 | **软件实现** |
| full-duplex | 同时收发 | ✅ 标准全双工 | **可实现** |

**Master 结论：**

```text
该 MCU 作为 SafeSPI Master：
- 32-bit 帧可直接硬件发送；
- 48-bit 帧需连续帧模式拼接，需实测验证波形；
- CRC3/CRC8、TA/SA 地址、D 位、S1:S0/S0/CE/high-Z 等 error indication、out-of-frame pipeline 全部由软件协议层实现；
- 10 MHz 时钟能力满足；
- CS 控制和时序延迟配置灵活。
```

### 6.3 MCU 作为 SafeSPI Slave

| 检查项 | SafeSPI 需求 | MCU 规格书支持情况 | 判定 |
|---|---|---|---|
| SPI Slave mode | 必须 | ✅ CTL0.MOD=10 支持 Slave | **可实现** |
| MISO valid after CS↓ | ≤40 ns | ❓ 规格书未给出 Slave 输出时序参数 | **待验证** |
| MISO valid after SCK↓ | ≤32 ns | ❓ 规格书未给出 Slave 输出时序参数 | **待验证** |
| MISO high-Z when CS high | CS 高时高阻 | ❓ 规格书仅描述 "SLSI 取消选择时移位寄存器停止"，未明确 MISO 三态及 disable lag | **待验证** |
| MISO disable lag | ≤50 ns | ❓ 未给出 | **待验证** |
| TX FIFO 预装载 | out-of-frame | ✅ 支持 TX FIFO 预装载（SCTLPUSH/DATPUSH）。TX FIFO 空时发送全 1 | **可实现** |
| In-frame response | 当前帧内返回 | ⚠️ 若响应依赖当前 MOSI 命令，软件几乎无法在同一帧内实时计算并更新 MISO；即使预装响应，也需验证 MISO valid/high-Z 时序 | **高风险，不建议宣称** |
| Out-of-frame response | 下一帧返回 | ✅ 软件提前准备 TX buffer，可行性较高 | **可实现** |
| 多 slave common CS | TA9:8/TA9 地址匹配，不匹配时通常需 MISO high-Z 避免冲突 | ❌ 无硬件地址过滤/自动 high-Z 控制 | **建议避免共用 CS，或外部硬件支持** |
| {CPOL,CPHA} 四种 | 兼容不同 Master | ✅ Slave 支持四种组合 | **可实现** |

**Slave 结论：**

```text
SafeSPI Slave out-of-frame：
    可评估，但必须先拿到 Slave 输出时序参数（MISO valid/disable lag）。

SafeSPI Slave in-frame：
    不建议宣称支持。响应在当前帧内完成，强依赖预装载能力、MISO valid/high-Z 路径和 Slave 输出时序 characterization。
```

### 6.4 MCU 作为 SafeSPI Monitor / Listener

| 检查项 | SafeSPI Monitor 需求 | MCU 支持情况 | 判定 |
|---|---|---|---|
| 被动监听 MOSI+MISO | 同时采样双向数据 | ❌ 无此模式 | **不可实现** |
| 以外部 SCK 为采样时钟 | 同步采样 | ❌ 不支持 | **不可实现** |
| CS 边沿识别 | 帧边界对齐 | ⚠️ Slave 模式有 SLSI 中断，但非监听用途 | **不适合** |
| Frame Reconstruction | 10 MHz 无丢样 | ❌ 无硬件支持 | **不可实现** |
| 硬件 CRC 校验 | Monitor 独立校验 | ❌ 无硬件 CRC | **不可实现** |

**Monitor 结论：**

```text
该 MCU 无专用 SafeSPI Monitor / Listener 能力。
如需 Monitor 功能，需外部硬件（FPGA/CPLD/Safety ASIC）或专用 Monitor IP。
```

---

## 7. 软件能补什么？不能补什么？

### 7.1 软件可以补的部分（SafeSPI Protocol Layer）

| 功能 | 软件可行性 |
|---|---|
| 32-bit frame pack/unpack | ✅ |
| 48-bit frame pack/unpack（配合硬件连续帧） | ✅ |
| CRC generate/check | ✅ |
| D bit 解析 | ✅ |
| status bit 解析 | ✅ |
| TA/SA 地址管理 | ✅ |
| out-of-frame pipeline | ✅ |
| error indication / fault management 处理 | ✅ |
| sensor data validity check | ✅ |
| timeout / retry | ✅ |
| DEM / DET / DTC 上报 | ✅ |
| AUTOSAR CDD 封装 | ✅ |

### 7.2 软件可部分补救的部分

| 问题 | 补救方式 | 限制 |
|---|---|---|
| 48-bit 单帧不支持 | 连续帧模式拼接 | 需验证无 CS/SCK gap |
| SCK 太快 | 降 baudrate | 牺牲吞吐 |
| CS lead/lag 不满足 | 配 SCONF.LCNT/TCNT/ICNT + 预分频 | 硬件已支持 |
| 无硬件 CRC | 软件 CRC | 增加 CPU 负载 |
| 无硬件地址过滤 | 软件比对地址 | 增加 CPU 负载 |

### 7.3 软件基本不能补的部分

| 问题 | 原因 |
|---|---|
| VIO 不支持 3.0~3.6 V | IO 电源域限制 |
| VIH/VIL 不满足 | Pad cell 固有特性 |
| VOH/VOL 不满足 | Pad driver 能力限制 |
| 输入/输出电容过大 | Pad / 封装 / 板级寄生 |
| MISO high-Z leakage 超标 | Pad leakage |
| MISO disable lag >50 ns | Slave 硬件三态路径 |
| Slave in-frame 响应来不及 | ns 级响应，软件无法实时处理 |
| Monitor 纯软件采样 | CPU/中断/DMA 延迟不可控 |

---

## 8. 当前缺失项与待验证清单

| 缺失项 | 为什么需要 | 影响范围 | 优先级 |
|:---|:---|:---|:---:|
| **MCU Pad 电气特性表** | 核对 VIH/VIL/VOH/VOL、电容、漏电流、驱动强度、slew rate | 物理层合规 | **P0** |
| **Master 输出时序图** | 核对 MOSI setup/hold、SCK 占空比、rise/fall | Master 时序 | P1 |
| **Slave 输出时序图** | 核对 MISO valid after CS/SCK、MISO disable lag | Slave 可行性 | **P0** |
| **48-bit 连续帧实测波形** | 确认 CS 保持期间无 SCONF 插入、无 SCK gap | 48-bit 帧支持 | **P1** |
| **目标应用场景确认** | Master / Slave / Monitor 哪种角色？ | 方案设计 | **P0** |
| **目标 SafeSPI Slave 器件型号** | 确认对方帧格式、in-frame/out-of-frame、电气要求 | 互操作测试 | P1 |

---

## 9. MCU 支持性评估 Checklist

### 9.1 SPI IP 基础能力（✅ = 支持，⚠️ = 条件支持，❌ = 不支持）

```text
[✅] 支持 Master mode (CTL0.MOD=00)
[✅] 支持 Slave mode (CTL0.MOD=10)
[✅] 支持 CPOL=0, CPHA=0
[✅] 支持 CPOL=0, CPHA=1
[✅] 支持 MSB first (SCONF.MSB=1)
[✅] 支持 SafeSPI 0.095~10.5 MHz 时钟范围内配置（最高 50 MHz，通过分频配置）
[✅] 支持 32-bit frame (SCONF.DATCNT=31, BYTE=0)
[⚠️] 支持 48-bit frame（需连续帧模式拼接，待验证波形）
[✅] 支持 TX FIFO / RX FIFO (4x32bit)
[✅] 支持 DMA（多种模式）
[✅] 支持连续传输不释放 CS (SCONF.LAST=0)
[✅] 支持硬件 CS lead / lag / delay 配置 (LCNT/TCNT/ICNT + 预分频)
[✅] 支持 frame complete / transfer complete 中断 (PT 中断)
[✅] 支持 underrun / overrun / baud error / phase timeout 检测
[❌] 支持 SafeSPI 专用硬件 CRC3/CRC8（无）
[❌] 支持 TA/SA 硬件地址过滤/比较（无）
```

### 9.2 Pad / PORT 能力（待 Datasheet 补充）

```text
[?] VIO 支持 3.0~3.6 V
[?] VIH/VIL 满足 SafeSPI 要求
[?] VOH/VOL 满足 SafeSPI 要求
[?] IO capacitance ≤10 pF
[?] 支持 CS pull-up
[?] 支持 MOSI/SCK/MISO pull-down
[?] 支持 MISO high-Z
[?] MISO leakage 满足要求
[?] 支持 drive strength 配置
[?] 支持 slew rate 配置
[?] SCK/MISO rise/fall time 可控制到 2~9 ns
[?] 不同负载电容下有 timing characterization
```

### 9.3 Slave 模式额外检查（待验证）

```text
[?] CS falling 后 MISO valid 是否满足 ≤40 ns
[?] SCK edge 后 MISO valid 是否满足 ≤32 ns
[?] CS rising 后 MISO disable 是否满足 ≤50 ns
[✅] 支持 TX shift register 预装载（TX FIFO）
[✅] 支持 out-of-frame response pipeline（软件+FIFO）
[❌] 支持非本地址时 MISO 不冲突（无硬件地址过滤）
```

### 9.4 Monitor 模式额外检查

```text
[❌] 是否有专用 SafeSPI monitor/listener 模式
[❌] 是否有 SPI passive sniff mode
[❌] 是否能同时采样 MOSI 和 MISO
[❌] 是否能以外部 SCK 为采样时钟
[❌] 是否能在 10 MHz 下无丢样捕获 CS/SCK/MOSI/MISO
```

---

## 10. 推荐的软件实现方案

### 10.1 模块架构

```text
┌──────────────────────────────┐
│ Application / Safety SWC      │
├──────────────────────────────┤
│ SafeSPI Service API           │
│ - SafeSpi_ReadSensor          │
│ - SafeSpi_ReadRegister        │
│ - SafeSpi_WriteRegister       │
├──────────────────────────────┤
│ SafeSPI Protocol              │
│ - frame pack/unpack           │
│ - CRC                         │
│ - address check               │
│ - fault management            │
│ - out-of-frame pipeline       │
├──────────────────────────────┤
│ SafeSPI Transport Adapter     │
│ - SPI 寄存器配置 (CHCTL/SCONF)│
│ - FIFO/DMA 触发               │
│ - 48-bit 帧拼接控制           │
├──────────────────────────────┤
│ AUTOSAR Spi Handler/Driver    │
│ 或 直接 MCU SPI IP 驱动       │
├──────────────────────────────┤
│ MCU SPI IP + PORT + DMA       │
└──────────────────────────────┘
```

### 10.2 48-bit 帧发送伪代码示例

```c
/* SafeSPI 48-bit frame 发送：使用连续帧模式拼接 32+16 位 */
Std_ReturnType SafeSpi_Send48BitFrame(
    uint8 Channel,
    const SafeSpi_Frame48_t *FramePtr)
{
    /* 第一帧：32 位，LAST=0 保持 CS */
    SCONF_Type sconf1;
    sconf1.SS       = Channel;          /* 目标片选 */
    sconf1.DATCNT   = 31u;              /* 32 位 */
    sconf1.BYTE     = 0u;               /* 位模式 */
    sconf1.MSB      = 1u;               /* MSB first */
    sconf1.LAST     = 0u;               /* 不是最后一帧，CS 保持 */
    /* ... 其他时序配置 ... */

    SPIx_SCONF_PUSH.U = sconf1.U;
    SPIx_DATPUSH0.U   = FramePtr->High32;   /* 高 32 位 */

    /* 第二帧：16 位，LAST=1 释放 CS */
    SCONF_Type sconf2;
    sconf2.SS       = Channel;
    sconf2.DATCNT   = 15u;              /* 16 位 */
    sconf2.BYTE     = 0u;
    sconf2.MSB      = 1u;
    sconf2.LAST     = 1u;               /* 最后一帧，CS 释放 */

    SPIx_SCONF_PUSH.U = sconf2.U;
    SPIx_DATPUSH0.U   = FramePtr->Low16;    /* 低 16 位 */

    return E_OK;
}
```

---

## 11. MCU 产品定义建议

### 11.1 当前 MCU 的定位

基于规格书分析，该 MCU SPI 的定位：

```text
SafeSPI-ready SPI Master（软件协议层适配）
```

可支持的宣传口径：

```text
English:
"Supports SafeSPI master communication through software protocol layer,
subject to IO electrical and timing compliance verification."

中文：
"SPI Master 接口具备 SafeSPI 软件协议适配能力，支持 32-bit 帧及
48-bit 连续帧拼接传输，最终兼容性需结合 IO 电气与时序验证。"
```

### 11.2 不建议直接宣传

不建议直接写：

```text
支持 SafeSPI
Native SafeSPI Controller
SafeSPI Slave
SafeSPI Monitor
```

除非已经具备：

```text
[ ] SafeSPI 软件协议层（frame/CRC/fault/pipeline）
[ ] 32-bit / 48-bit frame 测试通过
[ ] 48-bit 连续帧拼接波形验证（无 CS/SCK gap）
[ ] CRC/fault management 测试通过
[ ] out-of-frame pipeline 测试通过
[ ] 典型 SafeSPI sensor / ASIC 互操作测试通过
[ ] Pad 电气参数证明（VIH/VIL/VOH/VOL/电容/漏电流）
[ ] 10 MHz 时序证明（setup/hold/valid/disable）
[ ] 如果声称 Slave：MISO valid / high-Z / disable timing 证明
[ ] 如果声称 Monitor：passive sniffing 能力证明
```

---

## 12. 13K 对 SafeSPI 七大类要求的实现情况

| SafeSPI 要求大类 | 13K 实现情况 |
|:---|:---|
| **物理层 / IO 电气** | **结论：待验证（无 Pad Datasheet）**<br>支持的项：SPI IP 本身不决定 Pad 电气合规性<br>不支持的项：软件无法补救 VIO/VIH/VIL/VOH/VOL/CIO/漏电流等硬性电气参数不满足<br>可软件实现：无<br>资料不足不确定：VIO 3.0~3.6 V、CIO≤10 pF、CLWide/CLNarrow、MISO high-Z 漏电流、CS pull-up、MOSI/SCK/MISO pull-down、输入迟滞、驱动强度、slew rate |
| **时序** | **结论：Master 侧需波形验证，Slave 侧高度依赖 silicon characterization**<br>支持的项：Master 接口时钟最高 50 MHz，可配置到 SafeSPI 0.095~10.5 MHz 范围；CS lead/trail/idle 延迟可编程<br>不支持的项：当前资料未证明 MISO valid after CS≤40 ns、MISO valid after SCK≤32 ns、MISO disable lag≤50 ns<br>可软件实现：降速、配置 CS/SCK 间隔可缓解部分 timing 压力<br>资料不足不确定：SCK/MOSI/CS rise/fall 2~9 ns、SCK high/low≥37 ns、MOSI valid≤10 ns、sequential transfer delay 200/450/750 ns 等需要实测波形 |
| **SPI 传输层模式** | **结论：Master 基本支持；48-bit 帧条件支持**<br>支持的项：Master/Slave 模式、CPOL=0、CPHA=0/1、MSB first、32-bit 帧、CS 低电平保持与释放控制、全双工、DMA、TX/RX FIFO<br>不支持的项：单次硬件 frame 最大 32 bit，不能原生一次性发 48 bit<br>可软件实现：48-bit 通过连续帧模式拼接 32+16，需要验证 CS 低电平保持、SCK 连续性和帧间间隔<br>资料不足不确定：48-bit 拼接是否完全满足目标 slave 对连续 48 clock 的要求 |
| **逻辑层 / 帧格式** | **结论：Master 端软件可实现，硬件无 SafeSPI 原生语义支持**<br>支持的项：底层可搬运 32/48 bit 数据流<br>不支持的项：无硬件帧解析器、无 SafeSPI CRC3/CRC8、无 TA/SA 地址比较器、无 D bit/S1:S0/S0/CE 自动解析器<br>可软件实现：32/48-bit 帧打包/拆包、TA9:0/SA9:0 管理、D bit 解析、S1:S0/S0/CE 解析、CRC3/CRC8 生成与校验、FrTyp/RW/CAP 等字段处理<br>资料不足不确定：无 |
| **协议行为 / 机制** | **结论：Master out-of-frame 可行；Slave out-of-frame 条件可行；Slave in-frame 不建议；Monitor 不支持**<br>支持的项：Master out-of-frame pipeline 可由软件维护；Slave out-of-frame 可通过 TX FIFO 预装载评估<br>不支持的项：普通 SPI IP 不支持 passive listener；无硬件地址过滤后自动 high-Z；无硬件 SafeSPI pipeline 关联<br>可软件实现：Master request-response pipeline、地址比对、error indication 解析、timeout/retry 策略<br>资料不足不确定：Slave in-frame 与 common CS 多 Slave 场景需 MISO high-Z/valid timing 证明，不建议作为当前支持项 |
| **故障管理 / 诊断** | **结论：底层 SPI 错误部分支持；SafeSPI 语义层需软件封装**<br>支持的项：TX FIFO 欠载、RX FIFO 溢出、波特率错误、阶段超时、SLSI 取消选择（Slave 模式）<br>不支持的项：无硬件 SafeSPI error indication 生成/解析；无硬件 CRC 错误后自动 high-Z/CE/CRC invert 行为<br>可软件实现：CRC 错误检测、TA/SA 不匹配处理、unsupported address/command 处理、S1:S0/S0/CE 解析、out-of-frame response/request 匹配、错误计数、DEM/DET/DTC 上报、降级模式<br>资料不足不确定：MISO stuck-at、timeout、sequence error 属于工程扩展诊断，不是 SafeSPI 规范中统一固定的 fault code 表 |
| **Monitor / Listener** | **结论：不支持**<br>支持的项：无专用支持项<br>不支持的项：被动监听且不驱动总线、同时采样 MOSI+MISO、以外部 SCK 为采样时钟、CS 边沿帧对齐、10 MHz 下无丢样重建 32/48 bit 帧、独立 CRC 校验、Address/D 位硬件解析、Fault Indication<br>可软件实现：不建议用 CPU/普通 SPI slave 模拟 monitor<br>资料不足不确定：无 |

### 一句话总结

```text
13K 的 SPI 控制器（QSPI 架构）可作为 SafeSPI Master 的底层传输接口：
- 32-bit 帧直接支持；
- 48-bit 帧可通过连续帧模式拼接实现，需实测验证波形；
- SafeSPI 逻辑层（CRC3/CRC8、TA/SA 地址、D 位、S1:S0/S0/CE/error indication、pipeline）由软件实现；
- Slave 模式 out-of-frame 可评估，但缺少 MISO 时序 characterization；
- Slave in-frame 不建议；
- Monitor/Listener 不支持；
- 电气参数必须结合 Pad Datasheet 确认。
```

---

## 附录 A：SafeSPI 完整要求基线清单

### A.1 物理层 / IO 电气要求

| 编号 | 参数 | SafeSPI 要求 |
|:---|:---|:---|
| PHY-01 | VIO | **3.0 V ~ 3.6 V** |
| PHY-02 | 器件输入/输出电容 | **≤ 10 pF** |
| PHY-03 | 总线负载电容 (Wide) | **10 pF ~ 100 pF** |
| PHY-04 | 总线负载电容 (Narrow) | **30 pF ~ 100 pF** |
| PHY-05 | 输入低电平 VIL | **0 ~ 0.3 × VIO** |
| PHY-06 | 输入高电平 VIH | **0.7 × VIO ~ VIO** |
| PHY-07 | 输出低电平 VOL | **0 ~ 0.1 × VIO** |
| PHY-08 | 输出高电平 VOH | **0.9 × VIO ~ VIO** |
| PHY-09 | 输入迟滞 | **≥ 0.1 × VIO** |
| PHY-10 | MISO high-Z 漏电流 | **-10 µA ~ +10 µA** |
| PHY-11 | CS 上拉 | **60 kΩ ~ 140 kΩ** 或等效电流源 |
| PHY-12 | MOSI/SCK/MISO 下拉 | **60 kΩ ~ 140 kΩ** 或等效电流源 |

### A.2 时序要求基线

**Slave / Listener 侧相关要求（Master 视角）：**

| 编号 | 参数 | 符号 | SafeSPI 要求 |
|:---|:---|:---|:---|
| TIM-S01 | MISO data valid after CS↓ | A | **≤ 40 ns** |
| TIM-S02 | MISO data valid after SCK edge | B | **≤ 32 ns** |
| TIM-S03 | MOSI data hold time | C | **≥ 20 ns** |
| TIM-S04 | MISO rise/fall time | D | **2 ns ~ 9 ns** |
| TIM-S05 | MISO disable lag (CS↑→high-Z) | E | **≤ 50 ns** |
| TIM-S06 | MOSI data setup time | F | **≥ 10 ns** |

**Master / Listener 侧相关要求（Slave 视角）：**

| 编号 | 参数 | SafeSPI 要求 |
|:---|:---|:---|
| TIM-M01 | SCK operating frequency | **0.095 MHz ~ 10.5 MHz** |
| TIM-M02 | SCK disable lead time | **≥ 10 ns** |
| TIM-M03 | SCK enable lead time | **≥ 40 ns** |
| TIM-M04 | SCK rise/fall time | **2 ns ~ 9 ns** |
| TIM-M05 | SCK high time | **≥ 37 ns** |
| TIM-M06 | SCK low time | **≥ 37 ns** |
| TIM-M07 | SCK enable lag time | **≥ 20 ns** |
| TIM-M08 | SCK disable lag time | **≥ 10 ns** |
| TIM-M09 | Sequential transfer delay, out-of-frame write | **≥ 750 ns** |
| TIM-M10 | Sequential transfer delay, out-of-frame read | **≥ 450 ns** |
| TIM-M11 | Sequential transfer delay, in-frame | **≥ 200 ns** |
| TIM-M12 | MOSI rise/fall time | **2 ns ~ 9 ns** |
| TIM-M13 | MISO data setup time | **≥ 5 ns** |
| TIM-M14 | MISO data hold time | 稳定到下一个 SCK shift edge |
| TIM-M15 | MOSI valid time | **≤ 10 ns** |
| TIM-M16 | CS rise/fall time | **2 ns ~ 9 ns** |

### A.3 SPI 传输层模式要求

| 编号 | 要求项 | 具体规格 |
|:---|:---|:---|
| TRF-01 | CPOL | **0** |
| TRF-02 | CPHA | **0** (out-of-frame) / **1** (in-frame) |
| TRF-03 | Bit Order | **MSB first** |
| TRF-04 | Frame 位长 | **32 bit**；**48 bit 仅 out-of-frame** |
| TRF-05 | 时钟速率 | **0.095 MHz ~ 10.5 MHz** |
| TRF-06 | CS 极性 | **低有效** |
| TRF-07 | CS 高电平行为 | Slave 不响应；MISO 必须 **high-Z** |
| TRF-08 | 传输方向 | **Full-duplex** |

### A.4 逻辑层 / 帧格式要求

**32-bit Frame：**
- Target Address / command：**TA9:0**；其中 TA9:8/TA9 可作为 common CS 下的 slave address，TA7:0 或 TA8:7/TA6:0 作为 slave internal address，具体取决于 addressing option；
- Source Address：**SA9:0**；用于标识 response data 的来源/内容；
- 32-bit in-frame 变体只使用 **TA9:5 / SA9:5**；
- Data/Status：可变，sensor data 最多 **DATAO15:0**；
- D bit：1 bit，**D=1 sensor data format；D=0 non-sensor data/status/config readback**；
- Sensor status：out-of-frame 使用 **S1:0**，in-frame 使用 **S0**；
- CRC：**3-bit CRC，polynomial 0x5**；out-of-frame command/response 覆盖 bit31..3，in-frame command 覆盖 bit31..5，in-frame response 覆盖 bit26..3；
- 支持 in-frame + out-of-frame。

**48-bit Frame：**
- Target Address / command：**TA9:0**；
- Source Address：**SA9:0**；
- Sensor Data：最多 **DATAO19:0**；
- D bit：1 bit，**D=1 sensor data format；D=0 non-sensor data**；
- FixedSensorFrame 额外定义 **CE、IDS、S1:0、DCnt** 等字段；
- CRC：**8-bit CRC，polynomial 0x97**，覆盖 bit47..8；
- **仅支持 out-of-frame**。

### A.5 协议行为 / 机制要求

| 编号 | 机制 | 要求 |
|:---|:---|:---|
| PRT-01 | In-frame Response | Slave response data 位于 Master request 的同一 time slot；仅 32-bit 变体定义 |
| PRT-02 | Out-of-frame Response | Slave logical response 位于 Master 的下一帧；32-bit 和 48-bit 均定义 |
| PRT-03 | Multi-slave Common CS | 可通过 TA9 或 TA9:8 选择最多 2/4 个 Slave；非本地址通常需 MISO high-Z 避免冲突 |
| PRT-04 | 32/48-bit mode selection | 可通过独立 CS32/CS48 或 FrTyp + address/clock count/CRC 信息切换 |
| PRT-05 | Error indication / Fault Management | 规范给出处理示例，可能通过 status bits、MISO high-Z、CE bit、故意错误 CRC 或其他方式表示；不是固定统一 fault code 表 |
| PRT-06 | Monitor / Listener | 被动监听，不驱动总线；CSx、SCK、MOSI、MISO 均为输入 |
| PRT-07 | Monitor Frame Reconstruction | 监听 32/48-bit frame，校验 CRC，识别 D bit、address、sensor data/status |
| PRT-08 | Sensor data identification | 通过 response 中的 D bit 区分 sensor data frame 与 non-sensor/status/config readback frame |

### A.6 故障管理 / 诊断机制要求

> 这里按 SafeSPI 文档中的 fault management example 收敛。MISO stuck-at、timeout、sequence error 等可以作为 MCU 软件工程诊断扩展，但不是 SafeSPI Rev 2.0 统一规定的固定 fault code。

| 编号 | 检测/异常项 | SafeSPI 规范中的典型响应方式 |
|:---|:---|:---|
| FLT-01 | MOSI CRC Error | 32-bit in-frame 可故意反转 CR2:0 最后一位；out-of-frame/common CS 场景可在下一帧 high-Z；dedicated CS 场景可返回 error indication |
| FLT-02 | SCK cycle count 不等于 32/48 | common CS 场景通常 high-Z；dedicated CS 场景可返回 error indication 或在下一帧给出信息 |
| FLT-03 | TA9:8 / TA9 slave address 不匹配 | common CS 场景 MISO high-Z；dedicated CS 场景不适用 |
| FLT-04 | TA7:0 / 内部地址或命令不支持 | 对本 Slave 可返回 error indication；非本 Slave 不应驱动 MISO |
| FLT-05 | Module internal error | 优先返回 error indication；无法返回时 high-Z / no answer |
| FLT-06 | Sensor data 状态异常 | 通过 S1:0 或 S0 表示 sensor error/init/non-sensor data |
| FLT-07 | 48-bit FixedSensorFrame communication error | 通过 CE=1 表示上一 MOSI frame 存在 communication error，例如 clock cycle 错或 undefined address |

### A.7 Monitor / Listener 特殊要求

| 编号 | 要求 |
|:---|:---|
| MON-01 | 被动监听，不驱动总线 |
| MON-02 | 同时采样 MOSI + MISO |
| MON-03 | 以外部 SCK 为采样时钟 |
| MON-04 | CS 边沿识别用于帧边界对齐 |
| MON-05 | 10 MHz 下无丢样重建 32/48 bit 帧 |
| MON-06 | 独立 CRC 校验 |
| MON-07 | Address / D bit 解析 |
| MON-08 | Fault Indication |

---

*文档版本：基于 SafeSPI Rev 2.0 (2021-03-26) 与 MCU SPI 规格书 V1.8 (2026-05-06) 分析*
*更新日期：2026-05-11（按原大纲，仅修订与 SafeSPI Rev 2.0 不匹配的内容）*
*待补充：MCU Pad 电气参数、Slave 输出时序、48-bit 连续帧实测波形*
