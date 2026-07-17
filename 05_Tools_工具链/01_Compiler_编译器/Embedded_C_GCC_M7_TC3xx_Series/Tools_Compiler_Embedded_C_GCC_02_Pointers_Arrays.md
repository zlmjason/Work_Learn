# 嵌入式C指针、数组与函数指针

---

## 系列导航

- **返回总纲**：[[Tools_Compiler_Embedded_C_GCC_00_Series_Overview|00 学习总纲与进度]]
- **上一篇**：[[Tools_Compiler_Embedded_C_GCC_01_Object_Model|01_Object_Model]]
- **下一篇**：[[Tools_Compiler_Embedded_C_GCC_03_Memory_Layout|03_Memory_Layout]]

---


> 本章目标：从“指针保存地址”深入到类型缩放、对象边界、对齐、生命周期、别名规则、MMIO、DMA和函数调用。  
> 核心原则：一个数值上看似正确的地址，不一定是一个语言层面有效、硬件层面可访问的指针。

---

## 1. 指针包含哪些语义

```c
uint32_t *p;
```

它至少表达：

- `p`保存某个`uint32_t`对象的地址；
- `*p`按`uint32_t`宽度和对齐要求访问；
- `p + 1`跨过`sizeof(uint32_t)`字节；
- 编译器可基于类型做别名和优化推理；
- 目标地址还必须满足MPU、总线和Slave权限。

因此下面两个指针即使数值相同，生成的访问也可能不同：

```c
volatile uint8_t  *p8  = (volatile uint8_t  *)ADDR;
volatile uint32_t *p32 = (volatile uint32_t *)ADDR;
```

---

## 2. 指针声明的阅读方法

从变量名向外读：

```c
uint32_t *p;                 /* p是指向uint32_t的指针 */
uint32_t * const p0 = ...;   /* p0不可改，所指对象可改 */
const uint32_t *p1;          /* p1可改，不能通过p1修改对象 */
uint32_t const *p2;          /* 与p1相同 */
const uint32_t * const p3;   /* 指针和所指对象均不可通过该名字修改 */
volatile uint32_t *p4;       /* 每次访问所指对象都必须形成volatile访问 */
uint32_t * volatile p5;      /* 指针对象p5本身可能异步变化 */
volatile uint32_t * const p6 = ...; /* 常用于固定地址MMIO */
```

推荐MMIO形式：

```c
#define UART_STATUS_ADDR UINT32_C(0x40001000)

static volatile uint32_t * const UartStatus =
    (volatile uint32_t *)(uintptr_t)UART_STATUS_ADDR;
```

但实际工程通常使用厂商提供的寄存器结构体和访问宏，以包含正确的访问权限和对齐。

---

## 3. 指针算术与对象边界

```c
uint32_t buffer[8];
uint32_t *p = &buffer[0];

p + 1; /* 数值增加4字节，而不是1字节 */
```

C只允许在同一个数组对象及其“尾后一个位置”范围内形成和比较相关指针。尾后指针可以比较，但不能解引用：

```c
uint32_t *end = &buffer[8]; /* 可以形成 */
/* *end;                    不允许解引用 */
```

### CASE-01：寄存器步长错误

```c
volatile uint32_t *base = (volatile uint32_t *)PERIPH_BASE;
volatile uint32_t *reg = base + 0x20U;
```

这里地址增加`0x20 * 4 = 0x80`字节。如果寄存器偏移是字节单位，应写：

```c
volatile uint32_t *reg =
    (volatile uint32_t *)((uintptr_t)PERIPH_BASE + UINT32_C(0x20));
```

---

## 4. 数组与指针不是同一个对象

```c
uint32_t a[4];
uint32_t *p = a;
```

数组表达式在多数场合会转换为首元素指针，但：

```c
sizeof(a)  /* 16 */
sizeof(p)  /* 32-bit平台通常为4 */
&a        /* 类型是uint32_t (*)[4] */
&a[0]     /* 类型是uint32_t * */
```

### CASE-02：函数参数中的`sizeof`

```c
void Clear(uint8_t data[32])
{
    memset(data, 0, sizeof(data)); /* 错误：sizeof(data)是指针大小 */
}
```

函数形参数组调整为指针。正确接口必须传长度：

```c
void Clear(uint8_t *data, size_t length)
{
    memset(data, 0, length);
}
```

或使用固定对象封装：

```c
typedef struct
{
    uint8_t bytes[32];
} Block32_t;

void ClearBlock(Block32_t *block)
{
    memset(block->bytes, 0, sizeof(block->bytes));
}
```

---

## 5. 数组指针与指针数组

```c
uint32_t *table[4];     /* 4个元素，每个元素是uint32_t指针 */
uint32_t (*matrix)[4];  /* 指向“含4个uint32_t的数组”的指针 */
```

二维数组参数：

```c
void Process(uint32_t matrix[][4], size_t rows)
{
    /* matrix实际类型为uint32_t (*)[4] */
}
```

第二维必须已知，因为编译器需要计算：

```text
matrix[i][j]地址 = base + i * 4 * sizeof(uint32_t) + j * sizeof(uint32_t)
```

---

## 6. `void *`与通用接口

对象指针可以与`void *`相互转换：

```c
void *context;
```

典型用于：

- 回调上下文；
- RTOS任务参数；
- 通用Buffer；
- 驱动实例句柄。

但`void *`会丢失：

- 目标对象类型；
- 长度；
- 对齐信息；
- 所有权和生命周期；
- 可读/可写属性。

推荐把上下文类型固定在注册接口旁：

```c
typedef void (*Callback_t)(void *context, uint32_t event);

typedef struct
{
    Callback_t fn;
    void *context;
} CallbackEntry_t;
```

回调文档必须说明`context`由谁创建、存活多久、能否在ISR访问。

---

## 7. 函数指针

```c
typedef int32_t (*DriverInit_t)(uint32_t instance);
```

函数指针类型必须匹配参数和返回类型。通过不兼容类型强转后调用属于未定义行为：

```c
void Handler(void);
typedef void (*HandlerWithArg_t)(uint32_t);

HandlerWithArg_t bad = (HandlerWithArg_t)Handler;
bad(1U); /* 未定义行为 */
```

### 7.1 Cortex-M7函数地址

ARMv7-M只执行Thumb指令，异常向量中的处理函数地址要求Thumb状态指示符合架构要求。直接手工修改函数地址最低位可能导致UsageFault/HardFault。

正确做法：

- 使用函数指针和链接器符号；
- 不对函数地址做未经ABI保证的整数运算；
- 向量表项由链接器和工具链生成；
- 重映射VTOR时保证表对齐和内容完整。

### 7.2 TC3xx函数地址

TriCore没有M-profile的Thumb位语义，但仍受：

- 指令对齐；
- Code MPU；
- cached/non-cached地址别名；
- PFlash/PSPR映射；
- ABI调用约定。

将任意数据地址强转成函数指针并调用在两个平台上都不安全。

---

## 8. 生命周期：地址仍在，不代表对象仍存在

### CASE-03：返回局部变量地址

```c
uint32_t *GetValue(void)
{
    uint32_t value = 10U;
    return &value;
}
```

函数返回后`value`生命周期结束，返回指针成为悬空指针。Debug版本“偶尔能读到10”只是栈内容尚未覆盖，不代表行为有效。

M7通常表现为：

- `value`位于当前MSP/PSP栈帧；
- 下一个函数/中断可能覆盖该位置。

TC3xx中：

- 自动对象通常仍在A10所指软件栈区域；
- 函数调用的上层寄存器上下文可能由CSA管理；
- CSA不延长局部变量生命周期。

正确方式：

- 调用者提供输出Buffer；
- 返回值；
- 明确管理的静态对象，但要处理重入；
- 动态分配（车规嵌入式通常需严格限制）。

```c
bool GetValue(uint32_t *out)
{
    if (out == NULL)
    {
        return false;
    }
    *out = 10U;
    return true;
}
```

---

## 9. 对齐与非对齐指针

### CASE-04：`uint8_t`数组强转为`uint64_t *`

```c
uint8_t buf[16];
uint64_t *p = (uint64_t *)&buf[1];
uint64_t v = *p;
```

存在至少四层问题：

1. `&buf[1]`通常不满足`uint64_t`对齐；
2. 通过不兼容类型访问数组可能违反有效类型/别名规则；
3. 读取8字节可能跨越硬件边界；
4. 即使CPU能拆分非对齐访问，Device Memory或特定Slave仍可能报错。

### Cortex-M7

- 部分普通内存非对齐访问可由内核处理；
- 某些指令或多字访问仍要求对齐；
- `SCB->CCR.UNALIGN_TRP`可使部分非对齐访问产生UsageFault；
- Device/Strongly-ordered类区域不能套用普通RAM结论；
- 跨Cache Line、MPU Region或总线Slave边界风险更高。

### TC3xx

- 指令和DMI对齐行为需按具体访问宽度、地址和存储区域判断；
- TC3xx文档指出部分CPU数据访问支持16-bit对齐，但这不等价于任意64-bit C对象均可放在奇地址；
- 本地SRAM ECC和sub-width写可能引入RMW；
- 非自然对齐仍可能改变事务数量和原子性。

安全解码方式：

```c
uint64_t LoadLe64(const uint8_t *p)
{
    uint64_t value;
    memcpy(&value, p, sizeof(value));
    return value; /* 小端目标；跨端序协议还需显式转换 */
}
```

`memcpy`表达的是按字节搬运，编译器可在确认安全时优化成高效指令。

---

## 10. Effective Type与Strict Aliasing

### CASE-05：用指针强转重解释浮点

```c
float f = 1.0F;
uint32_t bits = *(uint32_t *)&f; /* 不推荐，可能违反别名规则 */
```

正确方式：

```c
uint32_t bits;
memcpy(&bits, &f, sizeof(bits));
```

GCC在`-O2`且启用strict aliasing时，可以假设不兼容类型的指针不会指向同一对象。这会使错误代码在`-O0`正常、`-O2`异常。

不要把`-fno-strict-aliasing`当成永久修复；它只是放宽编译器优化假设，无法修复对齐、生命周期和对象边界问题。

### 字符类型例外

允许通过字符类型观察对象表示：

```c
const unsigned char *bytes = (const unsigned char *)&object;
```

但把任意字节序列直接当成结构体对象使用，还要考虑有效类型、对齐、Padding、Trap Representation和协议端序。

---

## 11. `restrict`：给优化器的无别名承诺

```c
void Copy(uint32_t * restrict dst,
          const uint32_t * restrict src,
          size_t count)
```

它承诺在相关执行期间，通过`dst`访问的对象不会同时通过与`src`冲突的路径访问。违反承诺会导致未定义行为。

错误调用：

```c
uint32_t data[8];
Copy(&data[1], &data[0], 7U); /* 源目标重叠，违背restrict接口 */
```

若允许重叠，应使用类似`memmove`的语义，而不是`restrict`。

---

## 12. MMIO指针

典型寄存器结构：

```c
typedef struct
{
    volatile uint32_t CTRL;
    const volatile uint32_t STATUS;
    volatile uint32_t DATA;
} UartRegs_t;

#define UART0 ((UartRegs_t *)(uintptr_t)UART0_BASE)
```

需要额外保证：

- 结构体成员偏移与手册一致；
- Padding由静态断言验证；
- 访问宽度正确；
- `STATUS`的只读语义准确；
- 地址区域属性配置为Device/Non-cacheable等合适类型；
- 受保护寄存器遵循解锁/ENDINIT流程；
- 写后需要的屏障/read-back已封装。

```c
_Static_assert(offsetof(UartRegs_t, STATUS) == 4U, "STATUS offset mismatch");
```

### CASE-06：错误保留寄存器布局

```c
typedef struct
{
    volatile uint32_t CTRL;  /* 0x00 */
    volatile uint32_t DATA;  /* 实际硬件偏移0x10 */
} BadRegs_t;
```

编译器会把`DATA`放在偏移0x04。需要显式保留数组：

```c
typedef struct
{
    volatile uint32_t CTRL;
    uint32_t RESERVED0[3];
    volatile uint32_t DATA;
} GoodRegs_t;
```

---

## 13. DMA指针与所有权

### CASE-07：把栈Buffer交给异步DMA

```c
void StartTransfer(void)
{
    uint8_t tx[64];
    Fill(tx);
    Dma_Start(tx, sizeof(tx));
} /* tx生命周期结束，但DMA可能仍在读取 */
```

这是典型悬空Buffer。正确设计：

- 静态或专用DMA池；
- 调用者保证直到完成回调前对象存活；
- 通过状态机管理所有权；
- M7 Cacheable Buffer执行正确的clean；
- TC3xx根据DCache/DLMU/LMU映射处理一致性；
- 地址满足DMA对齐和可访问范围。

建议接口：

```c
typedef struct
{
    uint8_t *data;
    size_t length;
    void (*complete)(void *context, int32_t status);
    void *context;
} DmaRequest_t;
```

接口文档必须规定谁拥有`data`、何时可以复用。

---

## 14. 回调函数生命周期

### CASE-08：回调上下文指向局部变量

```c
void Configure(void)
{
    uint32_t local = 1U;
    RegisterCallback(OnEvent, &local);
}
```

回调稍后执行时`local`已失效。正确做法是使用生命周期覆盖注册周期的对象：

```c
typedef struct
{
    uint32_t state;
} ModuleContext_t;

static ModuleContext_t g_ctx;

void Configure(void)
{
    RegisterCallback(OnEvent, &g_ctx);
}
```

如果回调运行在ISR，还要进一步分析并发访问。

---

## 15. 空指针检查的边界

```c
if (p != NULL)
{
    value = *p;
}
```

这里只排除了空指针，不能证明：

- 指针指向有效对象；
- 对象仍在生命周期内；
- 地址满足对齐；
- MPU允许访问；
- 地址不是未实现Slave；
- DMA未同时改变所有权。

安全接口更依赖所有权、范围、类型和状态机，而不是到处添加空指针检查。

---

## 16. 双平台异常定位

### Cortex-M7

错误指针可能引发：

- MemManage Fault；
- BusFault；
- UsageFault；
- escalation到HardFault。

关键证据：

- stacked PC/LR；
- CFSR/HFSR；
- BFAR/MMFAR有效位和地址；
- 反汇编中的Load/Store宽度；
- MPU配置。

### AURIX TC3xx

错误数据访问可能引发：

- Memory Protection Trap；
- Data Access Synchronous Error；
- Data Access Asynchronous Error；
- Alignment或完整性相关Trap，具体以Trap Class/TIN为准。

关键证据：

- Trap Class/TIN；
- DSTR/DATR/DEADD等相关寄存器；
- A11/CSA和保存上下文；
- 指令反汇编；
- MPU/Safety Protection配置。

---

## 17. 验证实验

### EXP-01：数组退化

比较全局数组、局部数组和函数形参数组中的`sizeof`，查看编译警告和运行结果。

### EXP-02：非对齐访问

**配置**：M7分别清零/置位`UNALIGN_TRP`；TC3xx分别测试DSPR、DLMU和外设区。  
**步骤**：对地址偏移0～7执行16/32/64-bit访问。  
**预期**：记录C合法性、CPU异常、总线事务和性能；不得把某个RAM测试结果推广到全部地址空间。

### EXP-03：strict aliasing

同一案例分别用`-O0`、`-O2`、`-O2 -fno-strict-aliasing`编译，比较错误强转和`memcpy`实现。

### EXP-04：函数指针

建立中断向量/回调表，验证正确原型；故意制造原型不匹配，观察Warning、反汇编和异常。

### EXP-05：DMA生命周期

使用栈Buffer与静态Buffer分别发起异步DMA，在完成前制造栈覆盖；结合Cache维护验证数据正确性。

---

## 18. 编码规范建议

1. 指针接口同时定义长度、方向和所有权；
2. 禁止返回自动局部对象地址；
3. 不通过不兼容指针类型重解释对象；
4. 二进制重解释优先使用`memcpy`；
5. 地址算术通过`uintptr_t`并检查溢出；
6. MMIO结构体使用`offsetof`静态断言；
7. 函数指针原型必须完全匹配；
8. 异步DMA/回调对象的生命周期必须覆盖完成时刻；
9. 非对齐访问不能仅凭“芯片支持”判断C代码合法；
10. `restrict`只用于能够真正满足无别名承诺的接口。

---

## 19. 系统需求推导

| ID | 系统需求示例 | 验证证据 |
|---|---|---|
| SYS-C-PTR-001 | 所有跨模块Buffer接口应同时定义基地址、长度、元素类型、访问方向和所有权。 | API审查、负向参数测试。 |
| SYS-C-LIFE-001 | 异步DMA、回调和中断保存的对象地址，其生命周期应覆盖最后一次可能访问。 | 生命周期分析、延迟完成和取消路径测试。 |
| SYS-C-ALIGN-000 | 指针转换前应证明目标对象类型、对齐和有效范围；“CPU支持非对齐”不得作为C合法性依据。 | `_Static_assert`、运行时断言、Fault/Trap注入。 |
| SYS-C-ALIAS-001 | 二进制表示重解释应使用`memcpy`或标准允许的字符类型访问，不得依赖违反effective type/aliasing规则的强转。 | `-O0/-O2/-fno-strict-aliasing`对照测试。 |
| SYS-C-CALL-001 | 函数指针、向量表和回调原型应在编译期保持完全兼容，不得通过强制转换消除诊断。 | `-Wcast-function-type`、符号/反汇编检查。 |
| SYS-C-MMIO-003 | MMIO寄存器映射应以`offsetof`和`sizeof`静态断言核对芯片寄存器偏移，不得依赖未验证的保留区。 | 构建期断言、SFR地址抽查。 |
| SYS-C-DMA-001 | DMA Buffer应位于允许访问的地址域，并满足对齐、Cache维护和并发所有权要求。 | Linker Map、MPU/Cache配置检查、DMA压力测试。 |

需求里的“证明”很重要：地址碰巧可访问、测试偶尔通过，都不能替代对象生命周期、类型和硬件可达性的证据。

---

## 20. 面试与评审问题

1. `sizeof(array)`与函数参数中的`sizeof(array)`为什么不同？
2. `&array`和`&array[0]`数值可能相同，类型和`+1`结果有什么不同？
3. `volatile uint32_t * const`怎样阅读？
4. 为什么CPU支持非对齐访问仍不能证明强转代码正确？
5. strict aliasing是什么？为什么`memcpy`通常是类型重解释的正确方式？
6. 函数指针原型不匹配为什么不能靠强转解决？
7. Cortex-M7函数地址最低位有什么架构含义？
8. TC3xx的CSA为什么不能延长局部变量生命周期？
9. DMA使用栈Buffer有什么风险？
10. 如何从Fault/Trap反推出错误指针的访问宽度和地址？

---

## 21. 小结

判断一个指针访问应依次回答：

```text
它指向的对象是否存在且仍在生命周期内？
→ 类型是否兼容？
→ 地址是否满足对齐？
→ 访问是否在对象边界内？
→ 编译器是否可基于别名规则重排/消除访问？
→ MPU和总线是否允许？
→ Cache、DMA和并发所有权是否正确？
```

下一章将把这些对象和地址映射到`.text/.data/.bss/.noinit`，并解释`volatile/const/static/extern`在编译器和MCU上的真实意义。
