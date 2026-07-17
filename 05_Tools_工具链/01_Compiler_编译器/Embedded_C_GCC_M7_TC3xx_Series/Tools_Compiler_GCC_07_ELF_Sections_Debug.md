# ELF目标文件、Section与调试符号

---

## 系列导航

- **返回总纲**：[[Tools_Compiler_Embedded_C_GCC_00_Series_Overview|00 学习总纲与进度]]
- **上一篇**：[[Tools_Compiler_GCC_06_Compilation_ABI_Optimization|06_Compilation_ABI_Optimization]]
- **下一篇**：[[Tools_Compiler_GCC_08_Linker_Script_Startup|08_Linker_Script_Startup]]

---


> 本章目标：能够从C对象或函数出发，在`.o`、静态库、ELF、Map和反汇编之间追踪其Section、Symbol、地址、引用与调试信息。

---

## 1. `.o`不是“还没生成的机器码”

可重定位目标文件通常已经包含：

- 目标架构机器码；
- 数据；
- 输入Section；
- Symbol Table；
- Relocation记录；
- Debug信息；
- 编译器属性。

它缺少的是全局最终地址和部分跨文件引用解析。

---

## 2. ELF三种核心视角

### 2.1 ELF Header

描述：

- 文件类别；
- 目标架构；
- endian；
- 入口地址；
- Section/Program Header位置。

### 2.2 Section Header

主要面向链接器和调试工具：

- `.text/.data/.bss`；
- `.symtab/.strtab`；
- `.debug_*`；
- `.rela.*`或`.rel.*`；
- 自定义Section。

### 2.3 Program Header

主要面向装载/映像：描述哪些Section组合成可装载Segment、权限、文件大小与内存大小。

嵌入式烧录工具常根据ELF Load Segment生成Flash内容。

---

## 3. ELF、BIN和HEX的区别

| 格式 | 地址信息 | Symbol/Debug | 空洞表达 | 典型用途 |
|---|---:|---:|---:|---|
| ELF | 有 | 有 | 有 | 调试、链接结果、烧录 |
| BIN | 无裸地址元数据 | 无 | 以填充或文件偏移体现 | 连续映像/升级包 |
| Intel HEX/SREC | 有 | 无 | 可离散表达 | 烧录和传输 |

### CASE-01：ELF很大但BIN很小

ELF可能包含大量DWARF、Symbol和Section名称；它们不烧录到目标Flash。判断烧录大小应看：

- Load Segment；
- `.text/.rodata/.data`的LMA；
- `size`输出；
- objcopy后的实际映像；
- 升级包格式和填充策略。

---

## 4. 常见Section

```text
.text          代码
.rodata        只读数据
.data          有初值可写数据
.bss           零初值数据，NOBITS
.isr_vector    M7异常向量表
.inttab/.traptab等  TC3xx项目中断/Trap相关表，名称由工程决定
.debug_info    DWARF类型和变量信息
.debug_line    地址与源代码行映射
.symtab        完整符号表
.strtab        符号字符串
```

配合`-ffunction-sections -fdata-sections`时，每个函数/对象可能进入独立Section：

```text
.text.FunctionA
.text.FunctionB
.data.g_state
```

这使链接器可按粒度进行垃圾回收。

---

## 5. Symbol

Symbol包含：

- 名称；
- 值/地址或Section内偏移；
- 大小；
- 类型（函数/对象等）；
- 绑定属性（local/global/weak）；
- 所属Section或未定义状态。

查看：

```bash
arm-none-eabi-nm -n app.elf
arm-none-eabi-readelf -s app.elf
```

### Local

文件作用域`static`通常产生Local Symbol，不参与跨文件解析。

### Global

外部链接定义，可解析其他对象的未定义引用。

### Weak

弱定义可被同名强定义替换，常用于默认ISR：

```c
void Default_Handler(void);
void UART_IRQHandler(void)
    __attribute__((weak, alias("Default_Handler")));
```

---

## 6. CASE-02：Weak ISR没有被覆盖

可能原因：

1. 用户函数拼写不同；
2. C++源缺少`extern "C"`导致名称修饰；
3. 函数定义为`static`；
4. 中断表引用的是另一个Symbol；
5. 用户对象文件未参与链接；
6. 静态库没有因未定义引用被提取；
7. Linker Script收集了错误Section。

证据链：

```bash
arm-none-eabi-nm app.elf | grep UART
arm-none-eabi-objdump -s -j .isr_vector app.elf
arm-none-eabi-objdump -d app.elf
```

确认向量表中的地址到底指向哪个函数。

TC3xx同理检查BIV/中断表或Trap Table相关Symbol和最终地址，但表结构与M7 Vector Table不同。

---

## 7. Undefined Symbol与Relocation

源文件：

```c
extern void Driver_Init(void);

void App_Init(void)
{
    Driver_Init();
}
```

`App_Init.o`在编译时不知道`Driver_Init`最终地址，会生成：

- 未定义Symbol；
- 调用位置的Relocation。

链接器找到定义后：

- 选择最终地址；
- 修补调用指令或生成veneer/stub；
- 检查跳转范围和架构属性。

### CASE-03：链接成功但调用了错误版本

多个库提供同名弱/强Symbol或静态库顺序改变，可能选择非预期实现。使用：

- Map的Cross Reference；
- `--trace-symbol`；
- `nm -A library.a`；
- 链接器诊断。

---

## 8. 静态库Archive

静态库是多个`.o`的归档：

```bash
arm-none-eabi-ar rcs libdriver.a uart.o spi.o
```

传统链接器通常按扫描时的未解析Symbol从库中提取成员，顺序可能重要：

```bash
gcc app.o -ldriver -lplatform
```

循环依赖可使用link group，但更好的方法是改善模块依赖：

```text
-Wl,--start-group -la -lb -Wl,--end-group
```

### CASE-04：库中函数明明存在仍undefined reference

检查：

1. `nm -A lib.a`是否真有强定义；
2. 名称是否被C++修饰；
3. 库顺序；
4. CPU/ABI是否兼容；
5. 条件编译是否生成另一个Symbol；
6. Linker Script是否丢弃相关Section。

---

## 9. Section Garbage Collection

常见配置：

```text
-ffunction-sections -fdata-sections
-Wl,--gc-sections
```

链接器从根集合出发保留可达Section。入口、显式引用和`KEEP`可形成根。

### CASE-05：注册表被删除

```c
__attribute__((section(".test_cases"), used))
const TestCase_t test0 = { ... };
```

`used`促使编译器发出对象，但链接器仍可能回收该Section。链接脚本需要：

```ld
.test_cases :
{
    __test_cases_start = .;
    KEEP(*(.test_cases*))
    __test_cases_end = .;
} > FLASH
```

### M7高风险对象

- Vector Table；
- 构造函数表；
- RAM复制表；
- 调试/命令注册表。

### TC3xx高风险对象

- BMHD/启动头；
- 中断/Trap Table；
- Core启动入口；
- CSA/复制表；
- 安全配置结构。

---

## 10. Orphan Section

源文件产生了链接脚本未显式收集的Section，链接器可能按默认规则放置。风险：

- 放入意外Memory Region；
- 权限不符；
- 未被启动代码复制；
- 与安全区混合；
- 不同链接器版本布局变化。

项目应开启或审查orphan Section警告，并在Map中建立允许列表。

---

## 11. Map文件阅读

Map至少回答：

1. Memory Region起止和占用；
2. 每个输出Section地址、大小、加载地址；
3. 输入Section来自哪个`.o/.a`；
4. Symbol最终地址；
5. 被丢弃Section；
6. Cross Reference；
7. 填充和对齐浪费。

### CASE-06：Section重叠

错误示例：

```text
.psram_text [0x0221A334, 0x0221C333]
.unpriv_data[0x0221BB34, 0x0221FB33]
```

交集从`0x0221BB34`开始，说明两个输出Section的VMA规划重叠。定位：

1. 链接脚本中两者起始表达式；
2. 是否使用硬编码地址而非顺序`.`；
3. 前一Section实际大小是否增长；
4. ALIGN是否扩大；
5. NOLOAD/AT是否混淆VMA与LMA；
6. 多核固定窗口是否预算不足。

改进：

```ld
ASSERT(__psram_text_end <= __unpriv_data_start,
       "psram_text overlaps unpriv_data")
```

---

## 12. DWARF调试信息

`-g`生成：

- 地址到源代码行；
- 类型；
- 变量位置表达式；
- 调用帧信息；
- 宏信息（取决于选项）。

它不改变C程序语义，通常可以与`-O2`同时使用。但优化后：

- 变量可能无稳定位置；
- 指令对应多行；
- 行执行顺序看似跳跃；
- 函数内联；
- Tail Call改变回溯。

### CASE-07：断点跳行

不要用源代码单步顺序直接判断CPU执行顺序，应结合：

- disassembly mixed view；
- 当前PC；
- 优化等级；
- DWARF line table。

---

## 13. `addr2line`与故障地址

M7 HardFault得到stacked PC：

```bash
arm-none-eabi-addr2line -e app.elf -f -C 0x08012344
```

还应查看前后反汇编：

```bash
arm-none-eabi-objdump -d -S \
    --start-address=0x08012320 \
    --stop-address=0x08012370 app.elf
```

TC3xx对Trap保存地址使用TriCore工具链对应`addr2line/objdump`。注意：

- 同步Trap地址通常更接近故障指令；
- 异步Store错误返回地址可能晚于原Store；
- 地址别名/Overlay可能需要映射回链接地址；
- 使用的ELF必须与烧录版本完全一致。

---

## 14. Build ID与版本匹配

错误ELF会让所有符号定位失真。发布物应绑定：

- Git commit；
- 构建配置；
- 编译器版本；
- Linker Script版本；
- ELF hash/Build ID；
- BIN/HEX hash；
- Map；
- 配置生成文件版本。

故障日志至少记录软件版本和映像标识。

---

## 15. CASE-08：Debug Symbol被strip

发布可保留两个产物：

- 完整带符号ELF，受控归档；
- 面向发布/工具的strip映像。

不要只保存BIN，否则现场地址难以回溯。也不要把包含敏感符号的完整ELF无控制地随产品分发。

---

## 16. 常用工具命令

```bash
# Header
arm-none-eabi-readelf -h app.elf

# Section
arm-none-eabi-readelf -S app.elf

# Program Header
arm-none-eabi-readelf -l app.elf

# Symbol
arm-none-eabi-readelf -s app.elf
arm-none-eabi-nm -n -S app.elf

# 反汇编＋源码
arm-none-eabi-objdump -d -S app.elf

# Section内容
arm-none-eabi-objdump -s -j .isr_vector app.elf

# 大小
arm-none-eabi-size -A app.elf

# 地址反查
arm-none-eabi-addr2line -e app.elf -f -C ADDRESS
```

TriCore工具链使用同发行版中的对应工具，避免混用不同版本binutils。

---

## 17. 从对象到地址的完整追踪

假设：

```c
__attribute__((section(".shared_data")))
uint32_t g_mailbox;
```

证据步骤：

1. 预处理确认属性存在；
2. `readelf -S module.o`确认输入Section；
3. `readelf -s module.o`确认Symbol；
4. Linker Script确认输出Section与Memory Region；
5. Map确认来源、VMA、LMA和大小；
6. `nm app.elf`确认最终地址；
7. 启动代码确认是否复制/清零；
8. MPU/Cache配置确认访问属性；
9. Debugger读取地址验证。

---

## 18. M7与TC3xx专用检查点

### Cortex-M7

- `.isr_vector`是否KEEP；
- 初始MSP和Reset Handler地址；
- VTOR对齐；
- Thumb函数地址；
- ITCM/DTCM/RAM代码的VMA/LMA；
- FPU ABI属性；
- unwind/stack frame信息。

### TC3xx

- BMHD/启动入口；
- 每核入口和栈；
- CSA区域；
- BIV/BTV及表对齐；
- PSPR/DSPR/DLMU/LMU映射；
- cached/non-cached地址别名；
- Overlay/Copy Table；
- TriCore EABI属性。

---

## 19. 验证实验

### EXP-01：ELF解剖

对最小工程记录ELF Header、Section、Program Header、Symbol和Relocation；说明每项由哪个阶段生成。

### EXP-02：Weak覆盖

分别制造正确覆盖、拼写错误、C++修饰、static定义，使用`nm`和向量/表内容定位。

### EXP-03：GC

创建未引用函数、`used`对象和`KEEP`注册表，比较链接Map中的Discarded Section。

### EXP-04：静态库顺序

制造A/B库互相引用，观察顺序与group效果，并重构依赖。

### EXP-05：故障地址回溯

M7构造精确BusFault；TC3xx构造同步数据Trap。保存地址后离线使用匹配ELF定位。

---

## 20. 系统工程要求

| ID | 需求示例 |
|---|---|
| SYS-ELF-001 | 每次发布应归档与烧录映像严格匹配的ELF、Map和构建元数据。 |
| SYS-ELF-002 | Vector/Trap/BMHD/Copy Table等根Section应由Linker Script显式KEEP。 |
| SYS-ELF-003 | Orphan Section应产生诊断并纳入允许列表。 |
| SYS-ELF-004 | 关键Memory Region应使用ASSERT执行容量和重叠检查。 |
| SYS-ELF-005 | 故障日志应包含映像版本、PC/Trap地址和关键Fault寄存器。 |
| SYS-ELF-006 | 工具链binutils版本应与编译器发行版匹配。 |

---

## 21. 面试与评审问题

1. `.o`中是否已经有机器码？
2. Section Header与Program Header分别服务什么？
3. ELF和BIN大小为何差异巨大？
4. Weak Symbol覆盖为什么可能失败？
5. Relocation解决什么问题？
6. 静态库为什么与对象文件的链接行为不同？
7. `used`与`KEEP`分别作用于哪个阶段？
8. 如何从Map定位Section重叠？
9. 为什么发布必须保存完整ELF？
10. TC3xx Overlay启用后，Trap地址怎样映射回链接符号？

---

## 22. 小结

```text
.o记录局部机器码、Section、Symbol和Relocation
→ 静态库按引用提取成员
→ 链接器选择地址并执行GC
→ ELF保存最终地址、Load Segment和调试信息
→ Map/objdump/nm/addr2line建立现场故障证据链
```

下一章将深入Linker Script和启动代码，解释VMA/LMA、复制表、`.data/.bss`、RAM函数、M7 Vector Table与TC3xx BMHD/CSA/BIV/BTV。
