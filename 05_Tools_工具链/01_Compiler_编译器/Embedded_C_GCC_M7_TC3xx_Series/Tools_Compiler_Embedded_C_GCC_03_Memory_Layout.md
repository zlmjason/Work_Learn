# 嵌入式C内存布局与关键字

---

## 系列导航

- **返回总纲**：[[Tools_Compiler_Embedded_C_GCC_00_Series_Overview|00 学习总纲与进度]]
- **上一篇**：[[Tools_Compiler_Embedded_C_GCC_02_Pointers_Arrays|02_Pointers_Arrays]]
- **下一篇**：[[Tools_Compiler_Embedded_C_GCC_04_Struct_Alignment|04_Struct_Alignment]]

---


> 本章目标：把`const/volatile/static/extern/inline/restrict`与对象存储期、ELF Section、链接地址、复位初始化、Cache和总线可见性连接起来。

---

## 1. 一张图理解变量从源码到RAM

```c
static uint32_t g_count = 10U;
```

典型过程：

```text
C源码中的定义
  ↓
编译器在.o中生成Symbol和.data输入Section
  ↓
链接器为.data分配RAM运行地址VMA
  ↓
链接器同时在Flash映像分配初值加载地址LMA
  ↓
复位后启动代码从LMA复制到VMA
  ↓
main中CPU访问RAM里的g_count
```

所以一个初始化RAM变量同时消耗：

- Flash中的初值空间；
- RAM中的运行空间；
- 启动时复制时间。

---

## 2. 典型Section

| Section | 典型内容 | 运行位置 | 启动处理 |
|---|---|---|---|
| `.text` | 机器代码 | Flash/ROM/PSPR/ITCM | 通常不复制，RAM代码例外 |
| `.rodata` | 只读常量、字符串 | 常见为Flash | 通常无需处理 |
| `.data` | 非零初值静态对象 | RAM | 从Flash LMA复制 |
| `.bss` | 零初值/无显式初值静态对象 | RAM | 清零 |
| `.noinit` | 保留对象 | RAM | 不清零、不复制 |
| Stack | 自动对象、保存现场 | RAM | 设置初始SP/栈区 |
| Heap | 动态分配区域 | RAM | 由运行库管理 |
| Vector/Trap | 异常入口表 | Flash/RAM | 对齐并配置基址 |
| CSA | TC3xx上下文区 | DSPR/LMU等允许区 | 初始化链表 |

Section名称不是C标准规定，而是编译器、链接器和项目约定。

---

## 3. 存储期、作用域和链接属性

三个概念必须分开。

### 3.1 自动存储期

```c
void Func(void)
{
    uint32_t local = 1U;
}
```

`local`通常位于栈或寄存器，进入块时生命周期开始，离开块时结束。优化后可能完全没有内存位置。

### 3.2 静态存储期

```c
static uint32_t file_state;

void Func(void)
{
    static uint32_t call_count;
}
```

二者都从程序启动到结束一直存在，但作用域和链接不同：

- `file_state`：文件作用域、内部链接；
- `call_count`：块作用域、无链接。

### 3.3 外部链接

```c
/* state.c */
uint32_t g_state;

/* state.h */
extern uint32_t g_state;
```

对象在不同Translation Unit之间通过Symbol解析。

### 3.4 线程存储期

标准C可有线程局部对象，但裸机/RTOS工具链支持、运行库初始化和内存成本必须单独确认，不能默认等同于RTOS Task Local Storage。

---

## 4. `.data`与`.bss`

### 4.1 为什么无初值全局变量在`.bss`

```c
uint32_t g_a;
static uint32_t g_b = 0U;
```

二者通常都可放入`.bss`，因为启动时统一清零比在Flash保存大量0更节省映像空间。

### CASE-01：启动代码漏清`.bss`

现象：

- 上电第一次运行似乎正常；
- Debugger连接后或warm reset表现不同；
- 状态机从随机状态启动。

证据链：

1. Map确认对象在`.bss`；
2. Linker Symbol确认`_sbss/_ebss`；
3. 检查Reset Handler循环；
4. 在main第一条语句前观察RAM；
5. 区分BootROM RAM初始化与C运行时清零。

正确启动逻辑：

```c
extern uint32_t __bss_start__;
extern uint32_t __bss_end__;

static void ClearBss(void)
{
    uint32_t *p = &__bss_start__;
    while (p < &__bss_end__)
    {
        *p++ = 0U;
    }
}
```

符号名称由链接脚本决定。

### CASE-02：`.data`复制源/目标错误

```c
uint32_t g_magic = 0x12345678U;
```

如果LMA、VMA或复制长度错误，运行时可能得到：

- 0；
- 旧RAM内容；
- 邻近Flash数据；
- 部分初始化。

必须同时检查：

- ELF Section的VMA/LMA；
- BIN是否包含初值；
- 启动复制表；
- 复制单位和尾部处理；
- Cache/ECC初始化约束。

---

## 5. `.noinit`不是自动可靠的保留数据

```c
__attribute__((section(".noinit")))
static uint32_t reset_reason;
```

还需要链接脚本：

```ld
.noinit (NOLOAD) :
{
    __noinit_start__ = .;
    *(.noinit*)
    __noinit_end__ = .;
} > RAM
```

### 风险

- 某些复位源会清除该RAM；
- BootROM/SSW可能执行RAM初始化或ECC初始化；
- Debug下载可能重写RAM；
- 启动清零循环范围可能误覆盖；
- 保留内容没有CRC，无法判断有效性；
- 软件版本升级后结构体布局变化。

建议格式：

```c
typedef struct
{
    uint32_t magic;
    uint16_t version;
    uint16_t length;
    uint32_t reset_count;
    uint32_t crc;
} RetainedData_t;
```

初始化时验证magic、version、length和CRC。

### 平台对比

- M7：取决于具体SoC复位域、SRAM Bank和BootROM行为；Cortex-M7内核本身不定义芯片RAM保留策略。
- TC3xx：需结合复位类型、SRI RAM实例、SSH/MBIST初始化和具体UCB/启动配置；不能仅凭“warm reset”推断所有RAM保持。

---

## 6. `const`

### 6.1 `const`表示不能通过该表达式修改

```c
const uint32_t value = 10U;
```

它不保证：

- 一定放在Flash；
- 一定是编译期常量；
- 绝不会被DMA/硬件改变；
- 地址不可被观察。

局部`const`对象可能在栈上：

```c
void Func(uint32_t input)
{
    const uint32_t doubled = input * 2U;
}
```

### 6.2 `const volatile`

只读硬件状态寄存器适合：

```c
const volatile uint32_t STATUS;
```

含义：

- 软件不能通过该成员写；
- 每次读仍必须真实访问，因为硬件可能改变。

### CASE-03：强转去掉`const`

```c
const uint32_t table[4] = {1U, 2U, 3U, 4U};
uint32_t *p = (uint32_t *)table;
*p = 9U;
```

如果原对象确实定义为`const`，通过强转修改属于未定义行为；若链接到PFlash，还可能引发总线错误或无效写。

---

## 7. `volatile`

### 7.1 它保证什么

对volatile对象的访问属于可观察行为，编译器必须按抽象机规则保留相应访问，不能把轮询值永久缓存于寄存器：

```c
while ((UART->STATUS & RX_READY) == 0U)
{
}
```

适用：

- MMIO寄存器；
- ISR与普通代码共享的简单标志；
- 被硬件异步更新的内存映射对象；
- 调试/故障注入要求保留的特定访问，但应谨慎。

### 7.2 它不保证什么

`volatile`不自动提供：

- 原子性；
- 互斥；
- 多变量事务一致性；
- Cache clean/invalidate；
- CPU内存屏障；
- 总线完成；
- 多核C内存模型同步；
- 访问目标合法。

### CASE-04：volatile计数丢失

```c
volatile uint32_t counter;

void ISR(void)
{
    counter++;
}

void Task(void)
{
    counter++;
}
```

`counter++`仍是Load-Add-Store。ISR在Task两步之间抢占会丢失一次更新。

### CASE-05：DMA Buffer全加volatile仍旧错误

```c
volatile uint8_t dma_buffer[1024];
```

如果M7 DCache中存在该Buffer的Dirty/Valid Line，DMA不通过CPU Cache访问RAM：

- CPU→DMA：需在启动DMA前clean相关Cache Line；
- DMA→CPU：需在DMA完成后invalidate相关Cache Line；
- 同时需要正确的屏障和Buffer所有权。

TC3xx也必须按目标地址是否经过DCache、使用DLMU/LMU的路径和DMA Master可见性处理。`volatile`不能改变Cache硬件状态。

---

## 8. 编译器屏障与CPU屏障

### 8.1 编译器屏障

典型GNU形式：

```c
__asm__ volatile ("" ::: "memory");
```

它告诉编译器内存可能变化，限制编译器跨越该点重排内存访问，但不生成CPU屏障指令。

### 8.2 Cortex-M7

| 指令 | 核心语义 |
|---|---|
| DMB | 对规定域内的显式内存访问建立顺序 |
| DSB | 等待规定的前序显式内存访问完成，再继续后续指令 |
| ISB | 刷新流水线，使后续指令观察新的执行上下文配置 |

具体使用必须结合CMSIS封装、Memory Type和SoC互连语义。

### 8.3 TC3xx

| 指令 | 核心语义 |
|---|---|
| DSYNC | 保证前序数据访问完成后才启动后序数据访问 |
| ISYNC | 使后续指令观察前序架构状态改变并同步指令执行 |

TC3xx手册还指出，对SRI/SPB目标，有时需DSYNC后再执行目标Slave范围read-back，才能把写完成推进到Slave侧。DSYNC也不会自动invalidate DCache。

---

## 9. `static`

### 9.1 文件作用域static

```c
static uint32_t module_state;
static void Module_Reset(void);
```

产生内部链接，避免全局命名空间污染，并允许编译器进行更强的Translation Unit内分析。

### 9.2 块作用域static

```c
uint32_t NextId(void)
{
    static uint32_t id;
    return id++;
}
```

对象只初始化一次且长期存在，但函数不再可重入：

- ISR/任务并发调用会竞争；
- 多核调用需要同步；
- 单元测试状态难重置；
- warm reset后是否保留仍由Section和启动决定。

### CASE-06：ISR中使用共享静态临时Buffer

```c
uint8_t *FormatMessage(uint32_t value)
{
    static uint8_t text[16];
    /* fill text */
    return text;
}
```

两个调用者会覆盖同一Buffer。正确接口应由调用者提供Buffer。

---

## 10. `extern`

`extern`解决符号可见性，不解决并发、初始化顺序或模块所有权。

错误模式：

```c
extern uint32_t g_status;
```

所有模块都可随意读写，最终无法判断谁拥有状态。推荐：

```c
/* module.h */
uint32_t Module_GetStatus(void);
void Module_SetMode(uint32_t mode);

/* module.c */
static uint32_t g_status;
```

只有确实需要跨模块共享、且所有权明确的对象才导出。

---

## 11. `inline`

标准C中的`inline`语义与链接规则容易受语言方言影响；GCC属性`always_inline`又是额外扩展。

头文件常用：

```c
static inline uint32_t RegRead(const volatile uint32_t *reg)
{
    return *reg;
}
```

`static inline`避免多Translation Unit外部定义冲突。

注意：

- `inline`只是建议，编译器可以不内联；
- 内联不等于宏，不会多次求值参数；
- 大量强制内联可能增加代码尺寸；
- 调试栈和覆盖率会改变；
- `-O0`下行为可能不同。

---

## 12. Stack与Heap

### 12.1 Stack

自动对象、溢出参数、保存寄存器和临时值可能使用栈。

Cortex-M7：

- Handler模式通常使用MSP；
- Thread模式可使用MSP或PSP；
- 异常入口硬件压入基础栈帧，FPU配置可能扩展；
- RTOS为任务分配独立PSP栈。

TC3xx：

- A10通常作为软件栈指针；
- CALL/中断/Trap的寄存器上下文大量依赖CSA；
- 局部数组、溢出参数仍可能使用软件栈；
- CSA耗尽和普通栈溢出是两类不同故障。

### CASE-07：大局部数组导致栈溢出

```c
void Process(void)
{
    uint8_t temp[8192];
}
```

定位：

- Map只能看到静态栈预留，未必看到动态最深使用；
- 使用stack usage文件、栈水位填充、MPU guard；
- 检查递归、中断嵌套和FPU上下文；
- TC3xx同时检查CSA链表余量。

### 12.2 Heap

车规嵌入式通常限制运行期动态分配，原因包括：

- 碎片；
- 非确定延迟；
- 分配失败；
- 线程安全；
- 生命周期复杂；
- 难以证明最坏情况。

若必须使用，应采用固定块池、启动阶段分配或具备确定性的专用分配器，并明确失败策略。

---

## 13. 自定义Section

```c
__attribute__((section(".fast_data"), aligned(32)))
static uint8_t fast_buffer[256];
```

仅添加属性不够，还需要：

1. 链接脚本收集`.fast_data*`；
2. 分配正确VMA；
3. 如有初值，分配LMA和启动复制；
4. 配置MPU/Cache属性；
5. 检查对齐、容量、访问Master；
6. 通过Map/ELF验证。

### 平台实例

- M7：`.itcm_text`、`.dtcm_data`、non-cacheable DMA区；
- TC3xx：PSPR代码、DSPR私有数据、DLMU共享数据、LMU等区域。

不能仅按地址快慢决定布局，还要考虑：

- 本地/远端访问；
- DMA可达性；
- Cache一致性；
- ECC；
- 多核别名地址；
- 复位保持；
- 功能安全诊断。

---

## 14. 复位视角下的对象

| 对象类型 | Power-on Reset | Warm/System Reset | Application/Core Reset |
|---|---|---|---|
| `.data` | C启动重新复制 | 通常由启动路径决定 | 取决于是否重新执行C初始化 |
| `.bss` | C启动清零 | 同上 | 同上 |
| `.noinit` | 物理RAM可能未知 | 可能保留 | 可能保留 |
| Cache | 通常需失效/初始化 | 依复位域 | 依CPU/Cache复位行为 |
| 外设寄存器 | 按复位类型 | 按模块复位定义 | 可能不复位 |

这个表不能替代芯片手册。尤其M7只定义内核行为，不定义SoC SRAM和外设复位域。

---

## 15. 验证实验

### EXP-01：对象到Section追踪

定义以下对象：

```c
const uint32_t c0 = 1U;
uint32_t d0 = 2U;
uint32_t b0;
static uint32_t s0;
```

通过`readelf/nm/objdump/Map`确认Section、地址和Symbol链接属性。

### EXP-02：启动初始化

在Reset Handler的`.data`复制前、复制后、`.bss`清零后分别断点观察RAM。M7与TC3xx分别完成。

### EXP-03：`.noinit`复位矩阵

对每类复位源：

1. 写入magic和CRC；
2. 触发复位；
3. 在最早启动阶段读取；
4. 记录是否被BootROM/启动代码/硬件改变。

### EXP-04：volatile与优化

比较普通变量和volatile变量的轮询汇编；再由DMA修改RAM，证明即使volatile也不能自动解决Cache旧副本。

### EXP-05：自定义Section

将函数和数据分别放入ITCM/PSPR与DTCM/DSPR，验证VMA/LMA、复制、入口地址和性能。

---

## 16. 编码与系统规范建议

1. 模块内部状态默认文件作用域`static`；
2. 头文件只声明，不定义普通全局对象；
3. `.noinit`对象包含magic、版本、长度和CRC；
4. MMIO使用准确的`volatile/const volatile`访问类型；
5. 不用`volatile`替代同步、原子和Cache维护；
6. 大型局部对象和递归需经过栈预算；
7. 运行期动态分配需有明确安全论证；
8. 自定义Section必须同时评审链接、启动、MPU、Cache和DMA；
9. 每类复位源都应验证对象初始化策略；
10. 关键Section应在链接脚本中使用`ASSERT`检查越界。

---

## 17. 系统需求推导

| ID | 系统需求示例 | 验证证据 |
|---|---|---|
| SYS-MEM-INIT-001 | 启动软件应依据链接器生成的边界完成`.data`复制和`.bss`清零，不得在源码中重复维护地址常量。 | Reset后RAM检查、Map/Symbol对照。 |
| SYS-MEM-RET-001 | `.noinit`或保留RAM数据应定义适用复位源、magic、版本、长度、CRC及失效回退策略。 | 复位矩阵、破坏性CRC和版本升级测试。 |
| SYS-C-VOL-001 | `volatile`仅用于需要可观察访问的对象，不得作为原子性、互斥、内存序或Cache一致性机制。 | 代码审查、并发和DMA Cache测试。 |
| SYS-MEM-STACK-001 | 每个任务、ISR和Core的软件栈应有静态预算与运行期水位监控；TC3xx CSA预算应独立管理。 | Stack用量报告、最坏嵌套压力测试、CSA监控。 |
| SYS-MEM-HEAP-001 | 安全相关运行阶段原则上不得使用无界动态分配；若使用，应定义池容量、耗尽行为和确定性上界。 | 资源耗尽测试、时延测量。 |
| SYS-MEM-SECTION-001 | 自定义Section应同时定义VMA、LMA、复制/清零责任、访问者、MPU/Cache属性和越界断言。 | Linker Map、启动后内容检查、MPU测试。 |
| SYS-MEM-RESET-001 | 每类复位源应明确哪些内存域保留、重置或状态不确定，并由启动软件执行相应初始化策略。 | 冷启动、系统复位、看门狗复位及核复位测试。 |

这组需求把`const/volatile/static`从“关键字知识”落到启动、复位、内存保护和故障恢复职责上，适合继续分配给Linker、Startup、诊断和测试模块。

---

## 18. 面试与评审问题

1. 为什么`.data`同时占Flash和RAM？
2. `.bss`是否一定不占ELF文件空间？为什么BIN常不保存大量零？
3. `const`变量是否一定在Flash？
4. `volatile`保证了什么，没保证什么？
5. `const volatile`适合什么寄存器？
6. 编译器屏障和CPU屏障有什么区别？
7. M7的DMB/DSB/ISB与TC3xx的DSYNC/ISYNC如何对应，为什么不能简单画等号？
8. `.noinit`为什么还需要CRC和复位矩阵测试？
9. TC3xx的CSA和软件栈分别保存什么类别的状态？
10. 只加`section(".ram_code")`为什么不足以让函数从RAM执行？

---

## 19. 小结

一个对象的真实状态由多层共同决定：

```text
C关键字决定语言访问约束
→ 编译器决定Symbol和输入Section
→ 链接器决定VMA/LMA
→ 启动代码决定初值是否到位
→ MPU/Cache/总线决定访问是否可见和可达
→ 复位与并发决定对象是否仍可信
```

下一章将处理结构体、Padding、packed、位域、W1C和寄存器Read-Modify-Write，这些问题直接连接总线访问和外设语义。
