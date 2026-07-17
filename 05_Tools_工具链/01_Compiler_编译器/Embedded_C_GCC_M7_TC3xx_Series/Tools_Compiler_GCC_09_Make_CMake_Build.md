# Make、CMake、GCC属性与工程构建

---

## 系列导航

- **返回总纲**：[[Tools_Compiler_Embedded_C_GCC_00_Series_Overview|00 学习总纲与进度]]
- **上一篇**：[[Tools_Compiler_GCC_08_Linker_Script_Startup|08_Linker_Script_Startup]]
- **下一篇**：[[Tools_Compiler_Embedded_C_GCC_10_Case_Collection|10_Case_Collection]]

---


> 本章目标：区分CMake、Ninja/Make、GCC、Assembler和Linker的职责，构建可重复、可诊断、双平台可维护的嵌入式工程。

---

## 1. 构建链路

```text
CMake
  ↓ 生成构建规则
Ninja / Make
  ↓ 根据依赖决定执行哪些命令
GCC Driver
  ↓ 调用预处理器、编译器、汇编器、链接器
GNU ld / 工具链Linker
  ↓ 生成ELF和Map
objcopy/size/脚本
  ↓ BIN/HEX、大小报告、签名/打包
```

常见误区：

- CMake不直接编译C代码；
- Ninja不是编译器；
- `gcc`链接命令通常仍会调用`ld`并自动加入运行库；
- Linker Script不是启动代码；
- IDE只是组织并调用上述工具。

---

## 2. Make基本模型

```make
target: prerequisites
	recipe
```

示例：

```make
CC      := arm-none-eabi-gcc
OBJCOPY := arm-none-eabi-objcopy

CFLAGS  := -mcpu=cortex-m7 -mthumb -O2 -g3 \
           -ffunction-sections -fdata-sections
LDFLAGS := -T link.ld -Wl,--gc-sections -Wl,-Map=app.map

app.elf: main.o startup.o
	$(CC) $^ $(CFLAGS) $(LDFLAGS) -o $@

app.bin: app.elf
	$(OBJCOPY) -O binary $< $@
```

自动变量：

| 变量 | 含义 |
|---|---|
| `$@` | 当前Target |
| `$<` | 第一个Prerequisite |
| `$^` | 所有去重Prerequisite |
| `$?` | 比Target新的Prerequisite |

---

## 3. 头文件依赖

仅写：

```make
main.o: main.c
```

修改`config.h`时不会自动重编译。GCC可生成依赖：

```text
-MMD -MP
```

```make
CFLAGS += -MMD -MP
-include $(OBJECTS:.o=.d)
```

### CASE-01：修改头文件但固件行为不变

证据：

1. 查看Ninja/Make是否执行对应编译命令；
2. 检查`.d`依赖文件；
3. 检查是否包含了另一个同名头文件；
4. 查看预处理结果；
5. 禁止用“Clean All以后好了”作为根因闭环。

---

## 4. CMake Target思维

```cmake
add_executable(app.elf)

target_sources(app.elf PRIVATE
    src/main.c
    startup/startup_m7.S
)

target_include_directories(app.elf PRIVATE
    include
    cmsis
)

target_compile_definitions(app.elf PRIVATE
    CPU_CORTEX_M7=1
)

target_compile_options(app.elf PRIVATE
    -mcpu=cortex-m7
    -mthumb
    -O2
    -g3
)

target_link_options(app.elf PRIVATE
    -T${CMAKE_SOURCE_DIR}/link.ld
    -Wl,--gc-sections
    -Wl,-Map=${CMAKE_BINARY_DIR}/app.map
)
```

优先使用`target_*`接口，不要把所有选项塞入全局`CMAKE_C_FLAGS`，否则：

- Host工具也收到交叉编译参数；
- 不同Core/库无法隔离；
- PUBLIC/PRIVATE传播关系不清；
- Debug/Release难管理。

---

## 5. PUBLIC、PRIVATE、INTERFACE

假设`driver`依赖CMSIS头文件：

```cmake
target_include_directories(driver
    PUBLIC  ${PROJECT_SOURCE_DIR}/driver/include
    PRIVATE ${PROJECT_SOURCE_DIR}/driver/src
)
```

- PRIVATE：只编译当前Target需要；
- PUBLIC：当前Target和消费者都需要；
- INTERFACE：只消费者需要。

### CASE-02：宏没有传给目标

```cmake
set(MY_FLAGS -DENABLE_CACHE)
```

只创建CMake变量，不会自动传给编译器。必须：

```cmake
target_compile_definitions(app.elf PRIVATE ENABLE_CACHE=1)
```

最终证据是`compile_commands.json`或详细构建命令。

---

## 6. Toolchain File

M7示意：

```cmake
set(CMAKE_SYSTEM_NAME Generic)
set(CMAKE_SYSTEM_PROCESSOR arm)

set(CMAKE_C_COMPILER arm-none-eabi-gcc)
set(CMAKE_ASM_COMPILER arm-none-eabi-gcc)
set(CMAKE_OBJCOPY arm-none-eabi-objcopy)

set(CMAKE_TRY_COMPILE_TARGET_TYPE STATIC_LIBRARY)
```

TC3xx建立独立Toolchain File，配置TriCore编译器、assembler、linker和binutils。不要在同一Build Directory中切换架构；不同工具链使用独立构建目录：

```text
build/m7-debug
build/m7-release
build/tc3xx-debug
build/tc3xx-release
```

---

## 7. 编译选项分类

### CPU/ISA

M7：

```text
-mcpu=cortex-m7 -mthumb
```

以及项目实际FPU/ABI参数。

TC3xx：

- 目标Core/Derivative；
- EABI；
- FPU；
- small data、代码模型；
- 具体语法以工具链为准。

### 语言

```text
-std=c11
-ffreestanding
-fno-common
```

### 优化

```text
-O0/-Og/-O2/-Os
-flto
```

### 可诊断性

```text
-g3
-fstack-usage
-save-temps=obj
```

### Section

```text
-ffunction-sections -fdata-sections
```

### Warning

建立项目基线并固定编译器版本。

---

## 8. 链接选项传递

通过GCC Driver传给Linker通常使用：

```text
-Wl,option
```

例如：

```text
-Wl,-Map=app.map
-Wl,--gc-sections
-Wl,--cref
```

不要混淆：

```text
-Tlink.ld            GCC Driver识别并转交
-Wl,-T,link.ld       显式传给ld
```

具体工具链可能扩展不同语法。

---

## 9. GCC属性

### `section`

```c
__attribute__((section(".fast_code")))
void FastFunc(void);
```

只决定输入Section，不完成链接布局和复制。

### `aligned`

```c
__attribute__((aligned(32))) uint8_t buffer[128];
```

请求更高对齐；Linker和Memory Region仍需能够满足。

### `packed`

减少Padding，可能产生非对齐访问。

### `weak/alias`

默认Handler/可替换Hook。

### `used`

要求编译器发出对象，不阻止Linker GC。

### `noreturn`

```c
__attribute__((noreturn)) void Panic(void);
```

若函数实际返回，行为不符合声明，编译器可能省略返回后的正常控制流假设。

### `naked`

只用于受控汇编入口，禁止普通C逻辑依赖。

### `noinline/always_inline`

影响优化和可观测性，不是性能绝对保证。

### `interrupt`

语义与支持范围强烈依赖目标架构和编译器。M7异常Handler、TC3xx ISR/Trap应使用各自工具链官方模板。

---

## 10. CASE-03：`used`对象仍被删除

```c
__attribute__((used, section(".registry")))
const Entry_t entry = {...};
```

编译器生成了`.registry`，但`--gc-sections`把它删除。修复：

```ld
KEEP(*(.registry*))
```

验证：Map的Discarded Section与最终输出Section。

---

## 11. CASE-04：`naked`导致HardFault

普通C代码需要编译器自由使用栈和寄存器，`naked`却移除了ABI序言。正确模式是：

```text
最小naked汇编入口
→ 把必要上下文作为参数
→ 跳转到普通C函数
```

TC3xx使用其Trap/ISR ABI和CSA模型，不复用M7的MSP/PSP模板。

---

## 12. CASE-05：链接脚本变化没有触发重新链接

自定义Make规则只声明对象文件，没有把`link.ld`作为依赖：

```make
app.elf: $(OBJECTS)
```

应写：

```make
app.elf: $(OBJECTS) link.ld
```

CMake中把脚本作为`LINK_DEPENDS`或Target依赖：

```cmake
set_property(TARGET app.elf APPEND PROPERTY
    LINK_DEPENDS ${LINKER_SCRIPT})
```

精确方式依CMake版本/生成器验证。

---

## 13. CASE-06：Debug/Release宏不一致

```c
#ifdef DEBUG
    Watchdog_Service();
#endif
```

这会让Release不喂狗，属于设计错误。Debug宏不应控制必要功能。推荐：

- 功能由显式配置控制；
- Debug只控制诊断开销；
- 每个配置输出编译宏清单；
- 对Debug/Release均运行目标测试。

---

## 14. CASE-07：静态库链接顺序

```text
app.o需要A
libA中的A又需要B
libB提供B
```

库顺序错误可能undefined reference。定位：

- 查看最终link command；
- `nm -A`；
- Map Cross Reference；
- 只在必要时使用group；
- 优先消除循环依赖。

---

## 15. CASE-08：汇编文件未经过预处理

通常：

- `.s`：直接汇编；
- `.S`：先走C预处理器再汇编。

启动文件使用`#include/#if`却命名为`.s`，宏不会展开。CMake还需启用ASM语言并使用合适编译器。

---

## 16. 生成文件与源文件

SVD/配置工具可能生成：

- 寄存器头文件；
- MemMap；
- RTE/MCAL配置；
- Linker片段；
- Vector/Interrupt配置。

构建必须表达：

```text
输入配置
→ 生成命令
→ 生成文件
→ 编译Target依赖
```

禁止依靠工程师手工先运行工具而不进入依赖图，否则CI和本地结果可能不同。

---

## 17. 可重复构建

目标：相同源码、配置、工具链和环境产生可追踪的一致结果。

控制：

- 编译器/Linker/binutils版本；
- CMake/Ninja版本；
- 环境变量；
- 时间戳、绝对路径；
- 生成器版本；
- 库和Linker Script；
- 构建配置；
- 随机种子/归档顺序。

产物元数据：

```text
Git commit
Toolchain version
Configuration hash
ELF hash
BIN hash
Map
compile_commands.json
```

---

## 18. 构建后检查

在链接成功后自动执行：

1. `size`区域占用；
2. Map关键Symbol地址；
3. Section越界和重叠；
4. Vector/BMHD/Trap Table地址；
5. 栈/CSA最小容量；
6. 禁止Symbol扫描（如意外`malloc`）；
7. 未解析Weak Hook；
8. RAM代码VMA/LMA；
9. BIN/HEX生成；
10. 映像签名/CRC。

链接脚本`ASSERT`优于事后文本解析，但两者可互补。

---

## 19. 多目标工程组织

建议：

```text
platform/
  m7/
  tc3xx/
common/
drivers/
tests/
cmake/
linker/
startup/
```

公共代码只包含真正平台无关的C语义；平台差异通过接口隔离：

```c
void Platform_DataBarrier(void);
uint32_t Platform_EnterCritical(void);
void Platform_ExitCritical(uint32_t key);
```

不能为了“共用”把DMB和DSYNC、MSP/PSP和CSA抽象成语义错误的同一个实现。

---

## 20. M7与TC3xx配置隔离

| 项目 | M7 | TC3xx |
|---|---|---|
| 编译器 | arm-none-eabi-gcc | TriCore GNU/HighTec |
| CPU选项 | Cortex-M7/Thumb/FPU | Derivative/Core/EABI/FPU |
| 启动 | Vector/Reset_Handler | BMHD/SSW/Core startup |
| 链接 | GNU ld script | TriCore工具链脚本/LSL |
| 异常属性 | M-profile Handler ABI | TriCore ISR/Trap ABI |
| 库 | Arm EABI构建 | TriCore EABI构建 |

公共C库也要分别编译，不能把M7 `.a`链接到TC3xx。

---

## 21. CI建议

每次提交至少：

- 全量配置构建；
- Warning as Error；
- 单元测试；
- 静态分析；
- Map/Section检查；
- 栈使用检查；
- Debug/Release差异检查；
- 编译数据库归档；
- 发布哈希；
- 关键硬件Case定期运行。

---

## 22. 验证实验

### EXP-01：Make依赖

修改`.c/.h/link.ld/generated config`，验证最小且完整的重编译/重链接集合。

### EXP-02：CMake传播

建立PUBLIC/PRIVATE/INTERFACE库，使用`compile_commands.json`确认宏、头文件和选项只传播到预期Target。

### EXP-03：属性

分别验证`used/KEEP/aligned/section/naked/noinline`在编译、链接、运行阶段的真实效果。

### EXP-04：双平台

同一公共模块分别以M7和TC3xx工具链编译，检查接口类型静态断言、Warning和ABI专用代码隔离。

### EXP-05：可重复构建

清洁环境重复构建，比较ELF/BIN哈希；若不同，定位时间戳、路径和归档顺序。

---

## 23. 系统需求基线

| ID | 需求示例 |
|---|---|
| SYS-BUILD-001 | 编译器、Linker、binutils及构建工具版本应锁定并记录。 |
| SYS-BUILD-002 | 所有源、头文件、Linker Script和生成文件依赖应进入构建图。 |
| SYS-BUILD-003 | 每个Target的CPU/ABI/FPU选项应集中定义并禁止不一致对象链接。 |
| SYS-BUILD-004 | 发布构建应自动输出ELF、Map、BIN/HEX、大小和版本元数据。 |
| SYS-BUILD-005 | 关键Section地址和容量应在链接时自动检查。 |
| SYS-BUILD-006 | Debug宏不得删除安全相关必要功能。 |
| SYS-BUILD-007 | M7与TC3xx应使用独立Toolchain File、Build Directory和平台启动/链接文件。 |

---

## 24. 面试与评审问题

1. CMake、Ninja、GCC和ld分别做什么？
2. Make为什么需要头文件`.d`依赖？
3. CMake的PUBLIC/PRIVATE/INTERFACE有什么区别？
4. 为什么不同架构应使用独立Build Directory？
5. `section`属性为什么不等于完成RAM代码部署？
6. `used`与`KEEP`的区别是什么？
7. `.s`与`.S`有什么差别？
8. Linker Script为什么要作为链接依赖？
9. 怎样证明某个编译宏真正传给了目标文件？
10. 可重复构建需要记录哪些信息？

---

## 25. 小结

```text
CMake描述Target及使用需求
→ Ninja/Make根据依赖执行命令
→ GCC按统一CPU/ABI选项生成对象
→ Linker按脚本形成映像
→ Post-build检查并生成发布物
→ CI保证每个配置可重复和可追踪
```

至此编译器方向的四份理论文档完成。最后一份将用跨层案例把C、GCC、ELF、链接、启动、M7和TC3xx串成完整排障闭环。
