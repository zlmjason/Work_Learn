# 链接脚本、启动文件与MCU内存初始化

---

## 系列导航

- **返回总纲**：[[Tools_Compiler_Embedded_C_GCC_00_Series_Overview|00 学习总纲与进度]]
- **上一篇**：[[Tools_Compiler_GCC_07_ELF_Sections_Debug|07_ELF_Sections_Debug]]
- **下一篇**：[[Tools_Compiler_GCC_09_Make_CMake_Build|09_Make_CMake_Build]]

---


> 本章目标：从Memory Map出发定义VMA/LMA、Section、栈、复制表和入口，并理解M7与TC3xx从复位到`main()`的不同路径。

---

## 1. 链接脚本解决什么问题

编译器只知道：

```text
某函数在.text.Function中
某变量在.data.g_value中
```

链接器决定：

- 最终地址；
- 放入哪个Memory Region；
- 对齐；
- 加载地址；
- 是否保留；
- 是否导出边界Symbol；
- 是否越界；
- 程序入口。

---

## 2. VMA与LMA

### VMA：运行地址

CPU运行时访问的地址。

### LMA：加载地址

初值在程序映像/Flash中的存放地址。

`.data`典型关系：

```text
LMA：Flash中的初始字节
            ↓ 启动复制
VMA：RAM中的运行对象
```

`.text`直接从Flash执行时通常VMA=LMA；RAM代码则不同。

---

## 3. Cortex-M7 GNU ld基本示例

```ld
ENTRY(Reset_Handler)

MEMORY
{
    FLASH (rx)  : ORIGIN = 0x08000000, LENGTH = 2M
    RAM   (rwx) : ORIGIN = 0x20000000, LENGTH = 512K
}

SECTIONS
{
    .isr_vector :
    {
        . = ALIGN(256);
        KEEP(*(.isr_vector))
    } > FLASH

    .text :
    {
        *(.text*)
        *(.rodata*)
        KEEP(*(.init))
        KEEP(*(.fini))
    } > FLASH

    .data :
    {
        . = ALIGN(4);
        __data_start__ = .;
        *(.data*)
        __data_end__ = .;
    } > RAM AT > FLASH

    __data_load__ = LOADADDR(.data);

    .bss (NOLOAD) :
    {
        . = ALIGN(4);
        __bss_start__ = .;
        *(.bss*)
        *(COMMON)
        __bss_end__ = .;
    } > RAM

    .noinit (NOLOAD) :
    {
        __noinit_start__ = .;
        *(.noinit*)
        __noinit_end__ = .;
    } > RAM

    __StackTop = ORIGIN(RAM) + LENGTH(RAM);
}

ASSERT(__bss_end__ <= __StackTop, "RAM overflow")
```

该示例用于解释概念，实际M7 SoC可能有ITCM、DTCM、AXI SRAM、多个Flash Bank、共享RAM和Boot Header。

---

## 4. 常用链接脚本语法

### `MEMORY`

定义可用区域，不会自动把Section放进去。

### `SECTIONS`

把输入Section组合为输出Section。

### `.`位置计数器

表示当前输出地址。硬编码回退可能造成重叠，应谨慎。

### `ALIGN`

```ld
. = ALIGN(32);
```

对齐当前位置，可能引入Padding。

### `KEEP`

防止`--gc-sections`回收。

### `NOLOAD`

该输出Section通常不需要在加载映像中包含初始化数据；不等于硬件自动保留内容。

### `AT`/`AT>`

指定LMA。

### `LOADADDR/SIZEOF/ADDR`

生成启动复制和检查使用的表达式。

### `PROVIDE`

在未由其他对象定义时提供Symbol。

### `ASSERT`

将内存边界从人工检查变成构建失败：

```ld
ASSERT(SIZEOF(.stack) >= 0x1000, "stack too small")
```

---

## 5. M7从复位到main

典型路径：

```text
复位
→ 从Vector Table[0]装载初始MSP
→ 从Vector Table[1]取得Reset_Handler地址
→ 执行Reset_Handler
→ SystemInit：时钟/FPU/存储系统等早期配置
→ 复制.data和RAM代码
→ 清零.bss
→ 初始化C/C++运行时
→ main
```

具体顺序由厂商启动文件决定。例如Flash wait-state必须在升频前配置；Cache启用时机又会影响RAM代码复制和一致性。

### 5.1 Vector Table

```c
__attribute__((section(".isr_vector")))
const uintptr_t vectors[] =
{
    (uintptr_t)&__StackTop,
    (uintptr_t)Reset_Handler,
    (uintptr_t)NMI_Handler,
    (uintptr_t)HardFault_Handler,
};
```

真实实现使用厂商/CMSIS模板。要求：

- 表对齐满足VTOR；
- 初始SP位于有效RAM并满足对齐；
- Handler地址有效且Thumb状态正确；
- Section被KEEP；
- 重定位到RAM后执行DSB/ISB等规定同步。

### 5.2 `.data`复制

```c
extern uint32_t __data_load__;
extern uint32_t __data_start__;
extern uint32_t __data_end__;

static void CopyData(void)
{
    const uint32_t *src = &__data_load__;
    uint32_t *dst = &__data_start__;

    while (dst < &__data_end__)
    {
        *dst++ = *src++;
    }
}
```

复制单位必须覆盖尾部；若Section不保证4字节长度，需要byte尾处理或链接断言。

### 5.3 `.bss`清零

```c
static void ClearBss(void)
{
    uint32_t *dst = &__bss_start__;
    while (dst < &__bss_end__)
    {
        *dst++ = 0U;
    }
}
```

---

## 6. TC3xx从复位到main

TC3xx与M7的复位模型不同。概念路径：

```text
复位释放
→ Boot Firmware读取/评估BMHD与启动模式
→ Startup Software/用户入口
→ 主CPU早期初始化
→ 建立A10软件栈
→ 初始化CSA链表（FCX/LCX等）
→ 配置小数据区基址（按EABI/工具链）
→ 配置BTV/BIV和中断系统
→ 初始化时钟、Flash wait-state和受保护寄存器
→ 按Copy/Clear Table初始化.data/.bss及RAM代码
→ 必要的Cache/MPU/保护配置
→ 启动其他CPU核
→ 各核进入其main/入口
```

精确顺序由Infineon Startup、iLLD、MCAL或项目自定义启动文件决定。

### 6.1 BMHD

Boot Mode Header用于Boot Firmware选择和验证用户启动入口及相关配置。系统要求：

- 固定地址和格式正确；
- 链接脚本显式保留；
- CRC/确认码符合器件规范；
- 多份Header策略与启动模式一致；
- OTA/SWAP方案评审其地址映射。

### 6.2 CSA

CSA不是普通软件栈。启动软件需要：

- 为每核划分对齐的CSA区域；
- 把每个CSA块链接成Free Context List；
- 设置FCX/LCX；
- 预留最坏函数调用、中断/Trap嵌套和诊断需求；
- 防止与栈/数据Section重叠。

CSA耗尽会触发相应上下文管理Trap，不能仅通过增大A10栈解决。

### 6.3 A10软件栈

用于自动对象、溢出参数和编译器需要的栈空间。每个核应有独立区域和边界Symbol。

### 6.4 BIV/BTV

- BIV：中断向量基址；
- BTV：Trap向量基址。

要求：

- 对齐和Spacing配置正确；
- Table Section被KEEP；
- 写受保护寄存器遵守ENDINIT/同步要求；
- 配置后执行架构要求的同步；
- 多核分别配置。

---

## 7. TC3xx GNU链接布局概念

实际HighTec/Infineon GNU linker script/LSL语法和预定义宏应以工具链为准。概念上需要表达：

```text
PFlash：BMHD、启动代码、.text、.rodata、初始化镜像
CPUx PSPR：快速代码
CPUx DSPR：栈、CSA、核私有数据
DLMU/LMU：共享数据
各核：独立stack/CSA/入口/小数据区
```

不要直接把Arm GNU ld脚本复制给TriCore；二者的：

- 地址别名；
- 小数据寻址；
- CSA；
- 多核Section；
- Boot Header；
- 工具链语法和默认库

都不同。

---

## 8. RAM函数

### 8.1 为什么只加section属性不够

```c
__attribute__((section(".ram_code")))
void Flash_Program(void)
{
}
```

还需要：

1. 链接脚本为`.ram_code`分配RAM VMA；
2. Flash中分配LMA保存机器码；
3. 导出load/start/end Symbol；
4. 启动或调用前复制；
5. 执行D/I Cache维护；
6. MPU允许执行；
7. 验证所有被调用函数和常量是否仍位于忙Flash Bank。

### 8.2 M7示例

```ld
.ram_code :
{
    . = ALIGN(4);
    __ram_code_start__ = .;
    *(.ram_code*)
    __ram_code_end__ = .;
} > RAM AT > FLASH

__ram_code_load__ = LOADADDR(.ram_code);
```

复制后：

```text
Clean DCache（若复制经过Cache且目标可缓存）
→ Invalidate ICache/对应指令缓存路径
→ DSB
→ ISB
```

精确API按CMSIS和SoC手册。

### 8.3 TC3xx示例

把Flash Driver放入PSPR：

- 代码VMA在CPUx PSPR；
- LMA在不被操作的PFlash或镜像区；
- 启动Copy Table复制；
- 配置代码访问/Cache一致性；
- 依赖数据、常量、被调函数也必须可访问；
- 多核执行者要使用对应本地/全局地址映射；
- 编程代码不能继续从正在program/erase的同一PFlash Bank取指。

---

## 9. CASE-01：RAM函数HardFault/Trap

定位：

1. `nm`确认函数Symbol VMA是否在RAM；
2. Map确认LMA和大小；
3. main前读取RAM内容是否与Flash LMA一致；
4. 检查复制发生在调用前；
5. M7检查Thumb函数地址、XN、I-Cache；
6. TC3xx检查PSPR地址别名、Code MPU、PCache/PLB；
7. 检查函数内部调用是否跳回忙Flash；
8. 检查literal/rodata位置。

---

## 10. 多个RAM区域

M7 SoC常见：

- ITCM：低延迟指令；
- DTCM：低延迟数据，DMA可达性需确认；
- AXI SRAM：Cacheable且DMA常可达；
- 多Bank SRAM；
- Retention SRAM。

TC3xx常见：

- PSPR：核本地程序Scratchpad；
- DSPR：核本地数据Scratchpad；
- DLMU：分布式本地/全局访问；
- LMU：共享RAM；
- DAM/备用区域依器件。

布局决策维度：

| 维度 | 问题 |
|---|---|
| 延迟 | 本地核访问几周期？ |
| 带宽 | 是否与DMA/其他核争用？ |
| 可达性 | DMA/HSM/其他核能否访问？ |
| Cache | 地址属性是什么？ |
| 安全 | ECC、MPU、诊断覆盖如何？ |
| 复位 | 哪类复位保持/初始化？ |
| 容量 | 最坏增长和对齐浪费？ |

---

## 11. 多核Section

TC3xx需要明确每核：

```text
.cpu0_stack / .cpu1_stack / ...
.cpu0_csa   / .cpu1_csa
.cpu0_private_data
.cpu0_pspr_code
```

共享区：

```text
.shared_nocache
.shared_cacheable（需一致性协议）
.ipc_mailbox
```

系统需求：

- 私有区不被其他核误用；
- 共享区使用统一系统地址；
- Cache和原子属性明确；
- 链接断言检查重叠；
- 初始化责任只属于一个核或有严格握手。

### CASE-02：两个核重复清零共享`.bss`

CPU0已经写入启动握手，CPU1稍后执行自己的通用`.bss`清零并覆盖共享区，造成偶发启动失败。

正确设计：

- 每核私有clear table；
- 共享区只由主核初始化；
- 其他核等待初始化完成标志；
- 发布标志前执行正确屏障。

---

## 12. Copy Table与Clear Table

多个非连续区域不适合硬编码一组`_sidata/_sdata`。可生成表：

```text
CopyEntry { source LMA, destination VMA, length }
ClearEntry{ destination VMA, length }
```

启动软件循环处理：

```c
typedef struct
{
    const uint8_t *src;
    uint8_t *dst;
    size_t length;
} CopyEntry_t;
```

表本身必须：

- 位于启动时可读区域；
- 被KEEP；
- 端点明确；
- 防止恶意/错误条目越界；
- 与安全启动完整性保护关联。

---

## 13. CASE-03：`.noinit`被误清除

原因：

- `.noinit`被通配符`*(.bss*)`提前捕获；
- clear table范围过大；
- BootROM/MBIST初始化RAM；
- Debug下载器执行RAM reset；
- 链接脚本未使用NOLOAD。

验证：

1. Map确认输入Section最终归属；
2. 检查输出Section顺序；
3. 在C清零前读取；
4. 对复位源建立矩阵；
5. 检查硬件RAM初始化状态。

---

## 14. CASE-04：Linker Script通配符顺序

```ld
.data : { *(.data*) } > RAM
.data.fast : { *(.data.fast*) } > FAST_RAM
```

第一条已经捕获`.data.fast*`，第二条为空。应先放特例：

```ld
.data.fast : { *(.data.fast*) } > FAST_RAM
.data : { *(.data*) } > RAM
```

Map文件是最终证据。

---

## 15. CASE-05：Vector Table被GC

仅有：

```c
__attribute__((section(".isr_vector")))
const uintptr_t vectors[] = {...};
```

如果入口引用链未让链接器认为其可达，`--gc-sections`可能删除。必须：

```ld
KEEP(*(.isr_vector))
```

TC3xx的BMHD、Trap/Interrupt Table和Core启动入口同样属于必须显式保留的根Section。

---

## 16. CASE-06：Stack与Heap碰撞

简单脚本把Stack Top设为RAM末尾，却没有为Heap、DMA区和共享区建立边界。运行期动态增长后相互覆盖。

改进：

- 明确固定栈区；
- 链接`ASSERT`检查静态区；
- RTOS每任务独立栈；
- MPU Guard Region；
- 栈水位和`-fstack-usage`；
- 限制/禁止Heap；
- TC3xx同时预算CSA区域。

---

## 17. CASE-07：地址重叠

检测每个Section半开区间：

```text
[start, end)
```

重叠条件：

```text
A.start < B.end && B.start < A.end
```

链接脚本使用：

```ld
ASSERT(__region_a_end <= __region_b_start,
       "region A overlaps region B")
```

不要仅靠表格中的计划大小；Section会因代码增长、对齐、库更新而变化。

---

## 18. CASE-08：升频前Flash Wait-State不足

错误启动顺序：

```text
先提高CPU/SRI/FSI时钟
→ 仍使用复位默认Flash wait-state
→ PFlash读不满足访问时间
→ 随机取指错误/Trap
```

正确顺序通常是：

```text
保持安全低频
→ 配置满足目标频率的Flash wait-state
→ 配置PLL/分频
→ 等待稳定
→ 切换时钟
```

TC3xx明确要求时钟变化前保证PFlash/DFlash wait-cycle足够；M7具体SoC同样需遵守其Flash控制器顺序。

---

## 19. CASE-09：启动期间Cache问题

风险：

- 在复制RAM代码前启用DCache，数据只留Dirty Line；
- 调用RAM代码前未invalidate ICache；
- 清零共享区时其他核已缓存旧值；
- MPU属性修改后未执行同步；
- 使用Cache维护API时地址/长度未按Line处理。

应定义单一、审查过的早期启动顺序，而不是各模块自行开Cache。

---

## 20. CASE-10：TC3xx CSA不足

现象：

- 深调用/中断压力下触发FCU/FCD等上下文管理Trap；
- 普通栈看似仍有空间；
- 降低优化或改变调用路径后现象改变。

定位：

- 检查Trap Class/TIN；
- FCX/LCX/PCXI；
- CSA Link Word；
- 每核CSA数量；
- 最坏嵌套、函数调用和诊断需求。

修复不是简单增大M7式栈，而是重新预算/布局CSA并检查上下文泄漏。

---

## 21. 启动文件安全要求

启动代码处于系统最脆弱阶段：

- 栈/CSA可能尚未就绪；
- `.data/.bss`尚未初始化；
- FPU/Cache/MPU尚未配置；
- Watchdog/ENDINIT有效；
- 时钟处于复位配置；
- 多核状态不一致。

因此早期函数：

- 避免依赖未初始化全局变量；
- 避免复杂库函数；
- 明确是否可使用栈/FPU；
- 严格控制编译属性；
- 任何失败进入可诊断安全路径；
- 保留复位原因和关键错误信息。

---

## 22. 验证实验

### EXP-01：VMA/LMA

定义`.data`和`.ram_code`，用`readelf -l/-S`、Map和Debugger分别确认LMA/VMA及启动复制。

### EXP-02：M7 Vector Table

验证初始MSP、Reset Handler、VTOR重定位、对齐和Thumb地址；故意破坏单项观察Fault。

### EXP-03：TC3xx CSA

为测试核减少CSA数量，构造深调用和中断嵌套，验证上下文Trap及诊断信息。

### EXP-04：多核初始化

共享区只由CPU0初始化，CPU1等待标志；加入/移除屏障和错误clear table，观察启动竞态。

### EXP-05：RAM函数

M7从ITCM/SRAM执行，TC3xx从PSPR执行；验证复制、Cache、MPU、依赖函数和Flash Busy场景。

### EXP-06：复位矩阵

对`.data/.bss/.noinit/stack/CSA/Cache`记录不同复位源后的状态。

---

## 23. 系统需求基线

| ID | 需求示例 |
|---|---|
| SYS-LNK-001 | 所有Memory Region应定义起止、用途、访问Master、Cache和复位属性。 |
| SYS-LNK-002 | Linker Script应对关键区域执行容量和重叠ASSERT。 |
| SYS-LNK-003 | 启动根Section应使用KEEP且由构建检查地址。 |
| SYS-START-001 | 升频前应配置满足目标频率的Flash wait-state。 |
| SYS-START-002 | 每核Stack、CSA、Vector/Trap和私有数据应独立布局。 |
| SYS-START-003 | 共享区应只由指定主核初始化，并通过同步发布完成。 |
| SYS-RAMCODE-001 | RAM代码应定义VMA/LMA、复制、Cache/MPU及依赖闭包。 |
| SYS-RESET-001 | 每类复位源应定义`.data/.bss/.noinit`和RAM实例处理。 |
| SYS-SAFE-001 | 启动初始化失败应进入可诊断安全反应，不得继续运行未知映像。 |

---

## 24. 面试与评审问题

1. VMA和LMA是什么？
2. 为什么`.data`需要复制而`.bss`只需清零？
3. `NOLOAD`是否保证warm reset保留？
4. 为什么RAM函数只加section属性不够？
5. M7 Vector Table前两个word是什么？
6. TC3xx BMHD、CSA、BIV和BTV分别解决什么？
7. TC3xx的CSA和A10栈为何必须分别预算？
8. 多核为什么不能都执行同一份共享`.bss`清零？
9. 如何从Map证明Section重叠？
10. 为什么Flash wait-state必须在升频前配置？

---

## 25. 小结

```text
链接脚本定义映像的空间真相
→ 启动代码把加载映像变成运行状态
→ M7依赖Vector/MSP/Reset Handler
→ TC3xx依赖BMHD/SSW/Stack/CSA/BIV/BTV
→ Cache、MPU、多核和复位策略决定初始化是否真正可靠
```

下一章进入Make/CMake/GCC属性和工程构建，确保这些编译、链接与启动规则能在大型项目中稳定、可重复地生效。
