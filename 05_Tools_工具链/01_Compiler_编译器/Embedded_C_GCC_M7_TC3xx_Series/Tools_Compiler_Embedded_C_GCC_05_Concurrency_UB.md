# 嵌入式C并发、中断安全与未定义行为

---

## 系列导航

- **返回总纲**：[[Tools_Compiler_Embedded_C_GCC_00_Series_Overview|00 学习总纲与进度]]
- **上一篇**：[[Tools_Compiler_Embedded_C_GCC_04_Struct_Alignment|04_Struct_Alignment]]
- **下一篇**：[[Tools_Compiler_GCC_06_Compilation_ABI_Optimization|06_Compilation_ABI_Optimization]]

---


> 本章目标：区分“编译器看见什么、CPU按什么顺序执行、Cache里有什么、其他Master何时可见”，建立ISR、任务、多核和DMA共享数据的正确模型。

---

## 1. 嵌入式并发的四种来源

| 并发源 | 是否同一CPU | 能否被本核关中断阻止 | 是否经过CPU Cache |
|---|---:|---:|---:|
| 主程序与ISR | 是 | 通常可以 | 是 |
| RTOS任务间抢占 | 是 | 临界区/调度锁视实现 | 是 |
| 多CPU核 | 否 | 否 | 各核可能有独立Cache |
| DMA/外设Master | 否 | 否 | 通常不经过CPU Cache |

因此“关中断保护共享变量”只适用于特定单核并发，不能自动保护多核和DMA。

---

## 2. `volatile`、原子性、顺序与可见性是四件事

### 2.1 volatile

要求编译器形成可观察访问，不能永久缓存值。

### 2.2 原子性

其他执行者不能观察或插入操作的中间状态。

### 2.3 顺序

前后多个访问按照规定次序被观察。

### 2.4 可见性

一个Master的更新何时被另一个Master读取到。

```c
volatile uint32_t flag;
```

只凭这一定义，无法证明：

- `flag++`原子；
- `data`先于`flag`对另一核可见；
- DMA能看到CPU Cache中的新数据；
- posted write已经到达外设。

---

## 3. CASE-01：`counter++`丢失更新

```c
volatile uint32_t counter;

void Task(void)
{
    counter++;
}

void ISR(void)
{
    counter++;
}
```

可能交错：

```text
Task Load counter = 10
ISR  Load counter = 10
ISR  Add/Store 11
Task Add/Store 11
最终11，实际发生了两次++
```

### 单核解决

```c
uint32_t key = EnterCritical();
counter++;
ExitCritical(key);
```

要求恢复原中断状态，而不是无条件开中断。

### 多核解决

- C原子类型且工具链/目标实现满足需求；
- M7 SoC使用LDREX/STREX并确认互连和Shareable属性支持全系统独占监视；
- TC3xx使用LDMST/CMPSWAP等原子指令；
- 配合内存屏障建立数据发布顺序。

---

## 4. Cortex-M7临界区

### 4.1 PRIMASK

屏蔽可配置优先级异常，但不屏蔽NMI和HardFault。

### 4.2 BASEPRI

屏蔽优先级数值达到阈值的一组异常，适合RTOS临界区。需注意：

- ARM中数值越小逻辑优先级越高；
- 实现的优先级位数有限；
- FreeRTOS可调用API的ISR优先级受`configMAX_SYSCALL_INTERRUPT_PRIORITY`限制；
- 不能用BASEPRI保护来自另一个核或DMA的访问。

### 4.3 FAULTMASK

影响更广，普通应用极少使用。错误使用可能让系统失去故障处理能力。

保存/恢复示意：

```c
uint32_t key = __get_PRIMASK();
__disable_irq();
/* critical */
__set_PRIMASK(key);
```

生产代码优先使用经过验证的OS/CMSIS封装。

---

## 5. TC3xx临界区

TriCore可通过指令/编译器intrinsic管理中断使能和优先级。要点：

- 必须保存并恢复调用前状态；
- 本核禁中断只保护本核ISR；
- 不能阻止其他CPU、DMA、HSM或外设Master；
- ENDINIT、SMU等全局资源还需跨任务/跨核的软件锁；
- 临界区前后是否需要DSYNC取决于共享对象和外设完成语义。

不要把iLLD中的简单关中断序列直接推导为多核锁。

---

## 6. CASE-02：发布数据与标志

生产者：

```c
shared_data = 0x12345678U;
ready = 1U;
```

消费者：

```c
if (ready != 0U)
{
    Use(shared_data);
}
```

即使`ready`为volatile，仍要考虑：

- 编译器是否重排普通`shared_data`访问；
- CPU/总线是否允许观察顺序变化；
- 两个对象是否在不同Cache Line；
- 生产者是否clean Cache；
- 消费者是否invalidate；
- 多核C数据竞争是否已用原子类型建立happens-before。

正确抽象是release/acquire，而不是“加一个volatile”。

使用C原子示意：

```c
#include <stdatomic.h>

static uint32_t shared_data;
static atomic_uint ready;

void Publish(void)
{
    shared_data = UINT32_C(0x12345678);
    atomic_store_explicit(&ready, 1U, memory_order_release);
}

bool Consume(uint32_t *out)
{
    if (atomic_load_explicit(&ready, memory_order_acquire) == 0U)
    {
        return false;
    }
    *out = shared_data;
    return true;
}
```

但必须验证工具链是否生成lock-free指令、内存属性是否正确、Cache是否硬件一致。C原子也不会自动clean非一致DMA Buffer。

---

## 7. 内存屏障

### 7.1 编译器屏障

限制编译器重排，不保证CPU/互连完成：

```c
__asm__ volatile ("" ::: "memory");
```

### 7.2 Cortex-M7

```c
__DMB();
__DSB();
__ISB();
```

典型用途：

- DMB：共享数据发布顺序；
- DSB：在低功耗、系统控制或要求完成的场景等待前序操作；
- ISB：修改MPU、CONTROL、向量/执行上下文后刷新指令流水线。

不要把示例机械套用，需按ARM架构和SoC手册规定的域、Memory Type、Shareability使用。

### 7.3 TC3xx

```c
__dsync();
__isync();
```

- DSYNC保证前序数据访问完成后启动后序数据访问；
- ISYNC用于架构状态改变后的指令同步；
- SRI/SPB posted write可能还需目标Slave read-back；
- DSYNC不自动清理/失效DCache。

---

## 8. CASE-03：CPU到DMA

CPU填充发送Buffer：

```c
FillBuffer(tx, length);
Dma_Start(tx, length);
```

若`tx`位于M7 Write-back Cache区域：

```text
CPU修改只在DCache Dirty Line
→ DMA从RAM读取旧数据
```

正确顺序概念上是：

```text
CPU拥有Buffer并完成写入
→ Clean覆盖的Cache Line到PoC/平台规定点
→ 适当屏障
→ 配置并启动DMA
→ DMA拥有Buffer
```

TC3xx同样要判断目标数据是否位于DCacheable区域、DLMU/LMU的访问路径，以及DMA看到的系统地址。将共享Buffer放在明确的non-cacheable区域可简化一致性，但会损失CPU性能。

---

## 9. CASE-04：DMA到CPU

```text
CPU此前读过rx Buffer，Cache中保留旧副本
→ DMA把新数据写入RAM
→ CPU再次命中Cache，仍读旧数据
```

正确所有权流程：

```text
启动DMA前避免CPU继续使用Buffer
→ 必要时处理潜在Dirty Line
→ DMA完成
→ 屏障/读取完成状态
→ Invalidate相关Cache Line
→ CPU取得所有权并读取
```

危险操作：DMA进行中CPU同时invalidate/读取/写入同一Cache Line。

---

## 10. False Sharing

两个逻辑变量位于同一Cache Line：

```c
typedef struct
{
    uint32_t cpu0_counter;
    uint32_t cpu1_counter;
} Shared_t;
```

即使两个核写不同成员，仍可能：

- 频繁clean/invalidate整条Line；
- 相互覆盖Dirty数据；
- 产生性能抖动；
- ECC RMW落在同一物理word。

解决：按Cache Line/ECC粒度隔离高频写对象，并明确共享区布局。

---

## 11. 原子操作

### 11.1 Cortex-M7 LDREX/STREX模型

概念：

```c
do
{
    old = __LDREXW(addr);
    new_value = old | mask;
    status = __STREXW(new_value, addr);
} while (status != 0U);
```

`LDREX`不仅是读值，还建立独占监视；`STREX`只有监视仍有效时才成功。

注意：

- 异常、其他Master写入、地址属性和实现可能使STREX失败；
- 必须允许重试；
- 原子RMW不自动提供所有前后内存访问顺序；
- 使用CMSIS/C原子库优于散落手写intrinsic。

### 11.2 TC3xx

- LDMST：按掩码原子更新word，适合位集合；
- SWAP：原子交换；
- CMPSWAP：比较并交换，适合锁和无锁状态机；
- 具体地址范围、对齐和总线支持以TC3xx手册为准。

### CASE-05：错误Spinlock

```c
while (lock != 0U)
{
}
lock = 1U;
```

两个核可以同时看到0并同时写1，二者都进入临界区。必须使用原子test-and-set/compare-exchange，并定义release时的内存顺序。

---

## 12. ISR安全Ring Buffer

单生产者ISR、单消费者Task可设计为：

```c
#define RING_SIZE 16U

typedef struct
{
    uint8_t data[RING_SIZE];
    volatile uint32_t head;
    volatile uint32_t tail;
} Ring_t;
```

约束：

- 只有生产者写`head`；
- 只有消费者写`tail`；
- 二者都可读对方索引；
- 索引宽度访问必须原子；
- 生产者必须先写数据，再发布新`head`；
- 消费者观察到`head`后才能读数据。

生产者示意：

```c
bool Ring_PushFromISR(Ring_t *r, uint8_t value)
{
    uint32_t head = r->head;
    uint32_t next = (head + 1U) % RING_SIZE;
    if (next == r->tail)
    {
        return false;
    }

    r->data[head] = value;
    /* 发布前需要的编译器/CPU顺序由平台封装提供 */
    PublishBarrier();
    r->head = next;
    return true;
}
```

多生产者或多消费者时，这个简单模型不再成立。

---

## 13. 可重入性

函数可重入需要：

- 不依赖无保护的静态可变状态；
- 不返回共享静态Buffer；
- 调用的库函数也可重入；
- 对共享硬件资源有明确保护；
- 不依赖单一全局错误码。

### CASE-06：ISR调用非可重入格式化函数

ISR与Task同时调用使用全局Buffer的日志函数会破坏输出，且格式化耗时不可控。ISR中推荐：

- 记录固定宽度事件；
- 写入无阻塞Ring Buffer；
- 由后台任务格式化和输出。

---

## 14. 中断嵌套

共享对象不仅面对“ISR与Task”，还可能面对高优先级ISR抢占低优先级ISR。

设计时应列出访问矩阵：

| 对象 | Task | ISR Low | ISR High | DMA | CPU1 |
|---|---:|---:|---:|---:|---:|
| `rx_ring.head` | R | W | - | - | - |
| `error_flags` | RW | W | W | - | R |
| `dma_buffer` | R | - | - | W | - |

每个多写者对象都需要原子/锁/所有权方案。

---

## 15. TC3xx ENDINIT并发实例

错误模式：

```text
Task A：clear ENDINIT
→ 被抢占
Task B/ISR：clear或set ENDINIT
→ Task A继续，密码序列/保护状态不再符合预期
```

即使没人“修改密码变量”，仍可能由于同一WDT保护序列被重入而卡在等待状态。

系统设计：

- 每个WDT实例的clear/modify/set形成不可重入事务；
- 本核任务/ISR使用临界区；
- 全局Safety ENDINIT若可被多核访问，使用跨核锁；
- 异常路径确保恢复保护；
- 设置超时和故障记录；
- 按MCAL/芯片规范插入必要同步和read-back。

---

## 16. 未定义、实现定义和未指定行为

| 类别 | 含义 | 例子 |
|---|---|---|
| Undefined Behavior | 标准不施加要求 | 有符号溢出、越界、失效指针 |
| Implementation-defined | 实现选择并文档化 | `char`有符号性、负数右移 |
| Unspecified | 从多个允许结果中选择，不一定文档化 | 部分求值顺序 |

### 高频UB

- 数组越界；
- 空/悬空/无效指针解引用；
- 有符号溢出；
- 移位量越界；
- 除零；
- 违反对齐和有效类型；
- 无同步的数据竞争；
- 修改字符串字面量；
- 函数指针类型不匹配；
- 使用未初始化自动变量。

### CASE-07：数组越界破坏任务控制块

```c
uint8_t local[16];
for (uint32_t i = 0U; i <= 16U; i++)
{
    local[i] = 0U;
}
```

越界1字节可能破坏：

- 保存寄存器；
- 返回地址/栈帧；
- 邻近局部变量；
- RTOS栈水位或控制信息。

M7可能稍后在异常返回HardFault；TC3xx可能稍后在RET/CSA/数据访问时Trap。故障点不一定等于根因点。

---

## 17. CASE-08：`-O0`正常，`-O2`失败

定位顺序：

1. 检查UB：越界、生命周期、别名、溢出、竞态；
2. 检查缺少volatile的MMIO/ISR对象；
3. 检查链接/Section/未初始化；
4. 比较预处理结果；
5. 比较反汇编；
6. 检查LTO和`--gc-sections`；
7. 检查栈尺寸和内联；
8. 最后才怀疑编译器缺陷，并制作最小复现。

不要用全局`-O0`作为修复。它可能只是改变时间窗口、栈布局或寄存器分配，使Bug暂时消失。

---

## 18. CASE-09：外设写完成语义

```c
PERIPH->CTRL = START;
EnterLowPower();
```

写可能仍在：

- CPU Store Buffer；
- 总线Bridge posted write Buffer；
- 外设内部同步器。

M7常见要求是按SoC手册执行DSB/read-back后再进入低功耗；TC3xx可能要求DSYNC并读取目标Slave状态。必须区分：

```text
CPU已发出
≠ 总线已送达
≠ Slave已接收
≠ 外设动作已完成
```

---

## 19. CASE-10：64-bit共享计数

解决方案比较：

| 方案 | 单核ISR | 多核 | 实时性 | 备注 |
|---|---:|---:|---:|---|
| 关中断 | 适合短操作 | 不适合 | 可控 | 恢复原状态 |
| 高低高重复读 | 单写者计数器适用 | 有条件 | 低开销 | 写入顺序需定义 |
| Sequence Counter | 适合单写多读 | 可扩展 | 读可能重试 | 需内存序 |
| Mutex | Task适用 | 适合 | 可能阻塞 | ISR通常不能用 |
| 原子64-bit | 依实现 | 依实现 | 简洁 | 32-bit目标可能调用库锁 |

---

## 20. 安全编码策略

1. 为每个共享对象建立读写者矩阵；
2. 区分单核、ISR、多核和DMA并发；
3. 单写者优先于复杂锁；
4. 所有权转移点必须有屏障/Cache维护；
5. 临界区保存并恢复原状态；
6. 多核不能只靠关中断；
7. 不把volatile当原子或一致性机制；
8. ISR执行时间有界，不做阻塞和复杂格式化；
9. 共享64-bit对象显式设计一致读取；
10. 对`-O0/-O2/LTO`均执行回归；
11. 开启高等级Warning和静态分析；
12. 对重要共享结构进行压力、抢占和故障注入测试。

---

## 21. 验证实验

### EXP-01：丢失更新

任务和高频ISR同时递增，比较volatile、临界区、原子操作。

### EXP-02：发布顺序

生产者写数据再置flag，消费者校验数据；在高优化、多核和Cache压力下运行，比较无屏障与release/acquire方案。

### EXP-03：DMA Cache一致性

CPU→DMA、DMA→CPU各建立正向和负向Case，覆盖非Cache区、Cache区、非对齐起止地址和共享Cache Line。

### EXP-04：Spinlock

TC397多核和具备多Master平台上分别使用普通Load/Store与原子指令实现锁，统计同时进入临界区次数。

### EXP-05：Store完成

通过GPIO/总线监测比较普通写、屏障、read-back、BUSY轮询的完成时刻。

### EXP-06：优化矩阵

对竞态、别名、越界等案例使用`-O0/-Og/-O2/-Os/LTO`，记录现象并证明根因仍是代码语义。

---

## 22. 系统需求推导

| ID | 系统需求示例 |
|---|---|
| SYS-CONC-001 | 每个跨上下文共享对象应定义读者、写者、原子宽度和所有权。 |
| SYS-CONC-002 | 多核共享锁应使用所有相关Master可见的原子机制。 |
| SYS-CACHE-001 | DMA接口应定义CPU→DMA与DMA→CPU的Cache维护和屏障序列。 |
| SYS-ISR-001 | ISR调用接口应声明是否ISR-safe、是否可重入和最大执行时间。 |
| SYS-BARR-001 | 芯片手册应定义屏障到CPU、互连和Slave的完成边界。 |
| SYS-STRBUF-001 | 低功耗/复位前应有机制排空关键写Buffer并报告超时。 |
| SYS-CONC-DIAG-001 | 非锁步CPU的内部FIFO/Store Buffer应在诊断测试间隔内得到覆盖。 |

---

## 23. 面试与评审问题

1. volatile、原子性、顺序、可见性有什么区别？
2. BASEPRI临界区能否阻止DMA？
3. TC3xx本核禁中断能否保护多核共享变量？
4. DMB/DSB与Cache clean是什么关系？
5. DSYNC后为什么有时仍要read-back？
6. LDREX读取旧值的意义是什么？
7. 简单Spinlock不用原子指令会怎样？
8. 单生产者单消费者Ring Buffer需要哪些顺序保证？
9. 为什么DMA Buffer加volatile仍可能读旧数据？
10. 如何系统定位`-O0`正常、`-O2`失败？

---

## 24. 小结

并发正确性必须完成四层闭环：

```text
C层：没有数据竞争和未定义行为
→ 编译层：访问未被错误消除/重排
→ CPU层：原子指令和屏障正确
→ SoC层：Cache、互连、DMA和Slave完成语义正确
```

完成前五章后，已经能够判断多数嵌入式C代码本身是否可靠。下一阶段进入GCC、ABI和汇编，观察这些C语义怎样变成M7和TC3xx机器行为。
