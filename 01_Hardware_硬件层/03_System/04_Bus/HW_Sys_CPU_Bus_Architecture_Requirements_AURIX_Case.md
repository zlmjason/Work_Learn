# 车规级 MCU 系统工程师对 CPU / 总线架构的认知深度与需求定义方法

> 适用对象：车规 MCU 系统工程师、芯片产品定义、SoC 架构需求定义、系统验证 / CV 测试工程师。  
> 视角定位：**不是替 IC 设计写 RTL，而是把应用场景、实时性、安全性、可测性、可诊断性转化为芯片架构需求。**

---

## 0. 总结先行

对于车规级 MCU 的系统工程师，CPU 和总线不能只停留在“主频多少、几核、有没有 DMA”的层面。真正需要关注的是：

```text
应用场景 → 访问路径 → 竞争点 → 最坏延迟 → 安全隔离 → 错误诊断 → 产品需求
```

系统工程师要能回答下面这些问题：

| 问题 | 本质 |
|---|---|
| 多核同时访问共享 RAM，会不会拖慢控制环？ | 总线仲裁 + Slave 端口竞争 |
| DMA 搬运大数据时，CPU 中断延迟会不会抖？ | Master 竞争 + QoS / 仲裁策略 |
| Flash 编程时，代码还能不能执行？ | NVM 访问路径 + stall + bank 设计 |
| 外设寄存器写入返回后，硬件是否已经真正执行？ | posted write / write buffer 语义 |
| DMA 访问 cacheable RAM，数据为什么不一致？ | cache coherence / non-cacheable region / cache maintenance |
| 非法地址访问能不能定位到哪个 Master？ | TAG ID + error capture + default slave |
| ASIL 分区之间能不能做到 FFI？ | bus-level MPU / access enable / privilege / SMU alarm |

**一句话：系统工程师不是只看 CPU 算力，而是定义整颗 MCU 在真实应用压力下的“确定性、带宽、隔离、错误处理和可观测性”。**

---

## 1. 系统工程师面对 CPU / 总线时的职责边界

### 1.1 系统工程师不需要深到什么程度？

一般不需要深入到：

- Crossbar 内部 RTL 状态机怎么写；
- 仲裁器每个触发器如何实现；
- CDC 同步器的具体门级结构；
- SRAM macro 内部 bitcell；
- ECC encoder / decoder 的门级优化；
- AXI / AHB / SRI / FPI 每个信号的 RTL 波形细节。

这些是 IC 架构师、RTL 设计、验证工程师的主工作面。

### 1.2 系统工程师必须深到什么程度？

系统工程师需要深到：

| 维度 | 必须理解的问题 |
|---|---|
| 架构拓扑 | 有哪些 Master、Slave、Bus domain、Bridge、Clock domain？ |
| 访问路径 | CPU / DMA / HSM / Debug / Ethernet 访问某资源时走哪条路径？ |
| 竞争模型 | 哪些场景会多个 Master 打到同一个 Slave？ |
| 延迟模型 | 平均延迟、峰值延迟、最坏延迟、抖动来源是什么？ |
| 带宽模型 | 理论带宽、实际可用带宽、burst 效率、桥瓶颈是什么？ |
| 访问语义 | posted write、read completion、atomic、barrier、RMW 是否支持？ |
| 缓存一致性 | CPU cache 与 DMA / 外设 / 多核共享数据如何一致？ |
| 安全隔离 | Master TAG、privilege、bus MPU、region protection 如何支持 FFI？ |
| 错误诊断 | 非法地址、权限错误、协议错误、EDC/ECC 错误如何捕获？ |
| 可验证性 | 有没有计数器、trace、error address、master ID、性能监控？ |

系统工程师应该能把上面的内容变成芯片需求，例如：

```text
REQ-BUS-001:
DMA0 在 80 MB/s 连续搬运数据时，CPU0 访问本地 DSPR 的延迟不得受到影响；
CPU0 访问 LMU0 的最大附加延迟不得超过 X cycles。
```

```text
REQ-BUS-002:
所有 SRI / SPB 非法访问必须捕获 Master TAG、访问地址、访问类型、权限级别，
并可选择触发中断或 SMU alarm。
```

```text
REQ-BUS-003:
跨桥 posted write 必须在手册中明确完成语义；
对安全相关寄存器写入，软件必须有可读回或 barrier 机制确认写入已生效。
```

---

## 2. CPU 架构：系统工程师需要关注的深度

### 2.1 CPU 不是只看 DMIPS / CoreMark

车规 MCU 的 CPU 需求不能只写：

```text
CPU 主频 ≥ 300 MHz
CoreMark ≥ xxx
```

这太浅。系统工程师需要关注 CPU 与系统架构的耦合。

### 2.2 CPU 架构关键关注点

| 类别 | 需要关注的点 | 为什么重要 |
|---|---|---|
| Core 数量 | 单核 / 多核 / lockstep / checker core | 决定性能、安全和软件架构 |
| Pipeline | 分支、load-use、stall、flash wait state | 决定真实 WCET |
| 指令集 | DSP、FPU、MAC、bit 操作、atomic | 影响控制算法与编译器效率 |
| 中断异常 | 嵌套、优先级、入口延迟、上下文保存 | 决定实时响应 |
| 本地存储 | PSPR、DSPR、TCM、local SRAM | 决定确定性访问能力 |
| Cache | ICache、DCache、cache line、write policy | 决定性能和一致性风险 |
| MPU / MMU | region、权限、cache attribute | 决定隔离、安全和内存属性 |
| Atomic | TAS、CMPSWAP、LDREX/STREX 类 | 决定多核同步和 RTOS 原语 |
| Barrier | dsync/isync/dmb/dsb/isb 类 | 决定顺序性和外设写入语义 |
| Debug / Trace | PC trace、data trace、breakpoint | 决定调试和量产问题定位能力 |
| Safety | lockstep、STL、ECC、BIST、trap | 决定 ASIL 能力 |

### 2.3 CPU 需求定义要从“任务”出发

例如电机控制 / 域控 / 底盘 MCU，应该先列任务：

| 任务 | CPU 关注点 | 总线关注点 |
|---|---|---|
| 10 kHz 电流环 | ISR latency、FPU、PSPR/DSPR | 代码和数据不能被 DMA 干扰 |
| CAN FD 网关 | 中断压力、DMA、buffer | 多通道 DMA 与 RAM bank 带宽 |
| OTA / Flash 编程 | 代码运行区、bank swap | NVM 与 CPU fetch 冲突 |
| HSM 安全通信 | mailbox、timeout | HSM master 与 CPU/DMA 竞争 |
| 诊断 / 刷写 | UDS、Flash、CRC | Flash、DMA、通信外设并发 |
| Safety monitor | lockstep、SMU、trap | 错误捕获路径可靠性 |

由此推导 CPU 产品需求：

```text
1. 控制类 ISR 代码可放入 PSPR / TCM，数据可放入 DSPR / TCM。
2. CPU 本地存储访问不得经过共享系统总线。
3. cacheable / non-cacheable 地址别名或 MPU 属性必须明确支持。
4. CPU 对外设寄存器访问必须有明确 ordering 语义。
5. 多核共享原子操作必须支持 bus-level atomic 或软件锁机制。
```

---

## 3. 总线架构：系统工程师必须掌握的基本知识

## 3.1 Master / Slave / Agent

在片上总线里：

| 术语 | 含义 |
|---|---|
| Master / Initiator | 主动发起访问的一方，例如 CPU、DMA、HSM、Ethernet、Debug |
| Slave / Target | 被访问的一方，例如 SRAM、Flash、外设寄存器、Bridge、LMU |
| Agent | 连接到总线上的 Master 或 Slave 节点 |
| Interconnect / Fabric | 负责连接 Master 和 Slave 的总线 / crossbar / NoC |
| Bridge | 不同协议、不同位宽、不同频率、不同 domain 之间的转换器 |

AURIX TC3xx 的 SRI 文档中，SRI agent 包括 master 和 slave；master 可以发起 SRI transaction，slave 只能响应访问；SRI crossbar 提供同一 domain 内 master 和 slave 的互连、仲裁和错误捕获能力。AURIX 手册还定义了 MCI、SCI、domain 和 arbiter 等概念。参考：`TC3xx User Manual part1.pdf` 中 SRI Operational Overview。  
来源：fileciteturn5file3

---

## 3.2 Address phase / Data phase

一次总线事务通常可以分为：

```text
Address phase: 地址、访问类型、权限、Master ID、burst 属性等
Data phase   : 读数据或写数据
Response     : OK / Error / Retry / Timeout
```

为什么系统工程师要理解这个？

因为安全机制和错误定位经常分布在不同阶段：

| 阶段 | 可能错误 |
|---|---|
| Address phase | 地址错误、权限错误、Master TAG 错误、EDC 错误 |
| Data phase | ECC/EDC 错误、数据返回错误、写数据错误 |
| Response phase | bus error、timeout、decode error |

AURIX SRI 明确区分 address phase EDC、write data EDC、read data EDC，并且不同错误的响应路径不同。参考：`TC3xx User Manual part1.pdf` 中 SRI EDC Errors。  
来源：fileciteturn5file2

---

## 3.3 单次传输、block transfer、burst

### 3.3.1 基本概念

| 概念 | 含义 |
|---|---|
| Beat | burst 中的一个数据拍 |
| Single transfer | 一次事务只传一个数据单元 |
| Burst / Block transfer | 一次地址请求后连续传多个 beat |
| Incremental burst | 地址递增 |
| Wrap burst | 地址在某个边界内回绕 |
| Fixed burst | 地址固定，常见于 FIFO |
| Burst length | 一次 burst 有几个 beat |
| Burst size | 每个 beat 的数据宽度 |

### 3.3.2 为什么 burst 重要？

burst 的价值是减少地址 phase 和仲裁开销，提高有效带宽。

粗略理解：

```text
有效带宽 ≈ 数据 beat 数 / (地址开销 + 仲裁开销 + 数据 beat 数 + wait state)
```

如果是单次 32-bit 访问，每次都要仲裁和地址 phase，效率低。  
如果是 4-beat / 8-beat burst，可以摊薄开销，DMA 搬运效率高。

### 3.3.3 burst 的副作用

burst 不是越长越好。

| 好处 | 风险 |
|---|---|
| 提高 DMA / memory copy 吞吐 | 长时间占用 Slave，增加 CPU latency |
| 减少仲裁次数 | 影响高优先级实时访问 |
| 适合连续 buffer | 不适合离散寄存器访问 |
| 适合 cache line fill | 可能造成总线瞬时压力 |

系统需求里不能只写“DMA 支持 burst”，还要写：

```text
1. 支持哪些 burst length？
2. 是否支持固定地址 burst 访问 FIFO？
3. 是否支持 wrap burst 以适配 cache line fill？
4. 仲裁器是否允许高优先级请求打断长 burst？
5. 长 burst 下 CPU / ISR 最大阻塞延迟是多少？
```

### 3.3.4 AURIX 的例子

AURIX SRI operation code 中包含：

| SRI 操作 | 含义 |
|---|---|
| SDTB | Single Data Transfer Byte，8 bit |
| SDTH | Single Data Transfer Half-word，16 bit |
| SDTW | Single Data Transfer Word，32 bit |
| SDTD | Single Data Transfer Double-word，64 bit |
| BTR2 | Block Transfer Request，2 transfers，wrap-around address |
| BTR4 | Block Transfer Request，4 transfers，wrap-around address |

来源：fileciteturn5file6

这说明系统工程师在看 AURIX 时，不能只说“总线 64-bit”，还要看它支持哪些 transaction type、block transfer 形式、错误行为、桥映射关系。

---

## 3.4 位宽、对齐、byte lane、RMW

### 3.4.1 位宽

总线位宽会影响峰值带宽，例如：

```text
理论峰值带宽 = 总线数据宽度 Byte × 总线频率
```

但理论峰值不是实际带宽。实际还会被以下因素折损：

- 仲裁；
- 地址 phase；
- wait state；
- bridge buffer；
- Slave 响应速度；
- burst 长度；
- cache miss；
- ECC / EDC；
- clock domain crossing。

### 3.4.2 对齐

系统工程师要定义：

| 访问类型 | 需要明确 |
|---|---|
| 8-bit / 16-bit / 32-bit / 64-bit | 是否都支持？ |
| 非对齐访问 | 硬件拆分、报错，还是 undefined？ |
| 跨 bus beat 访问 | 是否拆成多个 transaction？ |
| 跨 cache line 访问 | cache maintenance 如何处理？ |
| 外设寄存器半字/字节访问 | 是否允许？是否有副作用？ |

### 3.4.3 RMW

Read-Modify-Write 是车规 MCU 外设寄存器设计中的高风险点。

典型风险：

```c
REG |= BIT0;
```

这不是单纯写 BIT0，而是：

```text
read REG → modify → write REG
```

如果寄存器有 W1C、RC、硬件置位、并发 Master 访问，就可能出问题。

所以系统工程师要推动 IC 设计支持：

- SET / CLR / TOGGLE alias register；
- atomic bit set / bit clear；
- write-one-to-set / write-one-to-clear 语义明确；
- RMW atomic 支持；
- 多 Master 访问同一外设时的并发规则。

AURIX FPI 文档说明 FPI 支持多 master、pipelined transaction、32-bit address/data bus、8/16/32-bit transfer、64/128/256-bit block transfer、timeout、atomic CPU operations、灵活仲裁、default slave、debug capture、Master TAG 和 supervisor mode 等机制。  
来源：fileciteturn5file8

---

## 3.5 仲裁：priority、round-robin、QoS、starvation

### 3.5.1 为什么仲裁是系统工程师重点？

仲裁决定多个 Master 同时访问同一个 Slave 时谁先走。

```text
CPU0 取指  
CPU1 访问共享 RAM  ---> LMU0
DMA 搬 buffer
HSM 访问 mailbox
```

如果全部访问 LMU0，瓶颈不在 CPU 主频，而在 LMU0 的 Slave 端口和仲裁器。

### 3.5.2 常见仲裁策略

| 策略 | 优点 | 风险 |
|---|---|---|
| Fixed priority | 高优先级实时性好 | 低优先级可能饿死 |
| Round-robin | 公平 | 高优先级实时性不强 |
| Weighted round-robin | 可兼顾公平和带宽 | 配置复杂 |
| QoS / priority level | 可按业务定义优先级 | 需要软件/硬件协同 |
| Starvation prevention | 防止低优先级长期无响应 | 可能增加高优先级抖动 |

### 3.5.3 AURIX 的例子

AURIX SRI 中，每个 SCI 关联一个 arbiter；当两个或更多 Master 访问同一个 Slave 时，arbiter 决定访问顺序，顺序由两级 round-robin 机制和用户配置决定。同时，SRI crossbar 在不同 Master 访问不同 Slave 时可以并行执行多个 transaction。  
来源：fileciteturn5file3

这给产品定义带来的启发是：

```text
不能只定义“有 crossbar”，还要定义：
1. 每个 Slave 有没有独立 arbiter？
2. 仲裁策略是否可配置？
3. 是否有优先级/QoS？
4. 是否有 starvation prevention？
5. 高优先级 Master 的最大等待周期是否可界定？
```

---

## 3.6 同步、异步、Clock Domain Crossing

### 3.6.1 同步总线

同步总线指访问双方处于同源或边沿对齐时钟域，数据在统一时钟边沿采样。

特点：

| 优点 | 缺点 |
|---|---|
| 延迟低 | 时钟树要求高 |
| 设计简单 | 频率/时钟域灵活性差 |
| 时序确定性较好 | 大 SoC 上难以全局同步 |

### 3.6.2 异步总线 / 异步桥

异步桥用于跨独立 clock domain。

常见实现：

- synchronizer flip-flops；
- async FIFO；
- request / acknowledge handshake；
- gray code pointer；
- CDC check；
- clock ratio adaptation。

特点：

| 优点 | 代价 |
|---|---|
| 支持不同 PLL / clock domain | 延迟增加 |
| 降低时钟耦合 | 吞吐可能下降 |
| 便于低功耗分域 | ordering 和 debug 更复杂 |
| 支持外设慢时钟域 | 需要 CDC 安全验证 |

### 3.6.3 系统工程师要定义什么？

| 需求项 | 说明 |
|---|---|
| clock domain 划分 | CPU / bus / flash / peripheral / HSM / debug 是否同域？ |
| 异步桥位置 | 哪些访问必经 CDC？ |
| CDC 延迟 | 最小 / 最大 / 抖动周期 |
| ordering | 同一 Master 多个 write 是否保序？跨 bridge 是否保序？ |
| reset domain | bridge 两侧 reset 顺序与异常行为 |
| low-power | 一侧 clock gate 时访问如何响应？ |
| debug | 异步桥是否有状态寄存器、overflow、timeout？ |

### 3.6.4 AURIX 的例子：GTM Bridge

AURIX GTM bridge 中存在同步 / 异步相关配置。手册中 `BYPASS_SYNC` 字段说明：当 `aei_clk` 和 `aei_sys_clk` 完全异步并来自独立时钟源时，需要使用 synchronizer flip-flops；如果两个时钟由共同 clock source 通过 gating 或 division 生成且边沿条件满足，可以 bypass synchronizer 以减少额外同步延迟。  
来源：fileciteturn3file9

这个例子非常典型：

```text
异步 = 更安全的 CDC，但增加 latency
同步 / 同源 = 可降低 latency，但要求时钟关系严格成立
```

系统工程师不能只说“支持异步桥”，而要定义：

```text
REQ-BRIDGE-CDC-001:
跨 clock domain bridge 必须明确支持 fully asynchronous mode，并给出最大访问延迟、
write buffer 深度、overflow 行为、错误上报路径和 debug status。
```

---

## 3.7 posted write / non-posted write / write buffer

### 3.7.1 posted write 是什么？

posted write 指：

```text
Master 发起写 → bridge / buffer 接收 → Master 侧认为写完成
实际写入 Slave 可能稍后发生
```

优点：

- 提高总线效率；
- 降低 Master 等待；
- 适合普通数据写入。

风险：

- 写返回不代表目标已真正更新；
- 后续读 / 触发动作可能早于实际写完成；
- 写错误不一定能返回给原 Master；
- 对安全寄存器、外设控制寄存器、高实时触发寄存器存在语义风险。

### 3.7.2 AURIX 的例子：S2S / F2S / S2F Bridge

AURIX S2S bridge 的写事务采用 posted write。也就是说，一个 SRI Master 通过 S2S bridge 写到另一个 SRI domain 时，写操作可以在源 SRI Fabric 上完成，由 S2S bridge 后续在目标 domain 完成。如果目标 domain 写事务出错，错误不会传回源 SRI Fabric。  
来源：fileciteturn5file6

AURIX SFI_F2S bridge 也类似：SPB master 写 SRI resource 时，SPB 侧可以先完成，SFI_F2S 后续在 SRI 上完成写入；如果 SRI 写出错，错误不会返回 SPB bus，而由接收 SRI slave 按配置中断或报警。  
来源：fileciteturn3file0

### 3.7.3 产品定义要求

对于车规 MCU，posted write 必须写进架构需求和软件约束：

```text
REQ-BUS-WR-001:
所有跨 bridge posted write 的完成语义必须在用户手册中明确描述。
```

```text
REQ-BUS-WR-002:
安全相关寄存器、trigger 类寄存器、reset/clock/power 控制寄存器，
必须提供 read-back、write-complete flag、barrier、non-posted path 或等效确认机制。
```

```text
REQ-BUS-WR-003:
posted write buffer full 时，Master 侧行为必须明确：stall、retry、error 或 wait。
```

```text
REQ-BUS-WR-004:
posted write 后端失败时，必须能记录目标地址、Master TAG、错误类型，并可触发 SMU/interrupt。
```

---

## 3.8 Timeout、default slave、bus error

### 3.8.1 为什么重要？

车规 MCU 不能出现访问不存在地址后系统永久 hang 住。

系统工程师要要求：

- 非法地址访问必须返回 bus error 或 timeout；
- 不能无限等待；
- 能定位 Master；
- 能定位地址；
- 能进入安全反应路径。

### 3.8.2 AURIX 例子

AURIX FPI 特性中包含 timeout detection and handling、default slave、debug support，可以在 timeout 或 bus error 时捕获 transaction information。  
来源：fileciteturn5file8

AURIX SRI protocol error 包括不存在地址 region、reserved address、unsupported opcode、访问权限错误、EDC invalid 等，相关错误可通过状态寄存器定位发生 protocol error 的 SRI Slave。  
来源：fileciteturn5file0

产品需求可以这样写：

```text
REQ-BUS-ERR-001:
所有未实现地址访问必须由 default slave 响应，不允许导致 bus hang。
```

```text
REQ-BUS-ERR-002:
bus error capture 信息至少包括：Master ID/TAG、Slave/SCI、地址、读写方向、访问大小、权限、opcode、错误类型。
```

```text
REQ-BUS-ERR-003:
timeout 阈值应可配置，并支持中断 / SMU alarm / reset escalation。
```

---

## 3.9 Master TAG、权限、bus-level MPU、FFI

### 3.9.1 为什么车规 MCU 特别关注这个？

车规 MCU 经常存在混合关键性软件：

```text
ASIL-D 控制任务
ASIL-B 诊断任务
QM 通信任务
Bootloader
HSM firmware
Debug / calibration
```

它们共享一颗芯片。如果没有总线级隔离，单个软件错误可能破坏安全相关内存或寄存器。

### 3.9.2 要关注的机制

| 机制 | 作用 |
|---|---|
| Master TAG ID | 标识访问来源，例如 CPUx、DMA channel、HSM |
| Supervisor / User | 区分特权和非特权访问 |
| Bus MPU / access enable | 按 Master / region 控制访问 |
| Peripheral protection | 控制寄存器只能特权写 |
| Safety ENDINIT | 防止运行期误改关键 SFR |
| SMU alarm | 访问违规后进入安全反应 |

AURIX Safety Manual 中说明，SRI address map monitoring 用于 slave bus agent 判断 incoming transaction address 是否属于自身地址空间，不匹配会向 SMU 产生 alarm；SRI transaction integrity 则在 SRI interface 检测 address 或 data phase 的完整性错误时触发 alarm。  
来源：fileciteturn5file10、fileciteturn5file11

对于 EMEM / LMU 等模块，Safety Manual 还描述了基于 Master Tag 的访问检查和 SV_AP supervisor privilege monitoring：如果 slave interface 接收写访问，会检查是否具备 supervisor privilege；关键模块寄存器限制为 supervisor 软件或具备 supervisor 权限的 DMA 访问。  
来源：fileciteturn5file5、fileciteturn5file11

### 3.9.3 产品定义要求

```text
REQ-FFI-001:
总线访问必须携带 Master TAG 和 privilege 信息，并覆盖 CPU、DMA、HSM、Debug、Ethernet 等所有 Master。
```

```text
REQ-FFI-002:
安全相关 RAM / SFR / 外设寄存器必须支持基于 Master TAG 的访问控制。
```

```text
REQ-FFI-003:
访问保护违规不得静默失败，必须支持错误捕获、SMU alarm 或 trap/interrupt。
```

```text
REQ-FFI-004:
DMA channel 必须能配置 privilege / protection attribute，否则 DMA 会成为绕过 CPU MPU 的后门。
```

---

## 3.10 Cache、DMA、一致性

### 3.10.1 系统工程师为什么必须懂 cache？

只要 MCU 有 DCache，DMA 就是高风险点。

典型错误：

```text
CPU 写 buffer，但数据还在 DCache，DMA 从 RAM 读到旧数据。
DMA 写 RAM，但 CPU DCache 里还有旧 cache line，CPU 读不到新数据。
```

### 3.10.2 需求定义关注点

| 项目 | 需求 |
|---|---|
| Cache line size | 软件必须知道，cache maintenance 需要对齐 |
| write-back / write-through | 影响 DMA 一致性 |
| cacheable / non-cacheable alias | 是否支持同一物理 RAM 的不同属性映射 |
| MPU attribute | 是否能按 region 配置 cache 属性 |
| DMA coherence | 是否硬件 snoop？多数 MCU 没有 |
| cache maintenance | clean / invalidate / clean+invalidate 是否支持按地址操作 |
| non-cacheable DMA buffer | 是否有推荐地址段或 MPU region |
| 跨 cache line buffer | 软件对齐和长度扩展规则 |

AURIX TC39x-B Appendix 中可以看到 EMEM RAM 同时存在 cached segment 和 non-cached segment，例如 EMEMRAM0 在 `99000000H..990FFFFFH` 为 cached segment，在 `B9000000H..B90FFFFFH` 为 non-cached segment。  
来源：fileciteturn5file16

这是一种典型的产品级设计：通过地址别名区分 cacheable / non-cacheable。系统工程师定义自研 MCU 时，需要明确：

```text
REQ-CACHE-001:
用于 DMA 的共享 RAM 必须提供 non-cacheable 访问路径，或提供明确 MPU 配置方案。
```

```text
REQ-CACHE-002:
cache maintenance API 所需的最小对齐粒度、cache line size、跨 line 行为必须在手册中明确。
```

```text
REQ-CACHE-003:
同一物理 RAM 的 cacheable / non-cacheable alias 使用限制必须明确，禁止软件同时混用导致 incoherent alias。
```

---

# 4. 以 AURIX TC3xx 为例理解总线架构

## 4.1 TC3xx 的三类片上连接资源

AURIX TC3xx User Manual 明确说明 TC3xx 平台有三类 independent on-chip connectivity resources：

| 资源 | 作用 |
|---|---|
| SRI Fabric | 连接 TriCore CPUs、DMA 和其他高带宽 requestor 到高带宽 memory / resource |
| SPB | 连接 CPUs、DMA 和其他 SPB master 到中低带宽外设 |
| BBB | 连接 CPUs、DMA、SPB masters 到 ADAS / Emulation 相关资源 |

此外，SPB master 不直接连接 SRI Fabric，而是通过 SFI_F2S bridge 访问 SRI attached resources；SRI master 不直接连接 BBB，而是通过 SFI_S2F bridge 访问 BBB attached resources。  
来源：fileciteturn3file1

系统工程师要从这个结构中学到：

```text
1. 高带宽资源和中低速外设要分 bus domain。
2. 跨 domain 必须经过 bridge。
3. bridge 是性能、ordering、错误传播和 CDC 的关键风险点。
4. “访问同一个地址”背后可能是完全不同的 bus path。
```

---

## 4.2 AURIX SRI：高带宽共享互连

### 4.2.1 SRI 的系统意义

SRI 是高带宽互连，负责：

- CPU instruction fetch；
- CPU data access；
- DMA memory access；
- 高带宽外设访问；
- LMU / EMEM / NVM / EBU 等资源访问。

Safety Manual 也说明，SRI Fabric 连接 CPU、DMA 和其他 high bandwidth requestors 到 high bandwidth memories 和其他资源，并支持 SRI masters 与 independent SRI slaves 之间的 parallel transactions。  
来源：fileciteturn3file3

### 4.2.2 SRI 的 MCI / SCI / Arbiter 模型

```text
Master → MCI → SRI Crossbar → SCI / Arbiter → Slave
```

| 部件 | 作用 |
|---|---|
| MCI | Master Connection Interface，每个 Master 经 MCI 接入 |
| SCI | Slave Connection Interface，每个 Slave 经 SCI 接入 |
| Arbiter | 当多个 Master 访问同一 Slave 时仲裁 |
| Crossbar | 允许不同 Master 访问不同 Slave 时并行 |
| Domain | 一个 crossbar 覆盖的 master/slave 集合 |

系统理解：

```text
不同 Master 访问不同 Slave → 可并行
多个 Master 访问同一 Slave → 仲裁，产生等待和抖动
```

这就是分析 bus load 的核心。

---

## 4.3 AURIX SPB / FPI：中低速外设互连

SPB 基于 FPI protocol，主要用于中低速外设。

FPI 的关键特性包括：

- multiple bus masters；
- pipelined transactions；
- 32-bit address and data buses；
- 8/16/32-bit data transfers；
- 64/128/256-bit block transfers；
- slave-controlled wait state insertion；
- timeout detection and handling；
- atomic CPU operations；
- flexible arbitration schemes；
- starvation prevention；
- default slave；
- bus error / timeout debug capture；
- Master TAG ID and Supervisor Mode information；
- information integrity support。  
来源：fileciteturn5file8

系统工程师要注意：外设寄存器访问通常不是性能主路径，但它是**配置正确性、安全保护、错误响应和实时触发**的高风险路径。

例如：

```text
CPU 写 GTM/ADC/QSPI 控制寄存器 → SPB/FPI → peripheral slave
```

要关注：

- 寄存器写入是否有 wait state；
- 写入是否 posted；
- 是否支持 W1C / SET / CLR；
- 多 Master 访问同一外设是否串行；
- 外设 FIFO 是否能被 DMA 及时服务；
- bus error 是否能定位到具体外设。

---

## 4.4 AURIX Bridge：最容易被忽略的风险点

AURIX 中常见 bridge：

| Bridge | 方向 | 典型作用 |
|---|---|---|
| S2S | SRI domain → SRI domain | 跨 SRI domain |
| F2S / SFI_F2S | SPB/FPI → SRI | SPB master 访问 SRI resource |
| S2F / SFI_S2F | SRI → BBB/FPI | SRI master 访问 BBB resource |
| GTM bridge | AEI / GTM domain | GTM 内部 domain 访问 |

Bridge 的产品定义必须明确：

| 主题 | 必须明确 |
|---|---|
| 协议转换 | transaction type 如何映射？ |
| 位宽转换 | 32-bit 到 64-bit 是否合并？ |
| clock domain crossing | 同步还是异步？ |
| posted write | 写完成语义是什么？ |
| buffer depth | 写 buffer / read buffer 多深？ |
| ordering | 同一 Master 的多个 transaction 是否保序？ |
| error propagation | 后端错误是否返回源 Master？ |
| timeout | bridge 侧是否有 timeout？ |
| debug | 是否有 pointer/status/error capture？ |

AURIX 的 SFI_F2S 文档就给出了 FPI transaction 到 SRI transaction 的映射，例如 2-word block transfer 映射为 single double-word，4-word block transfer 映射为 2 transfers 的 block transfer request，8-word block transfer 映射为 4 transfers。  
来源：fileciteturn3file0

这类映射会直接影响性能和错误行为。

---

# 5. 系统工程师如何把“总线理解”转成产品需求

## 5.1 第一步：列 Master

车规 MCU 常见 Master：

| Master | 典型访问 |
|---|---|
| CPU0..CPUx | 取指、读写数据、外设配置 |
| DMA | RAM↔外设、RAM↔RAM、Flash/RAM 搬运 |
| HSM | 安全 RAM、mailbox、密钥相关访问 |
| Ethernet / CAN XL / PCIe 类 | 网络数据搬运 |
| GTM / ADC / Radar / SPU | 高实时数据流 |
| Debug / Trace | 片上访问、trace buffer |
| Boot ROM / SSW | 启动期间配置访问 |
| External master | EBU / 外部总线场景 |

必须定义：

```text
每个 Master 的最大带宽、访问粒度、burst 能力、优先级、权限属性、错误行为。
```

---

## 5.2 第二步：列 Slave

常见 Slave：

| Slave | 风险点 |
|---|---|
| PFLASH | 取指、擦写、wait state、prefetch |
| DFLASH | EEPROM emulation、写擦除 stall |
| SRAM bank | 多 Master 竞争、ECC、bank conflict |
| DSPR / PSPR / TCM | 本地确定性访问，通常不希望被外部打扰 |
| LMU / shared RAM | 多核共享热点，最容易成为瓶颈 |
| 外设 SFR | 权限、RMW、副作用、posted write |
| FIFO | DMA 服务不及时导致 underflow/overflow |
| HSM RAM / mailbox | 安全隔离和 timeout |
| Debug / trace RAM | 调试时不能破坏实时性 |

必须定义：

```text
每个 Slave 的端口数量、数据宽度、最大吞吐、最坏响应、ECC/EDC、访问保护、错误上报。
```

---

## 5.3 第三步：画访问矩阵

建议产品定义阶段必须输出 Master-Slave 矩阵。

示例：

| Master \ Slave | PFLASH | DSPR0 | LMU0 | SRAM1 | QSPI | CAN | HSM RAM | SMU |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| CPU0 | R/X | R/W | R/W | R/W | Cfg | Cfg | No | Cfg |
| CPU1 | R/X | No | R/W | R/W | Cfg | Cfg | No | Cfg |
| DMA0 | No | No | R/W | R/W | R/W | R/W | No | No |
| HSM | No | No | Mailbox | No | No | No | R/W | No |
| Debug | R/W | R/W | R/W | R/W | R/W | R/W | Policy | R/W |

矩阵要标注：

- 是否允许；
- 读 / 写 / 执行；
- 是否 cacheable；
- 是否允许 burst；
- 是否安全相关；
- 是否需要 SMU alarm；
- 是否允许 debug 访问。

---

## 5.4 第四步：定义典型和极限 traffic profile

只定义单点带宽没有意义。必须定义场景。

### Profile A：电机控制实时场景

```text
CPU0: 20 kHz FOC ISR, code in PSPR, data in DSPR
CPU1: 通信协议栈，访问 CAN / Ethernet buffer
DMA0: ADC result → RAM
DMA1: QSPI sensor → RAM
GTM: PWM / capture
HSM: 周期性 alive check
```

关注：

- CPU0 ISR jitter；
- ADC DMA 是否抢占 CPU0 数据路径；
- GTM / ADC 触发链延迟；
- LMU 共享变量访问最坏延迟。

### Profile B：通信峰值场景

```text
CAN FD / Ethernet / LIN / SPI 同时高负载
DMA 多通道搬运 RX/TX buffer
CPU 处理协议栈
```

关注：

- DMA 总带宽；
- SRAM bank 冲突；
- FIFO underflow / overflow；
- 中断风暴下 CPU 和 SPB 访问延迟。

### Profile C：OTA / Flash 编程场景

```text
CPU 执行 bootloader
通信接收数据
Flash 擦写 / 校验
CRC / HSM 验签
```

关注：

- Flash 读写冲突；
- 代码是否需要搬到 RAM 执行；
- DMA / CRC / HSM 与 Flash / SRAM 的竞争；
- reset / power loss 下数据一致性。

### Profile D：安全故障场景

```text
非法地址访问
权限违规
SRI EDC 错误
ECC double-bit error
posted write 后端失败
```

关注：

- 能否定位 Master；
- 是否触发 SMU；
- 软件 ISR 能否读取错误地址和错误类型；
- 错误反应时间是否满足 FDTI / FHTI。

---

## 5.5 第五步：给 IC 设计明确的需求项

下面是一组可以直接放进产品需求文档的模板。

### 5.5.1 拓扑需求

```text
REQ-BUS-TOP-001:
SoC interconnect shall separate high-bandwidth memory traffic and low/medium bandwidth peripheral register traffic.
```

```text
REQ-BUS-TOP-002:
CPU instruction fetch, CPU data access, DMA memory access, and high-bandwidth peripheral access shall not share a single blocking bus segment without arbitration/QoS control.
```

```text
REQ-BUS-TOP-003:
Shared RAM shall be split into multiple banks or slave ports to reduce CPU/DMA/multi-core contention.
```

### 5.5.2 延迟需求

```text
REQ-BUS-LAT-001:
Under defined worst-case DMA traffic, CPU0 access to local DSPR/TCM shall remain single-cycle or bounded within X cycles.
```

```text
REQ-BUS-LAT-002:
Under communication peak profile, CPU access to safety-related peripheral registers shall complete within X bus cycles or generate timeout/error.
```

```text
REQ-BUS-LAT-003:
The interconnect specification shall provide worst-case arbitration latency per master class and slave port.
```

### 5.5.3 带宽需求

```text
REQ-BUS-BW-001:
The interconnect shall support simultaneous CPU instruction fetch, DMA peripheral transfer, and shared RAM access according to the product traffic model.
```

```text
REQ-BUS-BW-002:
DMA burst length shall be configurable to balance throughput and CPU real-time latency.
```

```text
REQ-BUS-BW-003:
The product manual shall provide sustained bandwidth numbers for typical paths: CPU↔RAM, DMA↔RAM, DMA↔Peripheral, CPU↔Flash.
```

### 5.5.4 仲裁 / QoS 需求

```text
REQ-BUS-QOS-001:
Bus arbitration shall support at least fixed priority and round-robin, or an equivalent QoS mechanism.
```

```text
REQ-BUS-QOS-002:
Starvation prevention shall be provided for low-priority masters.
```

```text
REQ-BUS-QOS-003:
Real-time masters, such as control CPU, ADC/GTM data path, and safety monitor, shall be configurable to higher arbitration class.
```

### 5.5.5 访问保护需求

```text
REQ-BUS-PROT-001:
All bus transactions shall carry Master ID/TAG and privilege/security attribute.
```

```text
REQ-BUS-PROT-002:
Memory and critical peripheral register regions shall support access control based on Master ID/TAG.
```

```text
REQ-BUS-PROT-003:
DMA channels shall have configurable access permission and privilege attributes.
```

```text
REQ-BUS-PROT-004:
Access violation shall be recordable and shall support interrupt/SMU alarm escalation.
```

### 5.5.6 错误处理需求

```text
REQ-BUS-ERR-001:
Non-existing address access shall be handled by default slave or equivalent mechanism; indefinite bus hang is not allowed.
```

```text
REQ-BUS-ERR-002:
Bus protocol error, timeout, transaction ID error, address/data integrity error shall be distinguishable by software.
```

```text
REQ-BUS-ERR-003:
Error capture shall include Master ID/TAG, target slave, address, access direction, access size, privilege, and error type.
```

```text
REQ-BUS-ERR-004:
Safety relevant bus errors shall be routable to SMU alarm and software interrupt.
```

### 5.5.7 Bridge 需求

```text
REQ-BRIDGE-001:
All bus bridges shall document transaction mapping, data-width conversion, ordering rule, posted/non-posted write behavior, buffer depth, and error propagation rule.
```

```text
REQ-BRIDGE-002:
For posted writes, backend write failure shall not be silent; it shall be captured by the receiving slave or bridge and shall support interrupt/SMU alarm.
```

```text
REQ-BRIDGE-003:
For safety-related register writes across bridge, software shall have a way to confirm completion, such as read-back, write-complete flag, barrier, or non-posted access path.
```

### 5.5.8 Clock domain / CDC 需求

```text
REQ-CDC-001:
All cross-clock-domain bus paths shall be identified in the architecture document.
```

```text
REQ-CDC-002:
CDC bridge shall specify synchronization mode, maximum latency, buffer depth, overflow behavior, reset behavior, and diagnostic status.
```

```text
REQ-CDC-003:
If synchronizer bypass is supported, the required clock relationship shall be explicitly stated and protected against invalid configuration.
```

### 5.5.9 Cache / DMA 需求

```text
REQ-CACHE-001:
The MCU shall provide a recommended DMA coherent memory solution: non-cacheable region, cache maintenance instruction, or hardware coherency.
```

```text
REQ-CACHE-002:
The cache line size, write policy, allocation policy, and maintenance granularity shall be documented.
```

```text
REQ-CACHE-003:
If cacheable and non-cacheable aliases are supported, aliasing restrictions shall be documented.
```

### 5.5.10 可观测性 / 验证需求

```text
REQ-OBS-001:
The interconnect shall provide debug registers or trace hooks to observe bus error, timeout, and transaction source.
```

```text
REQ-OBS-002:
Performance counters for selected bus paths, such as transaction count, stall cycle, arbitration lost count, and bandwidth counter, should be provided.
```

```text
REQ-OBS-003:
System validation shall be able to inject illegal address, access protection violation, timeout, and ECC/EDC error to verify the fault reaction path.
```

---

# 6. 面向总线的基本知识清单

## 6.1 必须掌握的术语

| 术语 | 解释 | 系统关注点 |
|---|---|---|
| Master | 发起访问者 | 谁会制造总线负载 |
| Slave | 被访问资源 | 哪里会成为瓶颈 |
| Crossbar | 多主多从互连 | 是否支持并行访问 |
| Bus matrix | Master-Slave 连接矩阵 | 哪些路径存在 / 不存在 |
| Bridge | 跨协议/位宽/时钟域转换 | latency、ordering、error propagation |
| Burst | 一次事务多 beat | 带宽与实时性的权衡 |
| Beat | burst 中一次数据传输 | 数据效率计算 |
| Outstanding | 未完成事务数量 | 吞吐和复杂度 |
| Pipeline | 地址/数据/响应重叠 | 提高吞吐但增加调试复杂度 |
| Wait state | Slave 插入等待 | 访问延迟来源 |
| Timeout | 超时响应 | 防止系统 hang |
| Default slave | 响应非法地址 | 定位非法访问 |
| Posted write | 写先返回、后完成 | 触发类寄存器风险 |
| Non-posted write | 写真正完成才返回 | 延迟高但语义清晰 |
| Read after write | 写后读依赖 | 用于确认写完成 |
| Atomic | 不可被打断访问 | 多核锁、RMW |
| Master TAG | 访问来源 ID | 保护和诊断 |
| Privilege | 特权属性 | 用户/监管模式隔离 |
| CDC | 跨时钟域 | metastability、latency、reset |
| ECC / EDC | 数据/事务完整性 | 安全与诊断 |

---

## 6.2 总线负载公式

简单模型：

```text
某 Slave 负载 = 观察窗口内该 Slave 被事务占用的周期数 / 观察窗口总周期数
```

工程模型：

```text
Bus Load ≈ 请求频率 × 单次事务成本 × 竞争系数
```

其中单次事务成本包括：

```text
地址 phase + 仲裁等待 + 数据 beat + wait state + bridge latency + CDC latency + response
```

竞争系数取决于：

```text
是否多个 Master 访问同一个 Slave / Bridge / RAM bank / Flash interface
```

---

## 6.3 总线性能不是看单一指标

| 指标 | 解释 |
|---|---|
| Peak bandwidth | 理论峰值，一般难达到 |
| Sustained bandwidth | 长时间稳定可用带宽，更重要 |
| Latency | 单次访问延迟 |
| Jitter | 延迟抖动，实时控制最敏感 |
| Worst-case latency | 安全和实时设计核心 |
| Arbitration delay | 竞争导致的等待 |
| Service time | Slave 真正服务事务的时间 |
| Blocking time | 一个 Master 被其他 Master 阻塞的时间 |
| Utilization | 总线或 Slave 被占用比例 |
| Error latency | 故障检测和上报耗时 |

---

# 7. 典型架构风险和需求建议

## 7.1 多核共享 RAM 热点

### 风险

```text
CPU0 + CPU1 + CPU2 + DMA 同时访问 LMU0
```

结果：

- CPU load/store 延迟增加；
- ISR jitter 增大；
- DMA 完成时间变长；
- 通信 FIFO 可能 underflow / overflow；
- 多核共享锁等待变长。

### 需求建议

```text
1. Shared RAM 分 bank / 多端口。
2. 支持按 Master / Slave 配置仲裁优先级。
3. 提供 bus performance counter。
4. 软件架构要求控制任务用本地 RAM，共享数据才放 LMU。
```

---

## 7.2 DMA 长 burst 抢占 CPU

### 风险

DMA 长 burst 提高吞吐，但可能长时间占用 SRAM slave port。

### 需求建议

```text
1. DMA burst length 可配置。
2. 仲裁器支持高优先级 CPU request 降低等待。
3. 文档给出 DMA burst 对 CPU worst-case latency 的影响。
4. 系统验证 profile 必须覆盖 DMA peak traffic。
```

---

## 7.3 posted write 导致配置顺序错误

### 风险

```text
write CTRL_REG
write START_REG
```

如果 CTRL_REG 经过 posted bridge 延迟，START_REG 可能先被执行，导致外设用旧配置启动。

### 需求建议

```text
1. 安全/trigger 寄存器不建议 posted。
2. 提供 read-back / completion flag。
3. 软件要求写关键寄存器后读回。
4. 文档明确不同 bus path 的 ordering 规则。
```

---

## 7.4 CPU cache 与 DMA 不一致

### 风险

```text
CPU 写 TX buffer → 数据停在 DCache
DMA 从 RAM 读 → 读到旧数据
```

或：

```text
DMA 写 RX buffer → RAM 已更新
CPU DCache 命中旧 line → 读到旧数据
```

### 需求建议

```text
1. DMA buffer 放 non-cacheable memory。
2. 或提供标准 clean / invalidate 流程。
3. cache maintenance 按 cache line 对齐。
4. 文档明确 cacheable alias 使用限制。
```

---

## 7.5 非法访问无法定位 Master

### 风险

发现 bus error，但不知道是哪个 CPU、哪个 DMA channel、哪个外设 Master。

### 需求建议

```text
1. transaction 必须携带 Master TAG。
2. error capture 必须记录 Master TAG。
3. DMA channel 信息最好能通过 sideband 记录。
4. error ISR 能读取地址、方向、大小、权限、opcode。
```

---

# 8. 系统工程师和 IC 设计评审时应该问的问题

## 8.1 CPU 评审问题

| 问题 | 目的 |
|---|---|
| CPU 取指路径有哪些？PFLASH / PSPR / cache miss 分别多大延迟？ | 判断实时性 |
| 中断入口最小 / 最大延迟是多少？受 cache miss 影响吗？ | 判断 ISR 确定性 |
| 本地 RAM 是否真正绕开系统总线？ | 判断控制任务隔离 |
| atomic 操作是否跨多核有效？ | 判断 RTOS / lock |
| barrier 指令对哪些总线路径生效？ | 判断 ordering |
| cache line size / policy / maintenance 如何定义？ | 判断 DMA 一致性 |
| lockstep CPU 对 bus error / ECC error 的反应是什么？ | 判断 safety |

## 8.2 总线评审问题

| 问题 | 目的 |
|---|---|
| 有哪些 Master？每个 Master 的 TAG ID 是多少？ | 保护与诊断 |
| 有哪些 Slave？每个 Slave 接在哪个 bus/domain？ | 访问路径 |
| 哪些路径经过 bridge？bridge 是否 posted write？ | ordering 风险 |
| 哪些 bridge 是异步 CDC？最大延迟是多少？ | 实时性和 CDC |
| 仲裁策略是否可配置？支持 QoS 吗？ | 实时性 |
| 长 burst 是否会阻塞高优先级访问？ | jitter |
| 非法地址访问如何响应？ | 防 hang |
| timeout 阈值是否可配置？ | 故障控制 |
| bus error 是否能触发 SMU？ | ASIL |
| error capture 是否记录 Master / address / opcode？ | 量产定位 |
| 是否有 bus load / stall counter？ | 性能验证 |
| Debug master 是否会破坏实时性？ | 调试影响 |

---

# 9. 系统验证角度：总线相关测试应该怎么设计

## 9.1 测试不应只做“寄存器读写通”

总线测试应该覆盖：

| 类别 | 测试内容 |
|---|---|
| 功能 | 各 Master 访问各 Slave 的基本读写 |
| 权限 | user/supervisor、Master TAG、DMA 权限 |
| 非法访问 | reserved address、未实现地址、只读写入 |
| 性能 | 单 Master、双 Master、多 Master 压力 |
| 实时性 | DMA 压力下 ISR jitter |
| burst | 不同 burst length、对齐、不对齐、跨边界 |
| bridge | 跨 bridge 读写、posted write、后端 error |
| CDC | 异步时钟比变化、clock gate、reset domain |
| cache | DMA buffer cacheable/non-cacheable 对比 |
| safety | EDC/ECC/error injection、SMU alarm、trap |
| debug | error capture、trace、performance counter |

## 9.2 典型测试 CASE

### CASE-BUS-001：多 Master 同 Slave 竞争

```text
条件：CPU0、CPU1、DMA0 同时访问 LMU0
步骤：
1. CPU0 周期性读写 LMU0 中变量，记录访问周期。
2. CPU1 执行 memory copy 到 LMU0。
3. DMA0 执行 RAM→RAM 或 RAM→外设搬运，源/目的包含 LMU0。
4. 统计 CPU0 访问最大延迟、DMA 完成时间、ISR jitter。
预期：
1. 不产生 bus error。
2. 最大延迟满足需求。
3. 仲裁行为与优先级配置一致。
```

### CASE-BUS-002：posted write 完成语义

```text
条件：Master 经 bridge 写目标寄存器或 RAM
步骤：
1. 连续写配置寄存器和启动寄存器。
2. 加 read-back / barrier 与不加 read-back 对比。
3. 制造目标侧 error 或 buffer full。
预期：
1. 文档定义的 posted 行为可复现。
2. 后端错误可被目标侧捕获。
3. 安全相关软件流程能确认写完成。
```

### CASE-BUS-003：非法地址和 default slave

```text
条件：CPU / DMA 访问未实现地址
步骤：
1. CPU 访问 reserved region。
2. DMA 访问 reserved region。
3. 读取 error capture 寄存器。
预期：
1. 不出现总线永久 hang。
2. 触发 bus error / trap / SMU alarm。
3. 能定位 Master、地址、访问方向、错误类型。
```

### CASE-BUS-004：DMA 与 cache 一致性

```text
条件：DMA buffer 分别放 cacheable 和 non-cacheable region
步骤：
1. CPU 写 TX buffer，DMA 发送。
2. DMA 写 RX buffer，CPU 读取。
3. 分别测试无 cache maintenance、clean、invalidate、clean+invalidate。
预期：
1. non-cacheable region 无一致性问题。
2. cacheable region 必须按文档维护 cache。
3. 跨 cache line buffer 处理正确。
```

---

# 10. 对自研车规 MCU 的建议架构需求包

如果你们要定义一颗车规 MCU，建议至少输出以下文档 / 需求包：

| 文档 | 内容 |
|---|---|
| CPU Architecture Requirement | core、cache、MPU、interrupt、atomic、safety |
| Bus Architecture Requirement | topology、master/slave、bridge、QoS、CDC |
| Memory Architecture Requirement | flash、SRAM bank、TCM、cacheable/non-cacheable |
| Safety Architecture Requirement | SMU、ECC/EDC、bus error、FFI、ENDINIT |
| Security Architecture Requirement | HSM、debug lock、secure access、DMA restriction |
| Performance Model | traffic profile、带宽、latency、jitter |
| Protection Matrix | Master → Slave access control |
| Error Handling Spec | bus error、timeout、EDC/ECC、alarm mapping |
| Software Constraint Spec | cache maintenance、posted write、barrier、RMW |
| System Validation Plan | 压力、错误注入、实时性、FFI、CDC |

---

# 11. 最终方法论

系统工程师看 CPU / 总线，不是为了证明自己懂多少 RTL，而是为了避免产品定义只停留在参数表。

正确方法是：

```text
1. 从应用任务出发，而不是从 IP 参数出发。
2. 从 Master-Slave 访问路径出发，而不是笼统说“总线负载”。
3. 从最坏场景出发，而不是平均性能。
4. 从安全隔离出发，而不是只看功能跑通。
5. 从错误可诊断出发，而不是只要求“不能错”。
6. 从软件可用性出发，而不是只让硬件“理论支持”。
```

产品定义里的核心句式应该是：

```text
在某个明确的 traffic profile 下，
某个 Master 访问某个 Slave，
经过某个 bus/bridge/domain，
在某种 cache/MPU/权限配置下，
必须满足某个 latency/bandwidth/error reaction/diagnostic requirement。
```

这就是车规 MCU 系统工程师在 CPU / 总线架构上应该达到的深度。🧩

---

# 参考资料

1. `TC3xx User Manual part1.pdf`：On-Chip System Connectivity、SRI Fabric、SFI Bridge、FPI/SPB。  
2. `TC3xx User Manual part2.pdf`：GTM bridge、外设 FIFO / DMA / 同步异步配置等。  
3. `TC39x B-Step User Manual Appendix.pdf`：TC39x-B memory map、SRI/SPB/BBB address map、cached/non-cached segment、CPU/DLMU/EMEM 映射。  
4. `AURIXTC3xxSafetyManualv2.0.pdf`：SRI address map monitoring、SRI transaction integrity、SV_AP、bus-level protection、SMU alarm。  

