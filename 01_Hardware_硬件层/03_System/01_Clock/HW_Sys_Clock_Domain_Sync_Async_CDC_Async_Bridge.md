# 车规 MCU 中同步时钟、异步时钟与异步桥理解笔记

> 适用对象：车规 MCU 系统工程师 / IP 测试工程师 / SoC 验证工程师  
> 核心主题：Clock Domain、CDC、Async Bridge、RTC/CAN/ADC/Debug/HSM 等具体案例

---

## 1. 核心结论

车规 MCU 里常说的 **同步时钟、异步时钟、异步桥**，本质是在讲：

> 两个硬件模块之间传递信号时，它们的时钟是否存在确定的频率关系和相位关系。

这会直接影响：

- 信号能否直接采样；
- 寄存器写入是否立即生效；
- 是否需要 CDC；
- 总线访问是否需要等待；
- 低功耗、复位、时钟切换时是否有特殊行为；
- 芯片验证是否需要专门覆盖跨时钟域场景。

---

## 2. 同步时钟是什么？

### 2.1 定义

如果两个时钟来自***<u>同一个时钟源，并且存在固定频率关系和可分析的相位关系</u>***，一般认为是 **同步时钟**。

例如：

```text
PLL_CLK = 160 MHz
    ↓
CPU_CLK = 160 MHz
AHB_CLK = 160 MHz
APB_CLK = 80 MHz
```

CPU_CLK、AHB_CLK、APB_CLK 都来自同一个 PLL，只是经过分频。  
如果分频关系固定、相位关系可控，那么它们通常属于同步时钟域。

---

### 2.2 典型案例：CPU 访问 APB 外设

假设：

```text
CPU_CLK / AHB_CLK = 160 MHz
APB_CLK           = 80 MHz
```

CPU 通过 AHB/APB Bridge 访问 UART、SPI、WDT、GPIO 等外设寄存器：

```text
Cortex-M7
   ↓ AHB Bus, 160 MHz
AHB-to-APB Bridge
   ↓ APB Bus, 80 MHz
UART / SPI / GPIO / WDT
```

虽然 AHB 和 APB 频率不同，但二者来自同一个 PLL，频率关系固定：

```text
160 MHz : 80 MHz = 2 : 1
```

因此 APB Bridge 可以按确定节拍完成访问。

CPU 写 UART 寄存器时，典型过程是：

```text
CPU/AHB 160 MHz 发起写访问
        ↓
AHB-to-APB Bridge 插入等待周期
        ↓
APB 80 MHz 完成寄存器写入
```

这类桥通常不叫异步桥，而更接近：

- 同步桥；
- 分频桥；
- 总线协议桥。

---

## 3. 异步时钟是什么？

### 3.1 定义

如果两个时钟没有固定相位关系，或者来自不同振荡源 / PLL，通常认为是 **异步时钟**。

典型例子：

```text
SYSCLK  = 160 MHz，来自主 PLL
RTC_CLK = 32.768 kHz，来自外部低速晶振
```

这两个时钟不是同一个源：

```text
高速系统时钟：PLL / HSE / HSI
低速 RTC 时钟：LSE 32.768 kHz
```

二者没有稳定相位关系，因此属于异步时钟域。

---

### 3.2 即使频率相同，也可能异步

例如：

```text
CLK_A = 80 MHz，来自 PLL1
CLK_B = 80 MHz，来自 PLL2
```

虽然频率都是 80 MHz，但如果它们来自两个独立 PLL，相位漂移不可控，那么仍然属于异步时钟。

所以判断同步 / 异步，不是只看频率，而是看：

> 是否同源、是否有固定相位关系、STA 是否可以完整分析。

---

## 4. 为什么异步时钟危险？

异步时钟域之间直接传信号，会遇到 **亚稳态 metastability** 问题。

假设 A 时钟域产生一个信号：

```text
A_CLK 域：signal_a
```

B 时钟域直接采样：

```text
B_CLK 域：signal_b <= signal_a
```

如果 signal_a 正好在 B_CLK 采样边沿附近变化，那么 B 域触发器可能进入亚稳态：

```text
          B_CLK 采样边沿
              ↓
signal_a  ____/‾‾‾‾‾
              ↑
          刚好变化
```

可能后果：

- 采到 0；
- 采到 1；
- 输出短时间不稳定；
- 后级逻辑误判；
- 状态机跑飞。

[**所以异步时钟域之间不能随便拉线，必须做 CDC，Clock Domain Crossing。**]()

---

## 5. CDC 是什么？

CDC 是 **Clock Domain Crossing**，即跨时钟域处理。

根据传输信号类型不同，CDC 方式也不同。

---

### 5.1 单 bit 控制信号：两级同步器

例如外设发出中断请求到 CPU 域：

```text
Peripheral_CLK 域 interrupt_raw
        ↓
两级触发器同步
        ↓
CPU_CLK 域 interrupt_sync
```

结构类似：

```text
interrupt_raw ──▶ DFF ──▶ DFF ──▶ interrupt_sync
                 CPU_CLK  CPU_CLK
```

适合：

- 单 bit enable；
- interrupt level；
- status flag；
- wakeup request；
- reset done flag。

---

### 5.2 脉冲信号：不能直接同步

如果 A 域产生一个很窄的 pulse：

```text
A_CLK 域：  ___|‾|___
```

B_CLK 比较慢时，可能完全采不到。

例如：

```text
A_CLK = 160 MHz
B_CLK = 32 kHz
```

A 域一个 1-cycle pulse 只有 6.25 ns。  
B 域一个周期约 30.5 μs。  
这个 pulse 大概率会丢失。

所以脉冲跨域通常要变成：

- level flag；
- toggle 信号；
- request/ack handshake；
- sticky status。

典型方式：

```text
A 域产生事件 → 置位 event_flag
B 域看到后处理 → 返回 ack
A 域收到 ack 后清 flag
```

---

### 5.3 多 bit 数据：不能每一位简单同步

比如 8 bit 数据：

```text
data[7:0]
```

如果每一位都用两级同步器，可能出现数据撕裂。

例如：

```text
旧数据：0x3F = 0011_1111
新数据：0x40 = 0100_0000
```

B 域可能采到错误中间值：

```text
0x00、0x7F、0x2F 等
```

所以多 bit 数据跨域一般使用：

- 握手协议；
- 异步 FIFO；
- 双口 RAM；
- Gray code 计数器；
- shadow register。

---

## 6. 异步桥是什么？

**异步桥**是连接两个异步时钟域的桥接电路。

它解决的问题是：

> A 时钟域的总线访问、寄存器读写、数据传输，如何安全地进入 B 时钟域。

典型形式包括：

| 类型 | 典型用途 |
|---|---|
| 异步寄存器桥 | CPU 访问低速外设寄存器 |
| 异步 FIFO | 高速数据流跨域 |
| 异步总线桥 | AHB / AXI / APB 跨异步 clock domain |
| Mailbox / 双口 RAM | 多核 / HSM / 通信模块跨域 |
| Request/Ack Bridge | 控制命令跨域 |

---

## 7. 案例一：CPU 访问 RTC

这是最典型的异步桥案例。

### 7.1 时钟关系

```text
CPU/AHB_CLK = 160 MHz
RTC_CLK     = 32.768 kHz
```

结构：

```text
Cortex-M7 / AHB / APB Domain
        │
        │ 160 MHz
        ↓
RTC Async Bridge
        │
        │ 32.768 kHz
        ↓
RTC Counter / Calendar / Alarm
```

CPU 写 RTC 寄存器时，不能直接把写信号送进 RTC 域，因为两个时钟异步。

---

### 7.2 CPU 写 RTC_ALARM 的过程

假设 CPU 写 RTC_ALARM：

```c
RTC->ALARM = 0x0008_3000;
```

硬件内部可能不是立即写入，而是：

```text
Step 1：CPU/APB 域发起写请求
Step 2：异步桥锁存地址、数据、写使能
Step 3：通过 request/ack 跨到 RTC_CLK 域
Step 4：RTC_CLK 域真正写入 ALARM 寄存器
Step 5：RTC_CLK 域返回 ack
Step 6：APB 域释放 busy / write complete flag
```

简化图：

```text
APB_CLK 域                         RTC_CLK 域
160 MHz                            32.768 kHz

addr/wdata/write
      │
      ↓
  async bridge  ── request ──▶  RTC register write
      ▲                         │
      └────── ack  ◀────────────┘
```

---

### 7.3 为什么 RTC 寄存器经常有 busy 位？

因为写入 RTC 域需要等待低速时钟采样。

常见类似状态位：

```text
INITF
RSF
WUTWF
ALRAWF
SHPF
SYNCBUSY
WRITE_BUSY
```

本质都在表达：

> CPU 域已经写了，但 RTC 域还没有同步完成。

所以 RTC 测试中不能简单这样写：

```c
RTC->ALARM = value;

if (RTC->ALARM == value)
{
    pass;
}
```

更稳妥的方式是：

```c
RTC->ALARM = value;

while (RTC->SYNCBUSY != 0)
{
    /* wait */
}

readback = RTC->ALARM;
```

或者等待对应的 write complete flag。

---

### 7.4 RTC 异步桥对测试的影响

| 测试点 | 原因 |
|---|---|
| 写寄存器后不能立即判断 | RTC 域同步慢 |
| 需要 polling busy / sync flag | 异步桥有握手延迟 |
| RTC clock 停止时访问可能卡住或超时 | 目标时钟域不工作 |
| 低功耗唤醒要测跨域中断 | RTC 域唤醒 CPU 域 |
| reset 后 shadow register 可能需要重新同步 | CPU 读到的是镜像值 |

---

## 8. 案例二：CAN 模块

车规 MCU 中 CAN / CAN FD 经常涉及多个时钟域。

典型结构：

```text
CPU/AHB/APB clock domain
        │
        ↓
CAN register interface
        │
        ↓
CAN protocol engine clock domain
        │
        ↓
CAN bit timing / sample point
```

可能的时钟配置：

```text
PCLK       = 80 MHz，用于 CPU 访问 CAN 寄存器
CAN_CLK    = 40 MHz，用于 CAN 内核协议逻辑
CAN bit rate = 500 kbps / 2 Mbps / 5 Mbps
```

---

### 8.1 CPU 配置 CAN 位时序

CPU 可能会写：

```text
CAN_NBTP
CAN_DBTP
CAN_CCCR
CAN_TXBAR
```

这些写操作发生在 APB/PCLK 域。

但 CAN 协议引擎可能运行在 CAN_CLK 域。

所以内部可能需要：

```text
APB_CLK 域寄存器写入
        ↓
同步到 CAN_CLK 域
        ↓
CAN protocol engine 生效
```

---

### 8.2 为什么有些 CAN 配置必须在 INIT 模式下改？

很多 CAN 控制器要求：

```text
进入 INIT 模式
    ↓
配置 bit timing / filter / mode
    ↓
退出 INIT 模式
```

一个重要原因是：

> CAN 协议引擎正在运行时，直接修改跨域配置可能导致协议状态机异常。

因此硬件要求软件先进入受控状态，再同步配置。

这既是软件使用规范，也是硬件跨时钟域安全设计。

---

### 8.3 CAN Message RAM 也可能跨域

典型结构：

```text
CPU 通过 AHB 访问 Message RAM
CAN 协议引擎也访问 Message RAM
```

例如：

```text
CPU 写 Tx Buffer
        ↓
设置 TX request
        ↓
CAN engine 读取 Tx Buffer
        ↓
发送 CAN frame
```

这里需要处理：

- CPU 域写 buffer；
- CAN 域读取 buffer；
- 请求位跨域；
- 完成状态跨域；
- 中断跨域。

简化图：

```text
CPU/AHB 域                         CAN_CLK 域

写 Tx Buffer
设置 TXBAR bit  ──sync/handshake──▶ CAN engine 读取并发送
                                      │
中断/完成标志 ◀──sync/handshake──────┘
```

所以测试 CAN 时，写完 TX request 后不能假设下一条指令时已经发送完成。  
需要等待：

```text
TX complete flag
TX event FIFO
interrupt status
```

---

## 9. 案例三：ADC

ADC 也是典型跨域模块。

### 9.1 时钟结构

```text
CPU/AHB/PCLK = 160 MHz / 80 MHz
ADC_CLK      = 20 MHz
ADC analog sampling clock 可能还会继续分频
```

结构：

```text
CPU/PCLK domain
      │
      ↓
ADC register interface
      │
      ↓
ADC conversion domain
      │
      ↓
analog frontend
```

---

### 9.2 CPU 启动转换

CPU 写：

```c
ADC->START = 1;
```

实际过程：

```text
PCLK 域写 START
        ↓
跨域同步到 ADC_CLK 域
        ↓
ADC sequencer 启动采样
        ↓
转换完成
        ↓
EOC flag 跨回 PCLK/CPU 域
        ↓
CPU 读结果寄存器
```

图：

```text
PCLK 域                         ADC_CLK 域

START bit  ──同步/握手──────▶  ADC sequencer start
                                │
EOC flag   ◀──同步/握手──────  conversion done
RESULT     ◀──shadow/FIFO────  conversion data
```

---

### 9.3 为什么 ADC 结果经常放 FIFO？

因为 ADC 结果是多 bit 数据，比如 12 bit、16 bit。  
多 bit 数据跨域不能每一位裸同步，所以常用：

```text
ADC result FIFO
ADC result data register shadow
DMA buffer
```

测试时要注意：

| 场景 | 关注点 |
|---|---|
| start 后立即读 result | 可能读到旧值 |
| EOC flag 清除 | 清除动作也可能跨域 |
| DMA 搬运 ADC 数据 | DMA 时钟域和 ADC 时钟域之间需要 FIFO / 握手 |
| clock stop | ADC 转换域停止后，状态位可能不更新 |

---

## 10. 案例四：Debug / JTAG / SWD

调试接口几乎一定是异步的。

例如：

```text
JTAG_TCK / SWDCLK：来自调试器
CPU_CLK：来自 MCU 内部 PLL
```

结构：

```text
External Debugger
      │ TCK/SWDCLK
      ↓
DAP / Debug Port
      │ async bridge
      ↓
System bus / CPU debug logic
      │ CPU_CLK / AHB_CLK
      ↓
Core / Memory / Peripheral
```

调试器的 SWDCLK 是外部来的，不可能和 MCU 内部系统时钟同步。  
所以 DAP 到系统总线之间必须有异步处理。

这也解释了为什么：

- 调试器访问寄存器有等待；
- CPU halt 状态下仍能访问部分资源；
- 某些低功耗模式下 debug 访问会失败；
- debug clock、system clock、bus clock 之间需要专门桥接。

---

## 11. 案例五：HSM / 安全岛 / 独立子系统

车规 MCU 常有 HSM、Safety Island、Always-on Domain。

例如：

```text
Application CPU domain：200 MHz
HSM domain：100 MHz 或独立 PLL
AON/RTC domain：32 kHz
Debug domain：外部 TCK
```

结构：

```text
CPU Domain
    │
    ↓
Interconnect / Firewall / Bridge
    │
    ↓
HSM Domain
```

如果 HSM 使用独立时钟，那么 CPU 访问 HSM mailbox、crypto engine、key RAM 时，就需要异步桥。

典型访问：

```text
CPU 写 HSM command mailbox
        ↓
异步桥同步到 HSM 域
        ↓
HSM 执行 AES/SHA/secure boot 服务
        ↓
HSM 写 response mailbox
        ↓
状态/中断同步回 CPU 域
```

所以 HSM 类模块经常有：

```text
BUSY
READY
CMD_VALID
RESP_VALID
IRQ
TIMEOUT
ACCESS ERROR
```

这些信号很多都和跨域握手有关。

---

## 12. 同步桥 vs 异步桥

### 12.1 同步桥

例如：

```text
AHB 160 MHz → APB 80 MHz
```

如果两个时钟同步同源：

```text
HCLK = 160 MHz
PCLK = HCLK / 2
```

桥主要解决：

- 总线协议转换；
- 数据宽度转换；
- 等待周期插入；
- 地址译码；
- byte enable 转换。

它不重点解决亚稳态。

示意：

```text
AHB_CLK 160 MHz
    ↓
AHB-to-APB Bridge
    ↓
APB_CLK 80 MHz，同源同步
```

---

### 12.2 异步桥

例如：

```text
AHB 160 MHz → RTC 32.768 kHz
```

桥需要解决：

- 总线协议转换；
- request/ack 跨域；
- 数据保持；
- busy/ready 反馈；
- 亚稳态风险；
- 目标时钟停止时的 timeout；
- reset domain 不一致。

示意：

```text
AHB_CLK 160 MHz
    ↓
Async Bridge
    ↓
RTC_CLK 32.768 kHz，异步
```

---

## 13. 一个完整异步桥访问例子：CPU 读 RTC_COUNTER

### 13.1 错误设计：CPU 直接读 RTC_COUNTER

```text
CPU 直接读取 RTC_COUNTER[31:0]
```

问题：

```text
RTC_COUNTER 可能正在 32 kHz 域变化
CPU 160 MHz 随机采样
```

例如 RTC counter 从：

```text
0x0000_FFFF
```

跳到：

```text
0x0001_0000
```

CPU 可能读到错误中间值：

```text
0x0001_FFFF
0x0000_0000
```

这就是多 bit 跨域错误。

---

### 13.2 正确设计：shadow register

常见做法：

```text
RTC_CLK 域 counter
        ↓
同步/锁存
        ↓
SYSCLK 域 shadow register
        ↓
CPU 读取 shadow register
```

结构：

```text
RTC_CLK 域                         SYSCLK 域

RTC_COUNTER[31:0] ──capture────▶ RTC_COUNTER_SHADOW
                                  │
CPU read ◀───────────────────────┘
```

所以 CPU 实际读到的可能不是 RTC 计数器的瞬时值，而是一个同步后的镜像值。

这就是为什么很多 RTC 有：

```text
RSF: Register Synchronization Flag
```

或者要求：

```text
clear RSF
wait RSF set
read calendar register
```

---

## 14. 车规 MCU 中常见时钟域划分

一个 MCU 内部可能有这些 clock domain：

```text
Core domain          CPU / FPU / NVIC
System bus domain    AHB / AXI / interconnect
Peripheral domain    APB / peripheral register
Flash domain         Flash controller / ECC
SRAM domain          RAM / ECC / bus wrapper
RTC/AON domain       RTC / wakeup / backup registers
Analog domain        ADC / comparator / PLL monitor
Communication domain CAN / Ethernet / USB / QSPI
Debug domain         JTAG / SWD / trace
Safety domain        SMU / FCCU / safety island
HSM domain           Crypto / secure boot
```

有些是同步的，有些是异步的。

| 模块 | 常见时钟关系 | 是否可能异步 |
|---|---:|---|
| CPU 与 AHB | 同源 | 通常同步 |
| AHB 与 APB | 同源分频 | 通常同步 |
| CPU 与 RTC | PLL vs 32.768 kHz | 异步 |
| CPU 与 ADC | PCLK vs ADC clock | 常见跨域 |
| CPU 与 CAN protocol engine | PCLK vs CAN kernel clock | 可能异步 |
| CPU 与 Debug TCK | 内部 PLL vs 外部调试器 | 异步 |
| CPU 与 HSM | 不同 PLL / 分频 / 电源域 | 可能异步 |
| CPU 与 AON wakeup | 高速系统域 vs always-on 低速域 | 异步 |

---

## 15. 软件 / 测试人员如何判断是否存在异步桥或 CDC？

看规格书时，看到以下关键词，通常说明存在跨时钟域：

| 关键词 | 含义 |
|---|---|
| sync | 需要同步 |
| synchronization flag | 同步完成标志 |
| busy | 目标域还没完成 |
| write pending | 写入挂起 |
| shadow register | 影子寄存器，跨域镜像 |
| update flag | 更新完成 |
| clock domain | 时钟域 |
| kernel clock | 模块内核时钟，可能不同于 bus clock |
| functional clock | 外设功能时钟 |
| register clock | 寄存器接口时钟 |
| timeout | 目标域无响应时防止总线卡死 |
| handshake | 请求 / 应答 |
| async bridge | 异步桥 |
| CDC | 跨时钟域 |

---

## 16. 对测试需求设计的影响

如果模块里有异步桥，测试时不能只做普通寄存器读写。

需要额外考虑以下场景。

---

### 16.1 时钟打开 / 关闭场景

例如：

```text
CPU 访问 RTC
RTC clock enabled  → 正常访问
RTC clock disabled → busy 不清 / timeout / bus error
```

测试点：

```text
1. 目标时钟开启时访问正常
2. 目标时钟关闭时访问行为符合规格
3. 重新开启目标时钟后访问恢复
```

---

### 16.2 写后同步延迟

例如：

```text
write register
immediate readback
```

可能读不到新值。

正确测试：

```text
write register
wait sync done / busy clear
readback check
```

---

### 16.3 中断跨域

例如 RTC alarm 唤醒 CPU：

```text
RTC_CLK 域产生 alarm event
        ↓
同步到 CPU/NVIC 域
        ↓
触发 interrupt / wakeup
```

测试点：

```text
1. alarm event 是否能跨域触发中断
2. 清中断 flag 是否能跨回 RTC 域
3. 连续 event 是否丢失
4. 低功耗下 wakeup 是否可靠
```

---

### 16.4 reset domain 不一致

异步桥两边可能 reset 不同步：

```text
SYS reset
RTC backup domain 不 reset
```

或者：

```text
Peripheral reset
Bus domain 不 reset
```

测试点：

```text
1. 只复位 bus domain 后，目标域寄存器是否保持
2. 只复位 peripheral domain 后，CPU 读到什么
3. 复位释放后是否需要重新同步
```

---

## 17. RTC 异步访问测试需求示例

RTC 的测试需求可以按以下方向拆分：

| 测试项 | 目的 |
|---|---|
| RTC clock enable 后访问寄存器 | 验证异步桥正常 |
| 写 RTC 配置后 polling busy | 验证写同步完成机制 |
| RTC counter 读同步 | 验证 shadow register 更新 |
| RTC clock stop 时访问 | 验证 timeout / busy 行为 |
| RTC alarm interrupt | 验证 RTC → CPU 跨域事件 |
| 清 alarm flag | 验证 CPU → RTC 跨域清除 |
| sleep 后 RTC wakeup | 验证 AON/RTC → system domain 唤醒链路 |
| backup domain reset | 验证 reset domain 与 sync 关系 |

这类测试比普通寄存器读写更接近真实风险点。

---

## 18. 总结

### 18.1 同步时钟

两个模块时钟同源、有固定相位 / 频率关系，可以直接做时序分析。

典型例子：

```text
CPU_CLK = 160 MHz
AHB_CLK = 160 MHz
APB_CLK = 80 MHz
```

同步桥主要解决：

- 协议转换；
- 频率分频；
- 等待周期；
- 数据宽度转换。

---

### 18.2 异步时钟

两个模块时钟无固定相位关系，信号不能直接传，必须做 CDC。

典型例子：

```text
CPU/AHB/APB 高速系统域
        ↓
RTC 32.768 kHz 低速域
```

---

### 18.3 异步桥

异步桥专门连接两个异步时钟域，常用机制包括：

- request/ack；
- shadow register；
- async FIFO；
- dual-port RAM；
- mailbox；
- sticky flag；
- timeout。

---

## 19. 车规 MCU 中最典型的异步桥场景

```text
CPU/AHB/APB 高速系统域
        ↓ 异步桥
RTC 32.768 kHz 低速域
```

以及：

```text
CPU 域 ↔ CAN 内核域
CPU 域 ↔ ADC 转换域
CPU 域 ↔ Debug TCK 域
CPU 域 ↔ HSM / 安全岛域
CPU 域 ↔ AON / 低功耗域
```

---

## 20. 实战判断口诀

看规格书时，只要看到下面这些词，就要警惕这里可能不是简单寄存器逻辑，而是有跨时钟域 / 异步桥设计：

```text
busy
sync
shadow
kernel clock
functional clock
write pending
clock domain
timeout
handshake
CDC
async bridge
```

对应测试上要优先想到：

```text
写后等待
读影子寄存器
目标时钟关闭
中断跨域
低功耗唤醒
复位域不一致
连续事件是否丢失
timeout / bus error 行为
```

---

## 21. 一句话版本

**同步时钟**：同源、有固定相位 / 频率关系，可以做确定时序分析。  
**异步时钟**：不同源或无固定相位关系，直接采样有亚稳态风险。  
**异步桥**：用于安全连接两个异步时钟域，靠 CDC、握手、FIFO、shadow register 等机制保证访问可靠性。

