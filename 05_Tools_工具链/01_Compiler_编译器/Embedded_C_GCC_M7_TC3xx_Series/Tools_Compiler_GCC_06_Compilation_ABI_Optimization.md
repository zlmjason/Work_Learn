# GCC编译流程、ABI、汇编与优化

---

## 系列导航

- **返回总纲**：[[Tools_Compiler_Embedded_C_GCC_00_Series_Overview|00 学习总纲与进度]]
- **上一篇**：[[Tools_Compiler_Embedded_C_GCC_05_Concurrency_UB|05_Concurrency_UB]]
- **下一篇**：[[Tools_Compiler_GCC_07_ELF_Sections_Debug|07_ELF_Sections_Debug]]

---


> 本章目标：理解一段C代码如何经过GCC前端、中间优化和后端生成M7/TriCore机器指令，并用ABI解释参数、返回值、栈帧、CSA和优化现象。

---

## 1. GCC不是一个单独步骤

```text
main.c
  ↓ 预处理
main.i
  ↓ 编译/优化
main.s
  ↓ 汇编
main.o
  ↓ 链接
app.elf
  ↓ objcopy
app.bin / app.hex
```

Arm示例：

```bash
arm-none-eabi-gcc -E main.c -o main.i
arm-none-eabi-gcc -S -mcpu=cortex-m7 -mthumb -O2 main.i -o main.s
arm-none-eabi-gcc -c -mcpu=cortex-m7 -mthumb main.s -o main.o
arm-none-eabi-gcc main.o -T link.ld -Wl,-Map=app.map -o app.elf
arm-none-eabi-objcopy -O binary app.elf app.bin
```

TriCore工具命令名随HighTec/GNU发行版变化，常见思路相同：预处理、编译为汇编、目标文件、链接ELF、再转换烧录格式。实际参数必须以项目工具链手册为准。

---

## 2. 预处理阶段

处理：

- `#include`；
- `#define`；
- 条件编译；
- `#pragma`；
- `#line`。

### CASE-01：实际编译的不是你看到的代码

```c
#ifdef ENABLE_CACHE
    Cache_Enable();
#endif
```

Debug/Release或不同Core Target的宏不一致，会使代码根本未进入Translation Unit。定位第一步：

```bash
arm-none-eabi-gcc -E -dD ... source.c -o source.i
```

检查：

- 宏最终值；
- 头文件搜索顺序；
- 条件分支；
- 寄存器定义；
- 编译命令是否属于预期Target。

---

## 3. Translation Unit

一个`.c`及其展开的头文件形成一个Translation Unit。编译器在传统非LTO模式下只能在该单元内进行完整语义分析。

```c
static void LocalHelper(void);
```

内部链接让编译器更容易：

- 删除未使用函数；
- 内联；
- 常量传播；
- 判断地址未逃逸。

LTO把更多跨文件信息带到链接优化阶段，但也会让调试、符号保留和函数边界发生变化。

---

## 4. 编译器优化的前提

编译器必须保持“具有已定义行为的程序”的可观察行为。它不需要为未定义行为保留程序员想象中的硬件结果。

因此：

```c
int32_t AddOne(int32_t x)
{
    return x + 1;
}
```

编译器可假设调用不会让有符号加法溢出。数组越界、悬空指针和数据竞争同理。

---

## 5. 优化等级

| 选项 | 定位 | 典型用途 |
|---|---|---|
| `-O0` | 几乎不优化 | 初步调试，不代表最接近真实发布行为 |
| `-Og` | 调试友好优化 | 开发调试 |
| `-O1` | 基础优化 | 中间选择 |
| `-O2` | 广泛性能优化 | 常见发布配置 |
| `-O3` | 更激进的循环/向量等优化 | 需评估代码尺寸和时序 |
| `-Os` | 尺寸优先 | Flash受限系统 |
| `-Ofast` | 放宽部分语言/数学约束 | 安全项目通常需谨慎 |
| `-flto` | 跨Translation Unit优化 | 发布构建，需验证调试/符号/GC |

车规项目应固定并配置管理：

- 编译器版本；
- 优化等级；
- CPU/ABI/FPU选项；
- 语言标准；
- Warning集合；
- LTO；
- 链接器和库版本。

---

## 6. ABI是什么

ABI定义二进制模块如何合作，包括：

- 参数放在哪些寄存器/栈；
- 返回值位置；
- 哪些寄存器由调用者/被调用者保存；
- 栈对齐；
- 结构体布局与传参；
- 浮点ABI；
- 符号、异常展开和调试格式。

两个源代码都“编译成功”不代表对象文件ABI兼容。

---

## 7. Cortex-M7 / AAPCS基础

常见AAPCS寄存器角色：

| 寄存器 | 常见角色 |
|---|---|
| R0-R3 | 参数、临时、返回值R0/R1 |
| R4-R11 | 被调用者保存 |
| R12 | 调用者保存临时寄存器IP |
| R13 | SP |
| R14 | LR |
| R15 | PC |

### 7.1 为什么R0-R3不由被调用函数保存

调用者已经知道调用会破坏R0-R3。如果调用后仍需原值，调用者在调用前保存或重新计算。

R4-R11则由被调用者保存：如果函数要使用它们，通常在入口压栈、返回前恢复。

### 7.2 示例

```c
uint32_t Add3(uint32_t a, uint32_t b, uint32_t c)
{
    return a + b + c;
}
```

代表性Thumb汇编可能为：

```asm
add r0, r0, r1
add r0, r0, r2
bx  lr
```

具体指令由GCC版本、选项和上下文决定。

### 7.3 第五个参数

前四个基础参数使用R0-R3，更多参数通常通过栈传递。结构体、64-bit和浮点参数还受对齐及ABI变体影响。

### 7.4 FPU ABI

必须统一：

- `-mfpu=...`；
- `-mfloat-abi=soft/softfp/hard`；
- 所有静态库；
- RTOS FPU上下文策略。

hard-float与softfp的函数参数位置可能不同，混用不是普通链接选项差异。

---

## 8. Cortex-M7函数栈帧

```c
uint32_t Func(uint32_t a)
{
    uint32_t local = a + 1U;
    return Helper(local) + 2U;
}
```

可能需要：

- 保存LR，因为函数还要调用Helper；
- 保存需跨调用保持的值；
- 为局部对象/溢出参数分配栈；
- 保持AAPCS栈对齐。

优化后`local`可能只存在于寄存器，甚至表达式被合并。

### 异常栈帧不是普通函数栈帧

Cortex-M异常入口硬件自动压入R0-R3、R12、LR、PC、xPSR等基础现场；FPU活动和懒栈配置可能扩展。Handler中的普通C函数仍遵循ABI。

---

## 9. TriCore TC1.6.2P调用与CSA

TriCore具有地址寄存器A和数据寄存器D两类寄存器。架构明确：

- A10通常作为栈指针；
- A11保存Return Address；
- CALL可自动把Upper Context保存到CSA，并更新A11；
- RET恢复相应上下文；
- 中断和Trap也使用CSA上下文机制。

Upper/Lower Context的精确寄存器集合由TriCore Architecture定义；参数寄存器、返回值、caller/callee-save集合由TriCore EABI和具体工具链规定。

### 为什么不要把AAPCS套到TriCore

M7普通函数主要通过软件序言压栈保存需要保持的寄存器；TriCore CALL可借助FCX/PCXI/CSA硬件上下文链。两者的：

- 调用成本；
- 栈分析；
- 中断入口；
- 上下文耗尽故障；
- 调试回溯方法

均不同。

### Fast Call

TriCore还存在FCALL/FRET类机制，减少完整CSA操作但改变保存责任。是否使用由编译器、选项和函数属性决定，不能假定所有调用都走同一路径。

---

## 10. M7与TC3xx函数调用对照案例

```c
uint32_t Sum(const uint32_t *p, uint32_t count)
{
    uint32_t sum = 0U;
    for (uint32_t i = 0U; i < count; i++)
    {
        sum += p[i];
    }
    return sum;
}
```

### M7观察点

- `p`与`count`通常从R0/R1进入；
- 返回值在R0；
- 可能使用后递增LDR；
- 小叶函数可不建立栈帧；
- `-O2`可能把索引循环转为尾指针循环。

### TC3xx观察点

- 地址参数和整数参数可能使用不同寄存器类别；
- Load与地址递增可利用TriCore寻址方式；
- 返回值寄存器按TriCore EABI；
- 是否产生CALL/CSA取决于是否为叶函数及优化。

正确学习方式：对同一C文件分别生成`.s`，再依据各自ABI解释，而不是比较指令名字多少。

---

## 11. CASE-02：局部变量`optimized out`

```c
uint32_t Calc(uint32_t x)
{
    uint32_t a = x * 2U;
    uint32_t b = a + 3U;
    return b;
}
```

`-O2`可能生成一条组合运算，不为`a/b`分配独立存储。Debugger显示`optimized out`不代表程序没有按语义计算，只表示DWARF无法在当前PC为变量提供稳定位置。

定位方法：

- 看反汇编；
- 看优化记录；
- 在需要观测的最小位置使用日志/Trace；
- 不为了“让调试器看见”而随意把变量改volatile进入量产代码。

---

## 12. CASE-03：内联改变调试和时序

```c
static inline uint32_t Clamp(uint32_t x)
{
    return (x > 100U) ? 100U : x;
}
```

内联后：

- 不产生独立CALL；
- 函数断点可能对应多个地址或无法稳定命中；
- 调用者寄存器压力可能增加；
- 代码尺寸可能增加或减少；
- WCET路径发生变化。

`always_inline`不能作为“性能一定更好”的保证。

---

## 13. CASE-04：死代码删除

```c
static void DiagnosticHook(void)
{
    GPIO->OUT ^= 1U;
}
```

如果函数从未被可达代码引用，编译器/链接器可删除。即便它准备由调试器手动调用，也需要明确保留策略：

- `used`影响编译器发出；
- 独立Section；
- 链接脚本`KEEP`防止`--gc-sections`删除；
- 调试安全评审。

`used`和`KEEP`处于不同阶段，不能互相替代。

---

## 14. CASE-05：普通内存访问被合并/消除

```c
uint32_t value;

value = 1U;
value = 2U;
```

若中间没有可观察使用，第一笔写可被删除。对MMIO必须使用正确的volatile类型：

```c
volatile uint32_t *reg = ...;
*reg = 1U;
*reg = 2U;
```

但即使两笔volatile写被发出，TC3xx Store Buffer是否合并、Slave是否要求间隔仍需硬件规范约束。例如Flash Load Page 32-bit命令序列需要DSYNC防止合并成64-bit事务。

---

## 15. CASE-06：浮点常量引入双精度

```c
float y = x * 0.1;  /* 0.1默认double */
```

可能引入双精度运算/转换和库调用。应根据算法要求写：

```c
float y = x * 0.1F;
```

但不能只为性能随意改精度，需评估误差、FPU能力、ASIL数值要求和编译选项。

---

## 16. CASE-07：对齐假设影响指令

```c
uint32_t Read(const uint32_t *p)
{
    return *p;
}
```

通过类型，编译器可以假设`p`满足`uint32_t`对齐。若调用者把奇地址强转传入，问题在调用者的C语义，不是编译器“错误选择了对齐Load”。

在M7关闭`UNALIGN_TRP`时可能碰巧成功；换成TC3xx某区域或启用Trap后失败。硬件容忍不修复语言层错误。

---

## 17. CASE-08：`naked`函数

```c
__attribute__((naked))
void HardFault_Handler(void)
{
    uint32_t status = SCB->CFSR; /* 危险 */
}
```

`naked`抑制标准函数序言/结尾，但普通C语句可能需要栈、局部变量或寄存器保存，行为不可依赖。

推荐结构：

```c
__attribute__((naked))
void HardFault_Handler(void)
{
    __asm volatile(
        "tst lr, #4\n"
        "ite eq\n"
        "mrseq r0, msp\n"
        "mrsne r0, psp\n"
        "b HardFault_C\n");
}

void HardFault_C(uint32_t *stacked)
{
    /* 普通C分析 */
}
```

精确汇编需与目标ABI、编译器和FPU栈帧策略配套。TC3xx Trap入口不应照搬该M7模板，应按CSA/Trap ABI编写。

---

## 18. 反汇编阅读方法

不要逐条翻译，而是围绕问题阅读：

1. 函数入口保存了哪些寄存器？
2. 参数从哪里来？
3. 内存访问宽度是什么？
4. 是否真正重复读取volatile对象？
5. 是否发生函数内联？
6. 是否有库调用？
7. 屏障指令是否存在？
8. 返回地址和栈是否匹配ABI？
9. 地址属于哪个Section/Memory Region？

Arm：

```bash
arm-none-eabi-objdump -d -S app.elf
```

TriCore使用工具链配套`objdump`或反汇编器，选项概念相同。

---

## 19. 编译诊断选项

建议基线示例：

```text
-Wall -Wextra -Werror
-Wshadow -Wconversion -Wsign-conversion
-Wundef -Wdouble-promotion
-Wformat=2 -Wcast-align
-ffunction-sections -fdata-sections
-fstack-usage
```

实际项目需评估编译器版本支持和遗留代码，不能盲目复制。关键是：

- Warning配置受版本控制；
- 新增Warning逐项消除或有审批豁免；
- 不在源文件局部随意关闭；
- 与MISRA/静态分析形成互补。

---

## 20. 验证实验

### EXP-01：编译四阶段

对一个源文件分别生成`.i/.s/.o/.elf`，记录每阶段新增的信息和仍未解析的信息。

### EXP-02：ABI参数

设计0～8个参数、64-bit参数、结构体参数和浮点参数函数，分别生成M7/TC3xx汇编，按各自ABI标注。

### EXP-03：优化矩阵

对同一函数使用`-O0/-Og/-O2/-Os/LTO`，比较：

- 指令数；
- 栈使用；
- 函数是否存在；
- Debug变量；
- 执行周期。

### EXP-04：volatile与Store Buffer

证明volatile保证编译器发出两笔写，再通过总线/Flash命令案例观察硬件是否合并或延迟。

### EXP-05：naked Handler

检查正确入口模板的反汇编，确认没有意外序言，并用构造Fault验证栈帧提取。

---

## 21. 系统工程要求

| ID | 需求示例 |
|---|---|
| SYS-COMP-001 | 所有对象库应使用一致的CPU、FPU、ABI、endian和语言选项。 |
| SYS-COMP-002 | 发布构建优化等级和LTO配置应纳入配置管理并执行回归。 |
| SYS-COMP-003 | 中断/Trap入口的函数属性和ABI应由平台模板统一提供。 |
| SYS-COMP-004 | 构建应输出反汇编、Map和stack-usage等分析产物。 |
| SYS-COMP-005 | 项目应禁止依靠`-O0`规避未定义行为或竞态。 |
| SYS-COMP-006 | TriCore参数寄存器和保存规则应以实际工具链EABI手册为正式依据。 |

---

## 22. 面试与评审问题

1. GCC四阶段分别输入输出什么？
2. Translation Unit对优化边界有什么影响？
3. M7为什么R0-R3通常由调用者负责保存？
4. TC3xx的CSA与M7普通函数压栈有什么根本区别？
5. `optimized out`说明代码没有执行吗？
6. `used`为什么不能替代`KEEP`？
7. volatile写已经出现在汇编中，为什么硬件仍可能改变事务形态？
8. `-O0`正常、`-O2`失败的第一检查项是什么？
9. hard-float与softfp为什么是ABI问题？
10. naked函数为什么只适合最小汇编入口？

---

## 23. 小结

```text
C语言给出抽象语义
→ GCC在合法假设下优化
→ ABI规定模块边界
→ 后端选择M7或TriCore指令
→ ELF记录尚待链接的Section/Symbol/Relocation
```

下一章进入ELF、Section、Symbol、Relocation、静态库和调试符号，建立从机器代码到最终映像的证据链。
