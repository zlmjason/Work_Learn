# AUTOSAR 多核数据一致性与多核间通信：Why / What / How

> 视角：AUTOSAR Classic Platform + 车规 MCU 系统工程  
> 例子：AURIX TC3xx 为主，ARM Cortex‑M7 系列作为对比  
> 关键词：RTE、IOC、OS Spinlock、SchM、Exclusive Area、IRV、LMU、Cache、Barrier、Inter-core Interrupt

---

## 0. 先给结论

在 AUTOSAR Classic 多核系统里，**多核数据一致性**和**多核间通信**是两个不同但强相关的问题。

- **多核数据一致性**解决的是：  
  多个执行上下文同时访问同一份数据时，如何保证数据不会被写坏、读旧、读半包、乱序可见。

- **多核间通信**解决的是：  
  Core0 上的软件实体如何把数据、事件、服务请求传递给 Core1 上的软件实体，并让接收方在正确的时机处理。

AUTOSAR 的设计思路不是让应用代码到处写共享全局变量，而是：

```text
SWC 间通信             → RTE
跨 OS-Application/Core → IOC
同核共享资源           → OS Resource / interrupt lock / Exclusive Area
跨核共享资源           → OS Spinlock / IOC / vendor-specific lock
BSW 模块内部互斥       → SchM_Enter / SchM_Exit
底层硬件保证           → 原子指令、cache maintenance、barrier、MPU/SMPU、interrupt router
```

一句话：

> **能用 RTE/IOC 消息传递，就不要裸共享变量；必须共享变量，就要明确“互斥 + 可见性 + 顺序 + 生命周期”。**

---

## 1. 两个概念的边界

| 维度 | 多核数据一致性 | 多核间通信 |
|---|---|---|
| 核心问题 | 数据本身是否正确 | 数据/事件如何从一个核传到另一个核 |
| 关注点 | 原子性、互斥、可见性、顺序、cache 一致性 | 通信路径、队列、通知、阻塞/非阻塞、丢包、时序 |
| AUTOSAR 机制 | Exclusive Area、SchM、OS Resource、Spinlock、IRV、IOC 原子传输 | RTE Sender-Receiver、IOC、跨核中断、Task/Event 激活 |
| 典型错误 | counter++ 丢失、结构体半更新、读到旧 cache、flag 先到 data 后到 | 丢事件、队列溢出、通知早于数据可见、跨核服务死锁 |
| 设计倾向 | 减少共享，明确所有权 | 消息化、队列化、单向化 |

注意：**多核通信本身也需要数据一致性**。例如 Core0 把数据写入 LMU，再发跨核中断通知 Core1；如果没有 cache clean/barrier，Core1 可能先收到中断，但读到旧数据。

---

# Part A：多核数据一致性

---

## 2. Why：为什么需要多核数据一致性？

### 2.1 单核时代的问题已经存在，多核会放大

即使单核也有并发：

```text
Task A
ISR
Task B
DMA
```

多核后并发来源变成：

```text
Core0 Task / ISR
Core1 Task / ISR
Core2 Task / ISR
DMA / GTM / Ethernet DMA / HSM
```

问题不再是“会不会被中断打断”这么简单，而是多个 Master 可以真正同时访问同一片 SRAM、同一个外设寄存器、同一个软件状态机。

---

### 2.2 典型错误 1：Read-Modify-Write 丢失更新

错误代码：

```c
/* Core0 */
SharedCounter++;

/* Core1 */
SharedCounter++;
```

`counter++` 在 C 语义上是一句，但底层通常是：

```text
load counter
add 1
store counter
```

如果两个核同时执行：

```text
初始 counter = 10

Core0 load 10
Core1 load 10
Core0 store 11
Core1 store 11

期望 12，实际 11
```

这就是典型的 RMW race。

---

### 2.3 典型错误 2：结构体半更新

```c
typedef struct
{
    uint32 seq;
    uint32 speed;
    uint32 torque;
    uint32 crc;
} SharedSignal_t;

/* Core0 写 */
gSig.seq++;
gSig.speed = 100;
gSig.torque = 200;
gSig.crc = CalcCrc(&gSig);

/* Core1 读 */
local = gSig;
```

Core1 可能读到：

```text
seq    = 新
speed  = 新
torque = 旧
crc    = 旧
```

这不是“变量类型加 volatile”能解决的问题。`volatile` 只限制编译器优化，不提供跨核互斥，也不自动处理 cache。

---

### 2.4 典型错误 3：flag 已经置位，但 data 还不可见

```c
/* Core0 */
shared.data = 0x12345678;
shared.ready = 1;

/* Core1 */
if (shared.ready == 1)
{
    value = shared.data;
}
```

在弱内存顺序、写缓冲、cache 存在时，Core1 可能看到 `ready == 1`，但 `data` 还是旧值。  
所以需要 **memory barrier / cache clean / cache invalidate** 来保证“写 data 先于写 flag 可见”。

---

### 2.5 典型错误 4：Cache 不一致

多核和 DMA 里最容易出问题的是：

```text
CPU cache 中有一份数据
RAM 中有另一份数据
DMA/另一个 Core 访问的是 RAM
当前 Core 访问的是 cache
```

如果没有硬件 cache coherency，就必须软件维护：

```text
Producer 写数据后：
    clean/writeback cache
    DSB/DMB/DSYNC

Consumer 读数据前：
    invalidate cache
    DSB/DMB/DSYNC
```

AURIX TC3xx 的 TriCore 架构支持数据 cache 操作指令，例如 `CACHEA.I` 地址失效、`CACHEI.W` 按 index/way 写回、`CACHEI.I` 按 index/way 失效等；这些指令通常只能在 Supervisor 模式执行。AURIX 文档也明确提到 PCACHE 没有自动 cache coherency，外部 memory 内容变化不会自动被已缓存的 PCACHE 感知，需要软件做一致性处理。TC3xx 的性能计数器里也能看到 DCACHE hit/miss/dirty writeback 等事件，说明 cache 行为是系统性能和一致性分析的重要对象。

---

## 3. What：多核数据一致性到底包含什么？

数据一致性不是一个点，而是一组属性。

| 属性 | 含义 | 例子 |
|---|---|---|
| 原子性 Atomicity | 一个操作不能被拆开观察 | 32-bit flag 一次写入；RMW 操作用原子指令 |
| 互斥 Mutual Exclusion | 同一时刻只有一个执行实体进入临界区 | Spinlock 保护共享状态机 |
| 可见性 Visibility | 一个核写的数据，另一个核能看到 | clean cache + barrier |
| 顺序 Ordering | data 必须先于 flag 可见 | 写 data → barrier → 写 ready |
| 一致快照 Consistent Snapshot | 读到的一组数据来自同一版本 | seq-lock / double buffer |
| 生命周期 Lifetime | 发送方不能提前复用 buffer | DMA descriptor / IOC buffer |
| 完整性 Integrity | 数据没有损坏或串包 | CRC、E2E Profile、counter、timeout |

---

## 4. AUTOSAR 规范视角下的 What

### 4.1 RTE：应用通信和数据访问抽象层

AUTOSAR Classic 的 RTE 是应用 SWC 和 BSW/OS 之间的核心抽象。SWC 理论上不应该知道对端在本核、别核，还是别 ECU。应用只看到：

```c
Rte_Write_PpSpeed_Speed(&speed);
Rte_Read_RpTorque_Torque(&torque);
Rte_Call_Server_DoSomething(...);
```

RTE Generator 根据系统配置决定底层是：

```text
同 Runnable 内部访问          → 直接变量
同 SWC Runnable 间访问        → IRV / RTE buffer
同核不同 Task                → RTE buffer + Exclusive Area
跨 OS-Application / 跨 Core  → IOC
跨 ECU                      → COM / PduR / BusIf / Driver
```

---

### 4.2 Exclusive Area：RTE 层临界区

SWC 的 Runnable 如果需要保护共享资源，可以声明 Exclusive Area：

```c
void Runnable_10ms(void)
{
    Rte_Enter_EA_State();

    gState.counter++;
    gState.valid = TRUE;

    Rte_Exit_EA_State();
}
```

配置含义：

```text
RunnableEntity.canEnter → ExclusiveArea
```

底层实现由 RTE/OS/vendor 决定，可能是：

```text
SuspendAllInterrupts
SuspendOSInterrupts
OS Resource
OS Spinlock
自定义关核内抢占
自定义硬件锁
```

核心点：  
**Exclusive Area 是建模抽象，不等价于具体锁。**

---

### 4.3 SchM Exclusive Area：BSW/MCAL 模块内部保护

BSW 模块不直接调用 `Rte_Enter`，而是使用 SchM：

```c
SchM_Enter_Can_CAN_EXCLUSIVE_AREA_0();

/* 修改 Can Driver 内部全局状态、Controller 状态、队列 */

SchM_Exit_Can_CAN_EXCLUSIVE_AREA_0();
```

生成后可能映射为：

```c
void SchM_Enter_Can_CAN_EXCLUSIVE_AREA_0(void)
{
    GetSpinlock(OsSpinlock_Can);
}

void SchM_Exit_Can_CAN_EXCLUSIVE_AREA_0(void)
{
    ReleaseSpinlock(OsSpinlock_Can);
}
```

如果这个 Can Driver 只在一个 core 上运行，可能只需要 SuspendOSInterrupts 或 OS Resource。  
如果多个 core 都会调用同一个 Driver 的 API，才需要跨核 Spinlock 或采用 master-satellite 架构。

---

### 4.4 OS Resource vs OS Spinlock

AUTOSAR OS 明确区分：

| 机制 | 适用范围 | 行为 |
|---|---|---|
| OS Resource | 同一个 Core 内任务/ISR 互斥 | 依赖优先级天花板等本地调度机制 |
| OS Spinlock | 跨 Core 互斥 | 获取不到就 busy wait |
| IOC | 跨 OS-Application/Core 通信 | 消息传输，不暴露共享变量 |

关键差异：

```text
OS Resource 不能跨 Core 使用。
Spinlock 可以跨 Core，但会 busy wait，影响实时性。
IOC 更偏通信，不要求应用直接处理共享内存锁。
```

---

### 4.5 IOC：通信同时保证传输操作的一致性

IOC 是 AUTOSAR OS 的 Inter-OS-Application Communicator。RTE 生成的跨 OS-Application / 跨 Core 通信通常会调用 IOC 函数：

```c
IocSend_SpeedToCore1(speed);
IocReceive_SpeedToCore1(&speed);
```

IOC 支持两种典型通信语义：

| 类型 | 语义 | 适合场景 |
|---|---|---|
| Unqueued IOC | Last-is-best，后写覆盖前写 | 周期性状态量，如转速、温度、状态字 |
| Queued IOC | FIFO，按顺序保存消息 | 事件、命令、诊断请求、服务请求 |

---

## 5. How：多核数据一致性怎么实现？

### 5.1 总体设计原则

优先级从高到低：

```text
1. 避免共享：每份数据只归属一个 core 或一个 SWC。
2. 消息传递优先：通过 RTE/IOC 传值，不共享变量。
3. 单写多读：一个 writer，多个 reader；reader 读快照。
4. 短临界区：必须共享时，临界区越短越好。
5. 明确 cache 策略：共享区要么 non-cacheable，要么严格 clean/invalidate。
6. 增加完整性保护：ASIL 数据加 counter、CRC、timeout、E2E。
```

---

### 5.2 实现模式 1：RTE Exclusive Area 保护 SWC 内共享状态

#### 场景

同一个 SWC 内两个 Runnable 访问同一个状态：

```text
Runnable_10ms：更新控制状态
Runnable_100ms：读取状态并上报诊断
```

#### 错误做法

```c
static uint32 gErrorCounter;
static boolean gValid;

void Runnable_10ms(void)
{
    gErrorCounter++;
    gValid = TRUE;
}

void Runnable_100ms(void)
{
    if (gValid)
    {
        Dem_Report(gErrorCounter);
    }
}
```

#### 推荐做法

```c
static uint32 gErrorCounter;
static boolean gValid;

void Runnable_10ms(void)
{
    Rte_Enter_EA_DiagState();

    gErrorCounter++;
    gValid = TRUE;

    Rte_Exit_EA_DiagState();
}

void Runnable_100ms(void)
{
    uint32 localCounter;
    boolean localValid;

    Rte_Enter_EA_DiagState();

    localCounter = gErrorCounter;
    localValid   = gValid;

    Rte_Exit_EA_DiagState();

    if (localValid)
    {
        Dem_Report(localCounter);
    }
}
```

#### How 要点

- 临界区内只做数据复制，不做耗时操作。
- 不要在 Exclusive Area 里调用可能阻塞的服务。
- 若 Runnable 可能分配到不同 core，则 Exclusive Area 需要映射到 Spinlock 或由 RTE 生成跨核保护。

---

### 5.3 实现模式 2：SchM + Spinlock 保护 BSW 全局状态

#### 场景

多个 core 上的应用都可能调用 CanIf/Can Driver：

```text
Core0：动力控制 SWC 发送 CAN
Core1：诊断 SWC 发送 CAN
共用同一个 CAN controller / Tx queue
```

#### BSW 代码风格

```c
Std_ReturnType Can_Write(Can_HwHandleType Hth, const Can_PduType* PduInfo)
{
    Std_ReturnType ret;

    SchM_Enter_Can_CAN_EXCLUSIVE_AREA_0();

    ret = Can_lPushTxQueue(Hth, PduInfo);

    SchM_Exit_Can_CAN_EXCLUSIVE_AREA_0();

    return ret;
}
```

#### 可能生成

```c
void SchM_Enter_Can_CAN_EXCLUSIVE_AREA_0(void)
{
    GetSpinlock(OsSpinlock_CanTxQueue);
}

void SchM_Exit_Can_CAN_EXCLUSIVE_AREA_0(void)
{
    ReleaseSpinlock(OsSpinlock_CanTxQueue);
}
```

#### How 要点

- Spinlock 保护的是软件队列/状态，不是 CAN 总线本身。
- Spinlock 内不要调用复杂路径，例如等待 mailbox 空、等待 Tx complete。
- 对于高负载通信模块，更推荐“一个 core 独占 driver，其他 core 通过 IOC 发送请求”。

---

### 5.4 实现模式 3：SeqLock / 版本号快照

#### 场景

一个 core 周期写共享数据，另一个 core 频繁读。  
读者不能阻塞 writer，writer 也不想用 Spinlock。

#### 数据结构

```c
typedef struct
{
    volatile uint32 seq;
    uint32 speed;
    uint32 torque;
    uint32 voltage;
} VehicleState_t;

volatile VehicleState_t gVehicleState;
```

#### Writer

```c
void Core0_UpdateVehicleState(void)
{
    gVehicleState.seq++;          /* odd: writing */

    __dsync();                    /* AURIX: ensure seq visible before data if required */

    gVehicleState.speed   = 100;
    gVehicleState.torque  = 200;
    gVehicleState.voltage = 350;

    __dsync();                    /* ensure data visible before final seq */

    gVehicleState.seq++;          /* even: stable */
}
```

#### Reader

```c
boolean Core1_ReadVehicleState(VehicleState_t* out)
{
    uint32 s1;
    uint32 s2;

    do
    {
        s1 = gVehicleState.seq;

        if ((s1 & 1u) != 0u)
        {
            continue;             /* writer is updating */
        }

        __dsync();

        out->speed   = gVehicleState.speed;
        out->torque  = gVehicleState.torque;
        out->voltage = gVehicleState.voltage;

        __dsync();

        s2 = gVehicleState.seq;

    } while (s1 != s2);

    return TRUE;
}
```

#### How 要点

- 适合单 writer、多 reader。
- 不适合多个 writer，多个 writer 仍要锁。
- cacheable 共享内存下仍需处理 cache clean/invalidate。
- 对 ASIL 数据建议加 CRC/counter，避免只靠 seq。

---

### 5.5 实现模式 4：双缓冲 + 原子索引切换

#### 场景

控制算法每 1ms 更新一组较大的结构体，另一个 core 每 10ms 读取。

#### 数据结构

```c
typedef struct
{
    uint32 speed;
    uint32 torque;
    uint32 crc;
} ControlFrame_t;

static ControlFrame_t gBuffer[2];
static volatile uint32 gActiveIndex;
```

#### Writer

```c
void Core0_WriteFrame(void)
{
    uint32 next = gActiveIndex ^ 1u;

    gBuffer[next].speed  = GetSpeed();
    gBuffer[next].torque = GetTorque();
    gBuffer[next].crc    = CalcCrc(&gBuffer[next]);

    __dsync();

    gActiveIndex = next;      /* 原子 32-bit store */
}
```

#### Reader

```c
boolean Core1_ReadFrame(ControlFrame_t* out)
{
    uint32 idx = gActiveIndex;

    __dsync();

    *out = gBuffer[idx];

    return CheckCrc(out);
}
```

#### How 要点

- Writer 只写非 active buffer。
- Reader 只读 active buffer。
- active index 必须是原子宽度且对齐。
- 对 Cortex-M7 / AURIX D-cache 场景，buffer 所在内存要做 cache 策略约束。

---

## 6. AURIX TC3xx 上怎么落地？

### 6.1 硬件背景

AURIX TC3xx 是多核 TriCore MCU，典型系统结构里包括：

```text
多个 TriCore CPU
每核 DSPR / PSPR / Cache
LMU / DLMU / DAM 等共享或局部 RAM
SRI / FPI 总线
DMA / HSM / GETH / GTM 等多个 Master
Interrupt Router / SRC
SMU / MPU / ENDINIT / Safety ENDINIT
```

TC3xx 用户手册说明，SoC 通信包括 SRI 和 FPI 两类 on-chip bus：SRI 是 crossbar based interconnect，64-bit data bus；FPI 是 multi-master interconnect，32-bit data bus。SRI 连接 TC1.6 CPU、高带宽外设、DMA 到本地资源，FPI 连接 CPU、DMA 到中低带宽外设。

---

### 6.2 AURIX 的原子操作

TriCore 架构支持一组原子内存操作：

```text
LDMST
SWAP.W
ST.T
CMPSWAP.W
SWAPMSK.W
```

其中：

- `SWAP.W` 可用于 test-and-set 类型二值信号量。
- `CMPSWAP.W` 可实现 compare-and-swap。
- 原子指令会强制完成语义上在它之前的数据访问，保证原子操作前的 buffered state 先写入内存。

这类指令是 OS Spinlock 的硬件基础之一。

#### AURIX 简化 Spinlock 思路

伪代码：

```c
typedef volatile uint32 OsRawSpinlockType;

boolean TryLock(OsRawSpinlockType* lock)
{
    uint32 old = 0u;
    uint32 new = 1u;

    /*
     * 底层可用 TriCore CMPSWAP.W / SWAP.W 实现。
     * 实际 AUTOSAR OS 不建议应用自己写锁，应使用 GetSpinlock。
     */
    return AtomicCompareAndSwap(lock, old, new);
}

void Unlock(OsRawSpinlockType* lock)
{
    __dsync();
    *lock = 0u;
}
```

应用层不要自己实现这个，AUTOSAR 下应使用：

```c
GetSpinlock(OsSpinlock_SharedResource);
/* critical section */
ReleaseSpinlock(OsSpinlock_SharedResource);
```

---

### 6.3 AURIX 共享内存建议：LMU / DLMU / DAM

跨核共享数据建议放在所有相关 Master 都可访问的区域，例如 LMU 或项目定义的 shared RAM section。

示意：

```c
#define SHARED_SEC_START_SEC_VAR_NOINIT_UNSPECIFIED
#include "MemMap.h"

volatile Mailbox_t g_Core0ToCore1_Mailbox;

#define SHARED_SEC_STOP_SEC_VAR_NOINIT_UNSPECIFIED
#include "MemMap.h"
```

链接脚本示意：

```ld
.lmu_shared (NOLOAD) :
{
    *(.lmu_shared*)
} > LMU_RAM
```

设计要求：

- 不要把共享区放在某个 core 私有 DSPR，除非明确知道其他 core 如何访问。
- 共享结构体按 cache line / natural alignment 对齐。
- 不同方向的数据尽量拆成不同 cache line，避免 false sharing。
- 如果 cache 打开：共享区优先配置为 non-cacheable；否则所有通信路径必须做 cache maintenance。

---

### 6.4 AURIX 跨核通信案例：LMU Mailbox + IOC/Spinlock + SRC 通知

#### 场景

Core0 的控制任务生成一帧状态，Core1 的诊断任务消费。

```text
Core0 Task_1ms
    写 LMU mailbox
    更新 seq/counter
    触发 Core1 service request

Core1 ISR / Task
    收到 service request
    读 LMU mailbox
    校验 counter/crc
    设置本地 RTE signal
```

#### 数据结构

```c
typedef struct
{
    uint32 counter;
    uint32 cmd;
    uint32 arg0;
    uint32 arg1;
    uint32 crc;
} IpcFrame_t;

typedef struct
{
    volatile uint32 valid;
    IpcFrame_t frame;
} LmuMailbox_t;

volatile LmuMailbox_t g_Core0ToCore1;
```

#### Core0 Producer

```c
void Core0_SendToCore1(uint32 cmd, uint32 arg0, uint32 arg1)
{
    GetSpinlock(OsSpinlock_IpcMailbox);

    g_Core0ToCore1.valid = 0u;

    g_Core0ToCore1.frame.counter++;
    g_Core0ToCore1.frame.cmd  = cmd;
    g_Core0ToCore1.frame.arg0 = arg0;
    g_Core0ToCore1.frame.arg1 = arg1;
    g_Core0ToCore1.frame.crc  = Ipc_CalcCrc(&g_Core0ToCore1.frame);

    __dsync();

    g_Core0ToCore1.valid = 1u;

    __dsync();

    ReleaseSpinlock(OsSpinlock_IpcMailbox);

    /*
     * 触发 Core1 中断/事件。
     * AUTOSAR 工程中通常不会让应用直接写 SRC，
     * 而是通过 OS / IOC / RTE 生成代码间接实现。
     */
    Ipc_TriggerCore1ServiceRequest();
}
```

#### Core1 Consumer

```c
void Core1_IpcNotification(void)
{
    IpcFrame_t local;

    GetSpinlock(OsSpinlock_IpcMailbox);

    if (g_Core0ToCore1.valid == 1u)
    {
        __dsync();

        local = g_Core0ToCore1.frame;
        g_Core0ToCore1.valid = 0u;
    }

    ReleaseSpinlock(OsSpinlock_IpcMailbox);

    if (Ipc_CheckCrc(&local))
    {
        Ipc_DispatchCommand(&local);
    }
}
```

#### 更 AUTOSAR 的写法

应用 SWC 不直接处理 mailbox，而是：

```c
/* Core0 SWC */
Rte_Write_PpDiagRequest_Request(&req);

/* RTE generated */
IocSend_DiagRequest_Core0ToCore1(req);

/* Core1 SWC */
Rte_Read_RpDiagRequest_Request(&req);
```

IOC/OS/RTE 负责：

```text
数据复制
必要的互斥
必要的通知
必要的错误返回
```

具体底层可能仍然是 shared RAM + spinlock + inter-core interrupt。

---

### 6.5 AURIX 外设寄存器共享：不要靠 Spinlock 硬抢外设

错误设计：

```text
Core0 直接配置 QSPI0 寄存器
Core1 也直接配置 QSPI0 寄存器
用一个 Spinlock 包起来
```

问题：

- 互斥只能保证“不会同时写”，不能保证模块状态机时序正确。
- 一个 core 正在发 SPI frame，另一个 core 改 BACON/ECON/CS 配置，仍可能破坏传输。
- ISR 归属、DMA channel 归属、错误处理归属会变复杂。

推荐设计：

```text
一个外设 Controller 归属一个 core / 一个 BSW partition。
其他 core 通过 IOC/RTE 请求 owner core 操作。
```

例如：

```text
Core0 owns QSPI0 Driver
Core1 SWC wants SPI transfer
Core1 → IOC request → Core0 Spi_MainFunction / Task → QSPI0
Core0 → IOC response → Core1
```

---

## 7. ARM Cortex‑M7 对比

### 7.1 先说明：M7 core 本身不是“天然多核模型”

Cortex‑M7 是一个处理器核。很多 MCU 是单 M7；也有异构双核 SoC，例如：

```text
Cortex-M7 + Cortex-M4
Cortex-M7 + Cortex-M33
双 Cortex-M7
```

因此对比时要分清：

```text
AURIX TC3xx：多 TriCore MCU，面向多核 AUTOSAR 比较典型
ARM M7：具体是否多核取决于 SoC 厂商实现
```

---

### 7.2 M7 的核心一致性问题：D-Cache + DMA / 另一个 Core

Cortex‑M7 常见问题：

```text
CM7 D-Cache enabled
DMA 写 SRAM
CM7 读 buffer
结果读到 cache 旧数据
```

或者：

```text
CM7 写 Tx buffer
DMA 读 SRAM 发送
结果 DMA 读到旧数据，因为 CM7 写还在 D-Cache dirty line
```

#### DMA Tx 前

```c
/* CPU 写 Tx buffer 后，DMA 读之前 */
SCB_CleanDCache_by_Addr((uint32_t*)txBuf, len);
__DSB();
StartDmaTx(txBuf, len);
```

#### DMA Rx 后

```c
/* DMA 写 Rx buffer 后，CPU 读之前 */
__DSB();
SCB_InvalidateDCache_by_Addr((uint32_t*)rxBuf, len);
ProcessRx(rxBuf);
```

#### 跨核 shared memory

```text
Producer core:
    写 shared data
    clean cache
    DMB/DSB
    写 flag / 触发中断

Consumer core:
    收到中断
    invalidate cache
    DMB/DSB
    读 shared data
```

---

### 7.3 M7 的原子操作

ARMv7‑M 支持 exclusive access 指令语义，常见 CMSIS 封装：

```c
__LDREXW(addr);
__STREXW(value, addr);
__CLREX();
```

简化 spinlock：

```c
static volatile uint32_t lock;

void Lock(void)
{
    while (1)
    {
        if (__LDREXW(&lock) == 0u)
        {
            if (__STREXW(1u, &lock) == 0u)
            {
                __DMB();
                return;
            }
        }
    }
}

void Unlock(void)
{
    __DMB();
    lock = 0u;
}
```

但 AUTOSAR 下不建议应用自己写这种锁。  
如果是 AUTOSAR OS，多核互斥应走 OS Spinlock。  
如果是非 AUTOSAR 双核 MCU，厂商常提供 HSEM、IPCC、mailbox、SEV/WFE 或 NVIC 软件中断等机制。

---

### 7.4 AURIX TC3xx vs Cortex‑M7 对比表

| 项目 | AURIX TC3xx | Cortex‑M7 类 MCU |
|---|---|---|
| 多核形态 | 多 TriCore，车规多核 AUTOSAR 常见 | 是否多核取决于 SoC，常见 M7+M4 |
| 共享内存 | LMU / DLMU / DAM / EMEM 等 | SRAM / AXI SRAM / DTCM / shared SRAM |
| 原子基础 | LDMST / SWAP.W / CMPSWAP.W / ST.T / SWAPMSK.W | LDREX / STREX / CLREX |
| 跨核通知 | Interrupt Router / SRC / OS/IOC | NVIC 软件中断、SEV/WFE、HSEM/IPCC，取决于厂商 |
| Cache 风险 | PCACHE/DCACHE/局部 RAM/共享 RAM，需要软件策略 | D‑Cache 与 DMA/共享 SRAM 一致性问题非常典型 |
| AUTOSAR 落地 | OS Spinlock + IOC + RTE/SchM | 同样可用 AUTOSAR OS/RTE/IOC，但底层由 vendor 适配 |
| 推荐共享区 | LMU shared section，必要时 non-cacheable | shared SRAM，MPU 配 non-cacheable 或显式 clean/invalidate |

---

# Part B：多核间通信

---

## 8. Why：为什么需要多核间通信？

### 8.1 多核不是为了“所有核都干同一件事”

车规 MCU 多核常见分工：

```text
Core0：主控制 / safety supervisor
Core1：通信栈 CAN/Eth/FlexRay
Core2：电机控制 / GTM / PWM
Core3：诊断 / 标定 / OTA
HSM ：安全启动 / crypto
DMA ：搬运数据
```

这些功能之间必须通信：

```text
控制核 → 通信核：发送 CAN/Eth 信号
通信核 → 控制核：接收传感器/网络指令
诊断核 → 控制核：读写 DID / RoutineControl
安全核 → 业务核：故障降级 / reset request
```

---

### 8.2 为什么不用全局变量硬传？

裸共享变量只能传“值”，不能完整表达：

```text
有没有新消息？
消息是否被消费？
多条消息如何排序？
队列满了怎么办？
接收方什么时候被唤醒？
发送方是否需要确认？
通信失败如何上报？
跨核复位/初始化时如何恢复？
```

所以多核通信必须设计成协议，而不是随便放一个全局变量。

---

## 9. What：多核间通信包含哪些模式？

### 9.1 AUTOSAR 层面的通信模式

```text
SWC Sender-Receiver
SWC Client-Server
BSW Module cross-partition call
IOC queued / unqueued
RTE event / OS task activation
```

### 9.2 底层硬件/软件通信模式

| 模式 | 说明 | 优点 | 风险 |
|---|---|---|---|
| Shared Memory + Flag | 共享内存 + 标志位 | 快 | 容易一致性错误 |
| Shared Memory + Spinlock | 加锁共享 mailbox | 简单 | busy wait，实时性差 |
| Ring Buffer | head/tail 队列 | 吞吐高 | full/empty/乱序处理复杂 |
| IOC | AUTOSAR 标准通信 | 对 SWC 透明 | 依赖生成配置 |
| Inter-core Interrupt | 只做通知 | 延迟低 | 数据本身仍需一致性 |
| Owner Core 模式 | 一个 core 拥有资源，其他 core 请求 | 最稳 | 多一次转发 |
| DMA 搬运 | 大块数据搬运 | CPU 负载低 | cache/descriptor 一致性 |

---

## 10. AUTOSAR How：跨核通信从配置到代码

### 10.1 SWC Sender-Receiver 跨核通信

#### 系统分配

```text
SWC_A / Runnable_A → Core0 / OsApplication_A / Task_A
SWC_B / Runnable_B → Core1 / OsApplication_B / Task_B
```

#### 应用代码

```c
/* Core0 */
void Runnable_A_10ms(void)
{
    VehicleSpeed_T speed;

    speed.value = 88;
    speed.status = VALID;

    (void)Rte_Write_PpVehicleSpeed_VehicleSpeed(&speed);
}

/* Core1 */
void Runnable_B_10ms(void)
{
    VehicleSpeed_T speed;

    if (Rte_Read_RpVehicleSpeed_VehicleSpeed(&speed) == RTE_E_OK)
    {
        UseSpeed(speed);
    }
}
```

#### 生成结果概念

```text
Rte_Write(...)
    ↓
IocSend_<signal>(...)
    ↓
IOC buffer / queue / lock / notification
    ↓
IocReceive_<signal>(...)
    ↓
Rte_Read(...)
```

应用代码不应该知道 `IocSend` 是否存在。  
它只应该依赖 RTE API。

---

### 10.2 Client-Server 跨核通信

#### 场景

Core1 诊断 SWC 调用 Core0 控制服务：

```c
Rte_Call_RpControlService_SetTorqueLimit(50);
```

#### 跨核后可能变成

```text
Client Runnable
    ↓ Rte_Call
IOC request message
    ↓
Server Task activated on Core0
    ↓
Server Runnable executes
    ↓
IOC response message
    ↓
Client gets return
```

#### 风险

- 同步调用可能阻塞 Client。
- Server 所在 core 如果负载高，响应时间不稳定。
- 如果 Client 持有 Spinlock 再跨核调用 Server，容易死锁。

#### 推荐

```text
跨核服务优先设计为异步请求/响应。
不要在持锁状态下做 Rte_Call。
重要请求加 counter + timeout + return code。
```

---

### 10.3 IOC Queued vs Unqueued 选择

| 信号类型 | 推荐 IOC | 说明 |
|---|---|---|
| 车速、温度、电压 | Unqueued | 新值覆盖旧值即可 |
| 诊断请求 | Queued | 每条请求都不能丢 |
| 控制命令 | Queued + ACK | 要知道是否执行 |
| 状态心跳 | Unqueued + counter | 只关心最新状态和活性 |
| 故障事件 | Queued 或 DEM event | 事件不能静默覆盖 |
| 大块数据 | Shared buffer + descriptor + IOC notify | IOC 只传索引/句柄 |

---

## 11. 具体案例 1：通信栈独占 Core，其他 Core 通过 IOC 请求发送 CAN

### 11.1 背景

```text
Core0：控制算法
Core1：CAN Stack / CanIf / CanDrv
```

### 11.2 Why

如果 Core0 和 Core1 都直接访问 CanDrv：

```text
CanDrv 全局状态需要跨核锁
Tx mailbox 分配复杂
CanIf/PduR/Com 回调上下文混乱
ISR 归属复杂
```

更好的方案是：

```text
CAN Driver 只在 Core1 操作。
Core0 通过 IOC 把发送请求交给 Core1。
```

### 11.3 通信结构

```text
Core0 Control SWC
    Rte_Write_PpCanTxReq()
        ↓
    IOC queued request
        ↓
Core1 CanTxProxy Task
    IocReceive_CanTxReq()
        ↓
    PduR/CanIf/Can_Write()
```

### 11.4 示例代码

Core0：

```c
void Ctrl_SendTorqueMsg(void)
{
    CanTxReq_t req;

    req.pduId = PDU_TORQUE_CMD;
    req.len   = 8u;
    FillTorqueData(req.sdu);

    (void)Rte_Write_PpCanTxReq_CanTxReq(&req);
}
```

Core1：

```c
void CanTxProxy_MainFunction(void)
{
    CanTxReq_t req;

    while (Rte_Read_RpCanTxReq_CanTxReq(&req) == RTE_E_OK)
    {
        PduInfoType pdu;

        pdu.SduDataPtr = req.sdu;
        pdu.SduLength  = req.len;

        (void)CanIf_Transmit(req.pduId, &pdu);
    }
}
```

### 11.5 这个设计解决的问题

| 问题 | 解决方式 |
|---|---|
| 外设寄存器多核抢占 | CanDrv 只归属 Core1 |
| Tx 队列一致性 | 队列在 Core1 本地 |
| 跨核通信 | RTE/IOC |
| 事件丢失 | Queued IOC |
| 实时性 | Core1 统一调度发送 |

---

## 12. 具体案例 2：诊断 DID 读取控制核数据

### 12.1 场景

```text
Core0：控制算法维护内部状态
Core1：Dcm/诊断栈
诊断请求 0x22 读取某个 DID
```

### 12.2 不推荐

Core1 Dcm 直接读取 Core0 内部全局变量：

```c
extern CtrlState_t gCtrlState;
Dcm_Copy(gCtrlState);
```

问题：

- 破坏 SWC 封装。
- 数据可能半更新。
- Core0 数据布局变化影响 Core1。
- ASIL/QM 混合时 freedom from interference 难分析。

### 12.3 推荐

Core0 周期发布快照：

```c
void Ctrl_PublishDiagSnapshot(void)
{
    DiagSnapshot_t snap;

    snap.speed = Ctrl_GetSpeed();
    snap.mode  = Ctrl_GetMode();
    snap.err   = Ctrl_GetError();
    snap.crc   = CalcCrc(&snap);

    (void)Rte_Write_PpDiagSnapshot_Snapshot(&snap);
}
```

Core1 Dcm 读取本地 RTE 缓存：

```c
Std_ReturnType Dcm_ReadData_DID_F190(uint8* Data)
{
    DiagSnapshot_t snap;

    if (Rte_Read_RpDiagSnapshot_Snapshot(&snap) != RTE_E_OK)
    {
        return E_NOT_OK;
    }

    if (!CheckCrc(&snap))
    {
        return E_NOT_OK;
    }

    SerializeSnapshot(Data, &snap);
    return E_OK;
}
```

### 12.4 设计收益

```text
控制核只负责发布一致快照
诊断核只读 RTE 缓存
跨核通信由 RTE/IOC 处理
DID 读取不会卡住控制算法
```

---

## 13. 具体案例 3：AURIX LMU Ring Buffer

### 13.1 场景

Core0 高频产生 log/event，Core1 低频拉取。

### 13.2 数据结构

```c
#define IPC_RING_SIZE  64u

typedef struct
{
    uint32 id;
    uint32 arg;
    uint32 timestamp;
    uint32 crc;
} IpcEvent_t;

typedef struct
{
    volatile uint32 head;  /* producer writes */
    volatile uint32 tail;  /* consumer writes */
    IpcEvent_t buf[IPC_RING_SIZE];
} IpcRing_t;

volatile IpcRing_t g_Core0ToCore1Ring;
```

### 13.3 Producer：Core0

```c
boolean Ipc_SendEvent(const IpcEvent_t* event)
{
    uint32 head = g_Core0ToCore1Ring.head;
    uint32 next = (head + 1u) % IPC_RING_SIZE;

    if (next == g_Core0ToCore1Ring.tail)
    {
        return FALSE; /* full */
    }

    g_Core0ToCore1Ring.buf[head] = *event;

    __dsync();

    g_Core0ToCore1Ring.head = next;

    __dsync();

    Ipc_TriggerCore1ServiceRequest();

    return TRUE;
}
```

### 13.4 Consumer：Core1

```c
boolean Ipc_ReceiveEvent(IpcEvent_t* event)
{
    uint32 tail = g_Core0ToCore1Ring.tail;

    if (tail == g_Core0ToCore1Ring.head)
    {
        return FALSE; /* empty */
    }

    __dsync();

    *event = g_Core0ToCore1Ring.buf[tail];

    g_Core0ToCore1Ring.tail = (tail + 1u) % IPC_RING_SIZE;

    return TRUE;
}
```

### 13.5 关键限制

这个版本成立的前提是：

```text
只有 Core0 写 head
只有 Core1 写 tail
只有 Core0 写 buf[head]
只有 Core1 读 buf[tail]
```

如果变成多 producer 或多 consumer，就要加 Spinlock 或用 CAS 设计 lock-free 队列。

---

## 14. 具体案例 4：Cortex‑M7 + M4 共享 SRAM Mailbox

### 14.1 场景

```text
CM7：主控制
CM4：通信/传感器
共享 SRAM：0x30040000
```

### 14.2 数据结构

```c
typedef struct
{
    volatile uint32_t ready;
    uint32_t cmd;
    uint32_t arg;
    uint32_t crc;
} M7M4_Mailbox_t;

#define MBOX ((M7M4_Mailbox_t*)0x30040000u)
```

### 14.3 CM7 发送

```c
void CM7_SendToCM4(uint32_t cmd, uint32_t arg)
{
    MBOX->ready = 0u;

    MBOX->cmd = cmd;
    MBOX->arg = arg;
    MBOX->crc = CalcCrc(MBOX);

    SCB_CleanDCache_by_Addr((uint32_t*)MBOX, sizeof(M7M4_Mailbox_t));
    __DSB();
    __DMB();

    MBOX->ready = 1u;

    SCB_CleanDCache_by_Addr((uint32_t*)&MBOX->ready, sizeof(uint32_t));
    __DSB();

    Trigger_CM4_Interrupt();
}
```

### 14.4 CM4 接收

```c
void CM4_IRQHandler(void)
{
    M7M4_Mailbox_t local;

    SCB_InvalidateDCache_by_Addr((uint32_t*)MBOX, sizeof(M7M4_Mailbox_t));
    __DSB();
    __DMB();

    if (MBOX->ready == 1u)
    {
        local = *MBOX;

        if (CheckCrc(&local))
        {
            Dispatch(local.cmd, local.arg);
        }
    }
}
```

### 14.5 Cortex‑M7 特别注意

- M7 的 D‑Cache 对 DMA/另一个 core 不透明。
- Buffer 地址和长度要按 cache line 对齐。
- `SCB_CleanDCache_by_Addr()` 和 `SCB_InvalidateDCache_by_Addr()` 的地址范围要覆盖完整 cache line。
- 对共享 SRAM 可通过 MPU 配成 non-cacheable，减少维护成本，但牺牲性能。

---

# Part C：系统工程落地方法

---

## 15. AUTOSAR 配置清单

### 15.1 OS 配置

需要确认：

```text
OsCore
OsApplication
OsTask core binding
ISR core binding
OsSpinlock
Spinlock nesting order
IOC communication
Cross-core interrupt / IPI support
```

重点：

- Task/ISR 是否绑定到指定 core。
- OS-Application 是否跨 core。
- 需要跨 core 的共享资源是否配置 Spinlock。
- 多个 Spinlock 是否配置唯一嵌套顺序。
- 是否禁止在持有 Spinlock 时调用可能阻塞的服务。

---

### 15.2 RTE 配置

需要确认：

```text
SWC-to-ECU mapping
Runnable-to-Task mapping
RTE partition mapping
Sender-Receiver 是否跨 partition/core
Client-Server 是否跨 partition/core
IRV 配置
Exclusive Area 配置
RTE event 激活路径
```

生成结果要检查：

```text
Rte_Write 是否调用 IocSend
Rte_Read 是否调用 IocReceive
Exclusive Area 映射成什么锁策略
是否有 queued/unqueued 配置
队列长度是否满足 burst
错误返回是否被应用处理
```

---

### 15.3 BSW / MCAL 配置

需要确认：

```text
BSW module belongs to which partition/core
Driver 是否允许 reentrant
SchM Exclusive Area 实现策略
ISR 归属 core
DMA channel 归属 core
外设 ownership
```

推荐原则：

```text
一个外设 Controller 归属一个 core。
其他 core 通过 IOC 请求 owner core。
不要多个 core 直接写同一个外设寄存器集合。
```

---

## 16. 测试验证视角

### 16.1 数据一致性测试点

| 测试项 | 方法 | 预期 |
|---|---|---|
| RMW race | 两核同时 counter++ 压测 | 无丢计数 |
| 结构体一致性 | seq/crc 快照校验 | 无半包 |
| Spinlock 互斥 | 临界区插入长延迟 | 同一时刻只有一核进入 |
| Spinlock 嵌套 | 故意反序申请 | OS 报错或禁止配置 |
| Cache 一致性 | cache on/off 对比 | 无旧数据 |
| DMA + cache | Tx/Rx buffer clean/invalidate | 无错包 |
| 跨核通知 | 高频 interrupt burst | 无丢通知或按设计合并 |
| 队列边界 | empty/full/overflow | 返回正确错误码 |
| 复位恢复 | 单 core reset / app reset | mailbox 状态可恢复 |

---

### 16.2 AUTOSAR 通信测试点

| 测试项 | 方法 | 预期 |
|---|---|---|
| RTE 本地通信 | 同 core Runnable 通信 | 读写正确 |
| RTE 跨核 unqueued | 高频写低频读 | 读到最新值 |
| RTE 跨核 queued | 连续发送 N 条事件 | FIFO 顺序正确 |
| IOC overflow | 队列写满 | 返回错误或按配置覆盖 |
| Client-Server 跨核 | Server core 忙 | timeout/返回码符合设计 |
| BSW distributed | Core0 请求 Core1 CAN 发送 | 发送成功，状态一致 |
| Error handling | IOC/Spinlock 返回错误 | 应用不忽略错误 |

---

## 17. 常见错误清单

### 17.1 把 volatile 当锁

错误：

```c
volatile uint32 flag;
```

`volatile` 不能保证：

```text
原子 RMW
跨核互斥
cache clean/invalidate
memory ordering
结构体一致快照
```

---

### 17.2 在 Spinlock 里做耗时操作

错误：

```c
GetSpinlock(S1);

while (PeripheralBusy())
{
    /* wait */
}

ReleaseSpinlock(S1);
```

问题：

```text
其他 core busy wait
实时性恶化
可能触发 watchdog
```

---

### 17.3 持锁跨核调用服务

错误：

```c
GetSpinlock(S1);
Rte_Call_RemoteServer_DoSomething();
ReleaseSpinlock(S1);
```

如果 RemoteServer 又需要 S1 或等待当前 core，直接死锁。

---

### 17.4 Cacheable shared buffer 不做维护

错误：

```c
shared.data = value;
shared.ready = 1;
TriggerOtherCore();
```

正确至少需要：

```text
写 data
clean/writeback cache
barrier
写 ready
clean/writeback ready
barrier
trigger
```

或者把 shared buffer 配成 non-cacheable。

---

## 18. 最推荐的工程架构

### 18.1 控制类信号

```text
SWC_A → RTE Sender-Receiver → IOC unqueued → SWC_B
```

### 18.2 事件类消息

```text
SWC_A → RTE Sender-Receiver → IOC queued → SWC_B
```

### 18.3 外设访问

```text
非 owner core → IOC request → owner core BSW/MCAL → 外设
```

### 18.4 大块数据

```text
shared buffer / descriptor
+ cache maintenance
+ IOC 传 descriptor index
+ CRC/counter/timeout
```

### 18.5 ASIL 数据

```text
RTE/IOC
+ E2E Profile / CRC
+ alive counter
+ timeout monitoring
+ memory protection
+ SMU reaction
```

---

## 19. 一页总结

```text
多核数据一致性
    WHY：
        防止 race、半包、旧 cache、乱序可见、RMW 丢失
    WHAT：
        原子性 + 互斥 + 可见性 + 顺序 + 完整性
    HOW：
        RTE Exclusive Area / SchM / OS Resource / Spinlock / Atomic / Cache maintenance / Barrier

多核间通信
    WHY：
        多核功能分工后必须传递数据、事件、服务请求
    WHAT：
        Sender-Receiver、Client-Server、IOC、Mailbox、RingBuffer、Inter-core interrupt
    HOW：
        SWC 走 RTE，跨 core 走 IOC；
        外设 owner core 化；
        shared memory 只做受控 mailbox，不做裸全局变量乱读写
```

最终工程原则：

> **AUTOSAR 层面用 RTE/IOC 保持软件架构清晰；OS 层面用 Spinlock/Resource 保证互斥；MCU 层面用 atomic/cache/barrier 保证硬件可见性；安全层面用 E2E/counter/timeout 保证可诊断。**

---

## 20. 参考资料

- AUTOSAR Classic Platform R24-11：Specification of Operating System  
  - IOC、Spinlock、OS-Application、multi-core startup、OS Resource 限制等。
- AUTOSAR Classic Platform R24-11：Specification / Requirements of RTE  
  - RTE、VFB、SWC location independence、Exclusive Area、IRV、RTE communication。
- AUTOSAR Classic Platform R22-11：Guide to BSW Distribution  
  - BSW multi-core distribution、BSW partitions、cross partition communication、performance use cases。
- Infineon AURIX TC3xx User Manual  
  - SRI/FPI interconnect、CPU subsystem、cache、LMU/DSPR/PSPR、interrupt/service request、ENDINIT。
- Infineon TriCore TC1.6.2 Architecture Manual  
  - Atomic operations：LDMST、SWAP.W、ST.T、CMPSWAP.W、SWAPMSK.W；cache instructions；DSYNC/ISYNC。
- Arm Cortex‑M7 Technical Reference Manual / ARMv7‑M Architecture Reference Manual  
  - L1 cache、DMB/DSB/ISB、exclusive access、cache maintenance。
