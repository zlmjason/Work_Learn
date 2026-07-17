# 嵌入式C对象模型、数据类型与表达式

---

## 系列导航

- **返回总纲**：[[Tools_Compiler_Embedded_C_GCC_00_Series_Overview|00 学习总纲与进度]]
- **上一篇**：[[Tools_Compiler_Embedded_C_GCC_00_Series_Overview|00_Series_Overview]]
- **下一篇**：[[Tools_Compiler_Embedded_C_GCC_02_Pointers_Arrays|02_Pointers_Arrays]]

---


> 本章目标：不靠“经验猜测”，而是用C对象模型判断一个表达式的类型、取值、生命周期和硬件访问后果。  
> 平台：32-bit Cortex-M7与32-bit TriCore TC1.6.2P。具体ABI尺寸以项目工具链预定义宏和ABI手册为准。

---

## 1. Why：为什么嵌入式必须重视类型

在桌面程序中，一次错误类型转换可能只产生错误结果；在MCU中，它还可能改变：

- 总线访问宽度；
- 地址对齐要求；
- 寄存器副作用；
- ECC Read-Modify-Write；
- 原子性；
- 函数参数传递方式；
- 编译器优化结论；
- Flash/RAM占用；
- Fault/Trap类型。

例如：

```c
*(volatile uint8_t  *)REG_ADDR = 1U;
*(volatile uint32_t *)REG_ADDR = 1U;
```

两句都“写1”，但可能分别产生8-bit和32-bit总线事务。若寄存器只允许32-bit访问，第一句可能产生BusFault、DSE或未定义的外设行为。

---

## 2. 对象、值、类型与存储

### 2.1 对象是什么

C中的对象是一块能够保存值的存储区域。对象具有：

- 类型；
- 大小；
- 对齐要求；
- 存储期；
- 可能的名字和链接属性。

```c
static uint32_t counter = 10U;
```

这里：

- 对象：保存`counter`的存储区域；
- 类型：`uint32_t`；
- 值：初始为10；
- 存储期：静态存储期；
- 链接属性：取决于定义位置，文件作用域`static`为内部链接；
- 典型Section：`.data`。

### 2.2 声明与定义

```c
extern uint32_t g_state; /* 声明：说明对象存在于其他位置 */
uint32_t g_state;        /* 定义：为对象提供存储 */
```

常见错误是头文件中直接定义：

```c
/* bad.h */
uint32_t g_state = 0U;
```

多个源文件包含后可能产生multiple definition。正确方式：

```c
/* state.h */
extern uint32_t g_state;

/* state.c */
uint32_t g_state = 0U;
```

### 2.3 左值不是“等号左边的值”

可修改左值代表一个可定位、可修改的对象：

```c
uint32_t x;
x = 1U;       /* x是可修改左值 */
```

数组名、函数名、`const`对象和寄存器宏的行为需要分别判断，不能只看是否出现在赋值号左侧。

---

## 3. 基本整数类型

### 3.1 标准只规定最小范围

ISO C没有保证`int`永远32-bit，也没有保证`long`在所有平台相同。因此嵌入式接口优先使用：

```c
#include <stdint.h>

uint8_t
uint16_t
uint32_t
uint64_t
int8_t
int16_t
int32_t
int64_t
```

典型32-bit嵌入式ABI常见情况：

| 类型 | 常见宽度 | 注意 |
|---|---:|---|
| `char` | 8 bit | 有符号性由实现决定 |
| `short` | 16 bit | 通常自然对齐2字节 |
| `int` | 32 bit | 整数提升的主要目标类型 |
| `long` | 32 bit | 不能假设与PC端LP64一致 |
| `long long` | 64 bit | 32-bit CPU上通常需多条指令 |
| 指针 | 32 bit | 仍需遵守所指类型对齐 |

应使用静态断言锁定关键假设：

```c
#include <stdint.h>

_Static_assert(sizeof(uint32_t) == 4U, "uint32_t must be 32 bit");
_Static_assert(sizeof(uintptr_t) == sizeof(void *), "uintptr_t mismatch");
```

### 3.2 `uint32_t`、`uint_fast32_t`和`uintptr_t`

| 类型 | 目的 |
|---|---|
| `uint32_t` | 精确32-bit，适合寄存器、协议、存储格式 |
| `uint_fast32_t` | 至少32-bit且实现认为最快，不保证存储格式固定 |
| `uint_least32_t` | 至少32-bit且占用最小 |
| `uintptr_t` | 能无损保存对象指针的无符号整数类型 |

地址计算应使用`uintptr_t`：

```c
uintptr_t addr = (uintptr_t)buffer;
bool aligned = ((addr & 0x1FU) == 0U); /* 32-byte Cache Line对齐 */
```

不要把指针强制塞入可能更窄的`uint32_t`，即使当前两个目标平台通常都是32-bit。

---

## 4. 整数提升：最容易被忽略的规则

### 4.1 两个`uint8_t`通常不是8-bit相加

```c
uint8_t a = 250U;
uint8_t b = 10U;
uint8_t c = a + b;
```

过程：

```text
a、b先整数提升为int
→ 250 + 10 = 260（int）
→ 赋值给uint8_t
→ 按模256转换为4
```

因此结果通常是4，而不是加法阶段立即8-bit溢出。

### 4.2 位运算也会提升

```c
uint8_t value = 0x80U;
uint8_t result = (uint8_t)(~value);
```

`value`先提升为`int`，`~`作用于整个`int`宽度，最后再截断为8-bit。若缺少显式转换，静态分析工具可能报出essential type问题。

### 4.3 枚举通常参与`int`运算

枚举适合状态语义，但不能默认其存储宽度等于8-bit：

```c
typedef enum
{
    STATE_IDLE,
    STATE_RUN,
    STATE_ERROR
} State_t;
```

若协议字段固定1字节，应显式序列化，而不是直接发送`sizeof(State_t)`。

---

## 5. 有符号与无符号混合

### CASE-01：看起来应该成立的比较

```c
int32_t  error = -1;
uint32_t count = 1U;

if (error < count)
{
    /* 是否进入？ */
}
```

在常见32-bit实现中，`error`会转换为`uint32_t`，`-1`变成`0xFFFFFFFF`，所以条件为假。

正确做法不是机械强转，而是先定义业务域：

```c
if ((error < 0) || ((uint32_t)error < count))
{
}
```

系统工程结论：

- 计数和长度通常使用无符号类型；
- 错误码和可能为负的差值使用有符号类型；
- 不让二者在无说明的情况下直接比较。

---

## 6. 溢出：无符号定义、有符号未定义

### 6.1 无符号回绕

无符号整数按模$2^N$运算：

```c
uint32_t x = UINT32_MAX;
x++; /* 定义良好，结果为0 */
```

可利用它实现计时回绕：

```c
bool TimeoutExpired(uint32_t now, uint32_t start, uint32_t timeout)
{
    return ((uint32_t)(now - start) >= timeout);
}
```

前提是`timeout`不跨越无法区分的过大范围，通常不超过计数模空间的一半。

### 6.2 有符号溢出是未定义行为

```c
int32_t x = INT32_MAX;
x++; /* 未定义行为 */
```

GCC可以假设有符号溢出不会发生，从而进行看似“反直觉”的优化：

```c
bool IsGreaterAfterIncrement(int32_t x)
{
    return (x + 1 > x);
}
```

在标准假设下该表达式恒真，编译器可能直接返回true。不能用“硬件补码会回绕”反驳编译器，因为C语义已在硬件执行之前失效。

正确策略：

- 业务允许回绕时使用无符号类型；
- 需要饱和时先检查边界；
- 使用编译器溢出检测内建函数时封装平台适配；
- 不依赖`-fwrapv`掩盖不清晰的接口语义，除非项目规范明确要求。

---

## 7. 移位与Mask

### CASE-02：`1 << 31`

```c
uint32_t mask = (1 << 31);
```

字面量`1`是`signed int`。在32-bit `int`上，把1移入符号位会触及未定义行为。应写：

```c
uint32_t mask = (UINT32_C(1) << 31U);
```

### 移位规则

- 移位量小于0：未定义；
- 移位量大于等于左操作数提升后的位宽：未定义；
- 负有符号数左移：未定义；
- 负有符号数右移：结果由实现定义；
- 无符号右移：高位补0。

安全位掩码：

```c
#define BIT_U32(pos) (UINT32_C(1) << (pos))

static inline uint32_t FieldPrep(uint32_t mask, uint32_t shift, uint32_t value)
{
    return ((value << shift) & mask);
}
```

接口还应断言或审查`pos < 32U`。

---

## 8. 常量类型与后缀

```c
100       /* int */
100U      /* unsigned int */
100L      /* long */
100UL     /* unsigned long */
100ULL    /* unsigned long long */
0x80000000/* 类型取决于可表示范围 */
```

推荐使用`stdint.h`宏表达固定宽度常量：

```c
uint32_t mask = UINT32_C(0x80000000);
uint64_t time = UINT64_C(10000000000);
```

### CASE-03：乘法在转换前已溢出

```c
uint32_t a = 100000U;
uint32_t b = 100000U;
uint64_t result = a * b;
```

乘法在`uint32_t`中进行，结果先32-bit回绕，再扩展到64-bit。正确写法：

```c
uint64_t result = (uint64_t)a * (uint64_t)b;
```

---

## 9. 64-bit对象在32-bit MCU上的问题

### 9.1 一条C赋值不等于一条机器指令

```c
volatile uint64_t timestamp;
```

在32-bit M7或TC1.6.2P上，普通64-bit访问可能：

- 使用成对寄存器和多条指令；
- 使用芯片支持的64-bit总线访问；
- 因对齐或内存类型被拆分；
- 不具备对ISR/多核的原子性。

### CASE-04：时间戳撕裂

ISR更新：

```c
volatile uint64_t g_tick;

void TimerISR(void)
{
    g_tick++;
}
```

任务读取时可能出现：

```text
读低32位
→ ISR更新高低两部分
→ 读高32位
→ 组合出从未真实存在的64-bit值
```

解决方式按场景选择：

1. 短临界区；
2. 原子库且实现确实lock-free；
3. sequence counter；
4. 高-低-高重复读取算法；
5. 硬件锁存寄存器。

Sequence counter示例：

```c
typedef struct
{
    volatile uint32_t seq;
    volatile uint32_t low;
    volatile uint32_t high;
} SharedTime_t;

uint64_t ReadTime(const SharedTime_t *p)
{
    uint32_t s0;
    uint32_t s1;
    uint32_t low;
    uint32_t high;

    do
    {
        s0 = p->seq;
        if ((s0 & 1U) != 0U)
        {
            continue;
        }
        high = p->high;
        low  = p->low;
        s1 = p->seq;
    } while ((s0 != s1) || ((s1 & 1U) != 0U));

    return (((uint64_t)high << 32U) | low);
}
```

真正用于多核时还必须加入合适的原子操作和内存序，不能只依靠`volatile`。

---

## 10. 浮点类型与FPU

### 10.1 C类型不等于硬件一定支持

```c
float  a;
double b;
```

是否由硬件FPU直接执行取决于：

- CPU实现；
- 编译器`-mfpu`、浮点ABI等选项；
- 目标是否支持单精度/双精度；
- 库函数实现；
- RTOS是否保存FPU上下文。

Cortex-M7实现可能配置单精度或双精度FPU，必须查询具体内核配置。AURIX TC3xx的TriCore FPU能力与编译选项也必须以具体器件和工具链为准。

### CASE-05：浮点ABI不一致

一个库按hard-float ABI编译，应用按soft/softfp ABI编译，可能产生：

- 链接器直接拒绝；
- 参数传递寄存器不一致；
- 运行结果错误。

系统要求：所有对象库必须统一CPU、FPU、ABI和endian相关编译选项，并在构建系统中集中定义。

---

## 11. 布尔与状态类型

使用`<stdbool.h>`：

```c
bool ready = false;
```

但不能假设外设寄存器、协议帧或Flash存储中的布尔编码与`bool`对象布局相同。跨接口应显式序列化：

```c
uint8_t encoded = ready ? UINT8_C(1) : UINT8_C(0);
```

状态机推荐：

```c
typedef enum
{
    MODE_INIT = 0,
    MODE_RUN,
    MODE_SAFE
} Mode_t;

typedef uint8_t ModeStorage_t;
```

枚举用于程序语义，固定宽度类型用于NVM/通信布局。

---

## 12. Cortex-M7与TC3xx访问宽度实例

### 12.1 Cortex-M7

对普通RAM，编译器可能根据类型选择：

```text
uint8_t  → LDRB/STRB
uint16_t → LDRH/STRH
uint32_t → LDR/STR
uint64_t → 指令组合或成对传输，依目标与优化而定
```

但最终行为还受：

- MPU Memory Type；
- 对齐；
- `SCB->CCR.UNALIGN_TRP`；
- 总线Slave能力；
- Cache Line与ECC粒度。

### 12.2 AURIX TC3xx

TriCore同样根据C类型和指令选择形成byte/half-word/word/double-word访问。TC3xx部分本地SRAM以64-bit数据计算ECC，sub-64-bit写可能在存储器接口执行read-modify-write。

因此：

> C代码写一个byte，不代表SRAM阵列只执行一个byte的物理写入。

这对未初始化ECC存储器、并发访问和故障注入测试尤其重要。

---

## 13. 工程案例

### CASE-06：寄存器地址计算溢出

错误写法：

```c
#define BASE_ADDR  0xF0000000
#define REG_ADDR(n) (BASE_ADDR + ((n) * 0x1000))
```

问题：常量类型、`n`类型和乘法溢出均不明确。建议：

```c
#define BASE_ADDR  UINT32_C(0xF0000000)
#define REG_STRIDE UINT32_C(0x00001000)

static inline uintptr_t RegAddr(uint32_t n)
{
    return ((uintptr_t)BASE_ADDR + ((uintptr_t)n * (uintptr_t)REG_STRIDE));
}
```

同时检查`n`范围。

### CASE-07：长度减一导致下溢

```c
void Process(const uint8_t *data, uint32_t length)
{
    for (uint32_t i = 0U; i <= (length - 1U); i++)
    {
        Use(data[i]);
    }
}
```

当`length==0U`时，`length-1U`变成`UINT32_MAX`。正确写法：

```c
for (uint32_t i = 0U; i < length; i++)
{
    Use(data[i]);
}
```

### CASE-08：负错误码存入无符号变量

```c
uint32_t status = Driver_Init(); /* Driver_Init返回int32_t */

if (status < 0U)
{
    /* 永远不成立 */
}
```

正确做法：接口返回类型保持一致：

```c
int32_t status = Driver_Init();

if (status < 0)
{
}
```

---

## 14. 验证实验

### EXP-01：整数提升

**条件**：M7和TC3xx分别以`-O0/-O2`编译。  
**步骤**：对`uint8_t`加法、取反、移位生成汇编。  
**观测**：寄存器宽度、截断指令、常量折叠。  
**预期**：结果符合整数提升规则，优化只改变实现不改变已定义语义。

### EXP-02：有符号溢出

**步骤**：编译`return x + 1 > x;`并查看不同优化等级。  
**预期**：理解编译器为何可将表达式化简；不得将此作为编译器Bug。

### EXP-03：64-bit撕裂

**条件**：高频ISR更新64-bit计数，任务持续读取。  
**步骤**：比较直接读取、关中断、sequence counter。  
**预期**：直接读取可能出现不一致；保护方案不得出现非法组合。

### EXP-04：访问宽度

**步骤**：分别通过`uint8_t/uint16_t/uint32_t/uint64_t`指针访问对齐RAM，检查反汇编和总线波形。  
**预期**：区分C对象访问宽度、CPU指令宽度和存储器物理ECC粒度。

---

## 15. 编码规范建议

1. 跨模块接口优先使用固定宽度整数类型；
2. 地址算术使用`uintptr_t`；
3. 计数回绕使用无符号类型并明确最大时间窗；
4. 禁止依赖有符号溢出；
5. 位移左操作数使用明确的无符号宽度；
6. 宽乘法在运算前扩展操作数；
7. 不直接用枚举对象布局作为通信/NVM格式；
8. 关键ABI假设使用`_Static_assert`；
9. 32-bit平台共享64-bit对象必须显式设计原子读取方案；
10. 外设访问宽度必须符合IP寄存器规范。

---

## 16. 系统需求推导

| ID | 系统需求示例 | 验证证据 |
|---|---|---|
| SYS-C-TYPE-001 | 跨模块、通信和持久化接口应使用明确宽度的整数类型，不得依赖`int/long/enum`的实现宽度。 | 接口审查、`_Static_assert`、跨工具链构建。 |
| SYS-C-ARITH-001 | 涉及量程、缩放、地址和长度的表达式应分析中间结果宽度，扩展必须发生在运算之前。 | 边界值单元测试、编译器Warning、UBSan主机测试。 |
| SYS-C-OVERFLOW-001 | 不得依赖有符号整数溢出；需要模运算时应使用无符号类型并定义有效时间窗或量程。 | `-O0/-O2`差异测试、静态分析、最大/最小值测试。 |
| SYS-C-SHIFT-001 | 位移量应小于提升后左操作数的位宽，左操作数应具有明确的无符号类型。 | 静态分析、位宽边界测试、反汇编抽查。 |
| SYS-C-WIDE-001 | 32-bit MCU上跨执行上下文共享64-bit对象时，应定义一致快照机制，不得假定单次C读写原子。 | ISR/任务压力测试、撕裂检测、临界区或sequence counter评审。 |
| SYS-C-MMIO-000 | 外设对象的C访问类型和宽度应与寄存器规范一致；不得由方便的指针强转决定事务宽度。 | 寄存器规范追踪、反汇编和总线Trace。 |

这些条目是“可验证的系统约束”，不是单纯的代码风格。项目可以继续拆成软件需求、设计约束和测试用例，并把最后一列纳入交付证据。

---

## 17. 面试与评审问题

1. `uint8_t a, b;`，`a+b`是什么类型？
2. 为什么`1 << 31`存在问题？
3. `uint64_t result = a * b;`为什么可能仍然先32-bit溢出？
4. 无符号回绕为什么可以用于超时判断？适用边界是什么？
5. 有符号溢出为什么会影响`-O2`结果？
6. `uint32_t`和`uint_fast32_t`分别适合什么？
7. 为什么`enum`不应直接作为CAN报文格式？
8. 32-bit CPU读取对齐的64-bit对象是否一定原子？
9. C访问一个byte时，ECC SRAM内部为什么可能执行64-bit RMW？
10. 如何证明项目中`int`、指针、`long`和`double`的实际宽度？

---

## 18. 小结

本章最重要的不是记住某个结果，而是建立以下判断顺序：

```text
先确定每个操作数的类型
→ 执行整数提升和通常算术转换
→ 判断运算是否溢出或未定义
→ 判断赋值时是否截断
→ 再看编译器选择什么指令
→ 最后分析总线、对齐和ECC行为
```

下一章进入指针、数组、函数指针、别名与生命周期，这是把“对象”连接到“地址访问”的关键一步。
