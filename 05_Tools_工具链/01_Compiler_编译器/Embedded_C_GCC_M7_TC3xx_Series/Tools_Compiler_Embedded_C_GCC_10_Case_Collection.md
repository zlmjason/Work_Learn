# Cortex-M7与AURIX TC3xx嵌入式C/GCC综合案例集

---

## 系列导航

- **返回总纲**：[[Tools_Compiler_Embedded_C_GCC_00_Series_Overview|00 学习总纲与进度]]
- **上一篇**：[[Tools_Compiler_GCC_09_Make_CMake_Build|09_Make_CMake_Build]]

---


> 用途：按“故障现象”快速查找，并沿C语义、GCC、链接/启动、M7和TC3xx硬件路径完成根因闭环。  
> 原则：案例代码用于解释机制，芯片寄存器、intrinsic和启动模板以项目实际头文件及工具链手册为准。

---

## 1. 通用排障流程

```text
1. 固定可复现条件
2. 保存构建配置、ELF、Map和寄存器现场
3. 判断：语言层 / 编译层 / 链接启动层 / CPU-SoC层
4. 查看预处理结果和最终编译命令
5. 查看反汇编、Symbol、Section和地址
6. 查看Fault/Trap、MPU、Cache和总线状态
7. 用最小改动验证假设
8. 修复根因，而不是降低优化或加延时
9. 添加正向、边界和负向回归Case
```

---

## 2. 快速索引

| 现象 | 优先案例 |
|---|---|
| `-O0`正常、`-O2`失败 | 01、02、03、15、22 |
| 偶发计数少一次 | 04、05 |
| DMA数据旧/错 | 06、07、08 |
| 非对齐Fault/Trap | 09、10 |
| 寄存器其他状态丢失 | 11、12 |
| RAM函数执行Fault | 18、19 |
| 复位后变量错误 | 20、21 |
| ISR进默认Handler | 16、17 |
| 链接重叠/容量错误 | 23、24 |
| 多核偶发死锁/竞态 | 25、26、27 |
| HardFault/Trap无法定位 | 28、29 |
| Make/CMake改动不生效 | 30、31、32 |

---

# 第一组：优化、volatile与未定义行为

## CASE-01：轮询变量在Release中死循环

### 错误代码

```c
uint32_t done;

while (done == 0U)
{
}
```

ISR修改`done`。

### 根因

普通对象在当前执行流中没有可见修改，GCC可只读一次并把值保存在寄存器。`-O0`重复Load只是实现偶然。

### 修复

单核ISR简单标志：

```c
static volatile uint32_t done;
```

如果是多核或DMA，还需：

- 原子/内存序；
- Cache维护；
- 所有权；
- 平台屏障。

### 验证

比较`-O0/-O2`反汇编中的Load次数；分别由ISR、DMA、另一核修改，证明三种场景需求不同。

---

## CASE-02：strict aliasing导致Release结果错误

```c
float f = 1.0F;
uint32_t bits = *(uint32_t *)&f;
```

### 根因

通过不兼容类型指针访问违反别名/有效类型规则；`-O2`可基于无别名假设优化。

### 修复

```c
uint32_t bits;
memcpy(&bits, &f, sizeof(bits));
```

### 双平台

M7和TC3xx都受C/GCC规则约束；硬件都能读取同一比特不代表C表达式合法。

### 验证

比较`-O0/-O2/-fno-strict-aliasing`与`memcpy`。最终修复保留`memcpy`，不依赖关闭优化。

---

## CASE-03：有符号溢出检查被优化

```c
bool Overflowed(int32_t x)
{
    return ((x + 1) < x);
}
```

### 根因

有符号溢出是UB，编译器可认为`x+1`合法时不会小于`x`。

### 修复

```c
bool AddOne(int32_t x, int32_t *out)
{
    if (x == INT32_MAX)
    {
        return false;
    }
    *out = x + 1;
    return true;
}
```

### 系统结论

错误检测不能依赖先触发UB再观察硬件回绕。

---

## CASE-04：`volatile counter++`丢失更新

任务和ISR都执行：

```c
counter++;
```

### 根因

Load-Add-Store可被抢占。

### M7

单核使用PRIMASK/BASEPRI临界区；多Master使用原子机制。

### TC3xx

本核可用受控中断临界区；多核使用LDMST/CMPSWAP等系统可见原子机制。

### 验证

高频中断/双核压力下比较期望递增总数与实际值。

---

## CASE-05：64-bit时间戳撕裂

32-bit MCU上ISR更新`uint64_t tick`，Task直接读取。

### 根因

一条C读取可能被实现为多个32-bit访问，ISR可插入中间。

### 修复选择

- 短临界区；
- sequence counter；
- 高-低-高重复读；
- 经验证的原子库；
- 硬件锁存寄存器。

### 验证

让低32位频繁回绕，检查是否出现时间倒退或非法高低组合。

---

# 第二组：DMA、Cache与所有权

## CASE-06：CPU发送Buffer，DMA读到旧数据

```c
Fill(tx_buffer);
Dma_Start(tx_buffer, length);
```

### 根因

Write-back DCache中的Dirty Line尚未写入RAM，DMA绕过CPU Cache。

### M7

Clean覆盖的Cache Line，执行规定屏障，再启动DMA。

### TC3xx

先判断Buffer地址的数据Cacheability、DLMU/LMU路径和DMA系统地址，再执行相应Cache维护/同步。

### 验证

预先让RAM和Cache内容不同，通过外设回环检查DMA实际数据。

---

## CASE-07：DMA接收完成，CPU仍读旧数据

### 根因

CPU此前缓存了rx Buffer旧内容；DMA只更新RAM。

### 修复

DMA拥有Buffer期间CPU不得读写；完成后按Line invalidate并执行规定屏障，再交给CPU。

### 负向Case

不invalidate、只把数组声明为volatile，预期仍可复现旧数据。

---

## CASE-08：Invalidate丢失邻近变量

DMA Buffer没有按Cache Line隔离，邻近普通变量与其共享一行。CPU修改邻近变量后直接invalidate整行，Dirty数据被丢弃。

### 修复

- 起始按Cache Line对齐；
- 占用长度按Line取整；
- 独立Section；
- 或clean后再invalidate，但仍需所有权设计。

### 系统结论

Cache维护范围是物理Line，不是C数组边界。

---

# 第三组：对齐、结构体与访问宽度

## CASE-09：奇地址`uint64_t *`导致Fault

```c
uint8_t buf[16];
uint64_t value = *(uint64_t *)&buf[1];
```

### C层

对齐和有效类型均可能无效。

### M7

可能拆分访问，也可能因指令、Memory Type或`UNALIGN_TRP`Fault。

### TC3xx

行为取决于访问宽度、地址区域和总线；即使某DMI路径支持部分非对齐，也不能合法化C对象访问。

### 修复

```c
uint64_t value;
memcpy(&value, &buf[1], sizeof(value));
```

---

## CASE-10：packed DMA描述符不工作

### 根因

packed使32-bit地址成员位于奇偏移，CPU和DMA看到的布局/对齐不满足IP要求。

### 修复

按硬件描述符格式显式布置32-bit字段和reserved，使用`aligned`与`_Static_assert`。

### 验证

检查`sizeof/offsetof`、反汇编访问宽度、DMA错误状态和描述符总线地址。

---

## CASE-11：W1C寄存器被`|=`误清

```c
STATUS |= ERROR_Msk;
```

### 根因

读取到的其他状态1在写回时也作为1写入，从而一起清除。

### 修复

```c
STATUS = ERROR_Msk;
```

前提是手册确认W1C语义。

### 双平台

与M7或TC3xx内核无关，属于外设寄存器语义；但总线宽度和Store Buffer还会影响实际事务。

---

## CASE-12：两个执行者RMW置不同bit，最终少一位

### 根因

双方都基于旧值计算并覆盖对方更新。

### 修复

- SET/CLR寄存器；
- M7独占访问/临界区；
- TC3xx LDMST/CMPSWAP；
- 单一驱动所有权。

### 验证

双核/ISR重复百万次，同时置不同bit，统计非法最终值。

---

## CASE-13：结构体CRC偶发不一致

```c
crc = Crc32((uint8_t *)&object, sizeof(object));
```

### 根因

Padding未初始化，字段相同但Padding字节不同。

### 修复

对显式序列化字节流计算CRC；持久化格式包含版本和长度。

---

## CASE-14：协议结构体升级后老数据无法读取

新增成员或ABI变化改变`sizeof/offset`。

### 修复

- 禁止直接持久化C结构体内存镜像；
- 明确定长字段、端序、版本、CRC；
- 提供版本迁移。

---

# 第四组：函数指针、中断与异常入口

## CASE-15：回调上下文悬空

```c
void Init(void)
{
    uint32_t state;
    RegisterCallback(OnEvent, &state);
}
```

### 根因

异步回调执行时局部对象生命周期已结束。

### 修复

使用模块静态上下文、调用者长期对象或显式所有权对象。

---

## CASE-16：M7进入Default_Handler

### 检查链

1. ICSR读取当前Vector；
2. NVIC pending/enable/priority；
3. VTOR基址和对齐；
4. 向量表对应word；
5. `nm`确认用户Handler Symbol；
6. 检查C++名称修饰、static、拼写；
7. 检查weak alias是否被强定义覆盖。

### 根因示例

用户实现`UART0_IRQHandler`，启动文件期待`USART0_IRQHandler`。

---

## CASE-17：TC3xx中断/Trap入口错误

### 检查链

- SRC路由、SRE、TOS和优先级；
- 当前核ICR/CCPN；
- BIV/BTV基址与对齐；
- Vector Spacing；
- Table Section是否被KEEP；
- ISR/Trap函数属性和工具链ABI；
- CSA是否有效。

不能按M7的“一个Vector Table数组+函数指针”模型定位全部TC3xx问题。

---

## CASE-18：naked HardFault Handler二次Fault

### 根因

naked函数中写普通C代码，编译器可能使用未建立的栈/保存规则。

### 修复

最小汇编入口选择MSP/PSP并跳转普通C分析函数；覆盖基本/扩展FPU栈帧。

### TC3xx

Trap使用CSA和A11等现场，必须使用TriCore模板，不能复用M7汇编。

---

# 第五组：链接、启动与RAM代码

## CASE-19：函数标记RAM Section但仍从Flash执行/直接Fault

### 根因列表

- Linker Script未收集；
- VMA仍在Flash；
- 未定义LMA；
- 启动未复制；
- I-Cache未失效；
- MPU XN；
- 调用地址/Thumb状态错误；
- 被调函数或常量仍在忙Flash。

### 验证

Map＋`nm`确认VMA；ELF确认LMA；比较RAM与Flash字节；反汇编单步确认PC区域。

---

## CASE-20：`.data`变量复位后初值错误

### 证据链

1. Symbol是否在`.data`；
2. ELF中是否有正确初值；
3. LMA/VMA；
4. Copy Table；
5. 复制长度/单位；
6. 复制后是否被其他核/初始化覆盖；
7. RAM ECC初始化顺序。

### M7/TC3xx差异

M7通常单一Reset Handler；TC3xx多核和Boot/SSW流程使初始化责任更复杂。

---

## CASE-21：`.noinit`在warm reset后被清

### 根因

- 通配符被`.bss*`捕获；
- Clear Table覆盖；
- BootROM/MBIST初始化RAM；
- 所选RAM不保持；
- Debug器重写。

### 修复

NOLOAD独立Section＋Map检查＋复位矩阵＋magic/version/CRC。

---

## CASE-22：Vector/BMHD/注册表被GC

### 根因

`used`只保证编译器发出，Linker `--gc-sections`仍删除不可达Section。

### 修复

链接脚本：

```ld
KEEP(*(.isr_vector))
KEEP(*(.boot_header*))
KEEP(*(.registry*))
```

实际Section名按平台工程。

---

## CASE-23：Section地址重叠

### 现象

Linker报告两个地址区间相交。

### 根因

- 固定起始地址预算不足；
- Section增长；
- ALIGN扩大；
- VMA/LMA混淆；
- 多核窗口重叠；
- 地址单位错误。

### 修复

顺序布局、明确边界Symbol、使用`ASSERT`；不能只减少一个数组让错误暂时消失。

---

## CASE-24：Flash/RAM占用突然增加

### 定位

- 比较两版Map；
- 按`.o/.a`统计Section增长；
- 检查内联、模板/库、浮点格式化；
- 检查LTO开关；
- 检查重复常量和Debug宏；
- 检查对齐空洞。

### 系统化

CI建立各Memory Region预算和增长阈值。

---

# 第六组：多核、原子与Store Buffer

## CASE-25：普通Load/Store实现Spinlock，两个核同时进入

```c
while (lock != 0U) {}
lock = 1U;
```

### 根因

检查和设置不是不可分割事务。

### M7

使用C原子或LDREX/STREX，并确认SoC全系统独占监视与Shareable属性。

### TC3xx

使用CMPSWAP/SWAP等原子机制和DSYNC定义锁内数据顺序。

### 验证

临界区内维护`inside_count`，若大于1则记录失败；多核高负载运行。

---

## CASE-26：多核Mailbox先看到flag后看到旧数据

### 根因

数据和flag缺少release/acquire顺序，或Cache/地址别名不一致。

### 修复

- 共享区地址属性统一；
- 生产者完成数据写/clean；
- release屏障后发布原子flag；
- 消费者acquire读取flag，再invalidate/读数据；
- 单一所有权。

### TC3xx重点

检查DSPR本地/全局别名、DLMU/LMU路径、DCacheability和SRI可见性。

---

## CASE-27：Flash Load Page命令偶发SQER

### 场景

连续两个32-bit Store装载Page数据。

### 根因

TC1.6.2P Store Buffer可能把相邻32-bit写合并为64-bit，而DMU要求同一Page所有Load Page传输宽度一致。

### 修复

按TC3xx手册在32-bit写之间DSYNC/read-back，或统一使用合法64-bit接口；命令使用non-cached地址。

### 验证

开启/关闭Store Buffer、插入/移除DSYNC，检查总线事务宽度和SQER。

---

# 第七组：Fault/Trap定位

## CASE-28：M7 HardFault定位闭环

### 现场保存

- stacked R0-R3、R12、LR、PC、xPSR；
- EXC_RETURN；
- CFSR/HFSR；
- BFAR/MMFAR及有效位；
- SHCSR/ICSR；
- MSP/PSP；
- FPU扩展帧状态。

### 分析

1. EXC_RETURN判断使用MSP/PSP和帧类型；
2. CFSR分解MemManage/BusFault/UsageFault；
3. `addr2line`定位PC；
4. 反汇编确认访问指令和寄存器地址；
5. 回查指针、MPU、Cache和总线。

### 注意

异步/imprecise BusFault的stacked PC可能晚于原始Store。

---

## CASE-29：TC3xx Trap定位闭环

### 现场保存

- Trap Class/TIN；
- A11/返回地址；
- PCXI/CSA上下文；
- DSTR/DATR/DEADD或对应Trap寄存器；
- PIETR/DIETR等完整性信息；
- MPU/保护和SMU状态。

### 分析

1. 区分同步DSE与异步DAE；
2. 根据Trap Class/TIN选择寄存器；
3. 解析CSA恢复寄存器；
4. 使用匹配ELF反查；
5. 若Overlay/地址别名启用，映射到链接地址；
6. 检查Store Buffer和总线桥是否导致延迟报告。

---

# 第八组：构建系统

## CASE-30：修改头文件，目标文件没有重编译

### 根因

Make规则缺少自动头文件依赖。

### 修复

使用`-MMD -MP`并包含`.d`文件；CMake/Ninja检查依赖扫描。

### 闭环

不要只执行Clean Build；证明依赖图已修复。

---

## CASE-31：CMake宏没有生效

```cmake
set(FLAGS -DENABLE_FEATURE)
```

### 根因

只设置CMake变量，未绑定Target。

### 修复

```cmake
target_compile_definitions(app PRIVATE ENABLE_FEATURE=1)
```

### 验证

检查`compile_commands.json`和预处理输出。

---

## CASE-32：替换Linker Script但ELF未变化

### 根因

脚本未进入Target链接依赖，增量构建没有重新链接；或实际link command使用了另一个同名脚本。

### 修复

- 打印最终link command；
- 使用绝对路径；
- 把脚本加入`LINK_DEPENDS`/Make prerequisites；
- 在Map头或构建元数据记录脚本版本。

---

# 第九组：补充高频工程案例

## CASE-33：大局部数组引发偶发异常

### 根因

任务栈溢出，破坏保存现场/控制块。M7还可能在异常压栈时Fault；TC3xx同时要区分A10软件栈与CSA耗尽。

### 验证

- `-fstack-usage`；
- 栈填充水位；
- MPU Guard；
- 最大中断嵌套；
- TC3xx FCX/LCX/CSA余量。

---

## CASE-34：TC3xx运行一段时间后ENDINIT clear卡住

### 排除“密码被别人改”之后的重点

- Task/ISR重入同一WDT序列；
- 多核竞争Safety ENDINIT；
- clear/set异常路径不配对；
- Store Buffer/同步；
- WDT状态和访问保护；
- 超时/Trap后上下文恢复。

### 修复结构

```text
获取本核/全局锁
→ 保存中断状态
→ 执行规范clear序列
→ 修改受保护寄存器
→ 执行规范set序列
→ 恢复中断
→ 释放锁
```

并保证任何错误路径都恢复保护或进入安全反应。

---

## CASE-35：Flash 30 ns但代码没有每条停9周期

### 先把时钟换算正确

300 MHz CPU的单周期为：

```text
Tcpu = 1 / 300,000,000 s = 3.333... ns
30 ns / 3.333... ns ≈ 9 cycles
```

所以不是“300 MHz等于3 ns”，而是约`3.33 ns/cycle`。但这9周期只表示30 ns大约跨越多少个CPU周期，不能推出“每条指令固定等待9周期”。

### 为什么没有每条都等9周期

TC3xx程序指令通常是16/32-bit，但取指系统按更宽粒度搬运和复用数据。PCache和PLB的Line为256-bit/32-byte；BTR4由4个64-bit Beat组成，并支持critical double-word first。PCache、PLB和PFI中的FPB进一步隐藏Flash阵列延迟。

因此30 ns更接近一次底层Flash读取相关的延迟参数，而不是每条C语句、每条机器指令或每个64-bit Beat都重复支付的固定成本。首次miss、线性执行、Taken Branch、跨Line、Bank冲突和其他Master争用的表现会不同。

### FPB和PLB不要混淆

| 对比项 | Flash Prefetch Buffer，FPB | Program Line Buffer，PLB |
|---|---|---|
| 所在位置 | PFI的Flash预取路径 | CPU的PMI取指路径 |
| 核心作用 | 推测性准备后续PFlash数据，隐藏线性读取延迟 | 在non-cacheable程序访问或PCache bypass时保存当前256-bit程序行 |
| 数据来源/粒度 | 服务BTR4等Flash访问，可按Master Tag分配 | BTR4填充一条256-bit Line，critical double-word优先 |
| 典型命中 | 后续请求命中已预取的数据 | 后续取指仍落在当前同一程序行 |
| 关键误区 | non-cached地址不自动等于所有PFI预取都关闭 | PCache bypass不等于每条16/32-bit指令都直接访问Flash阵列 |

还要区分CPU指令宽度、PMI返回宽度、Line宽度和Flash物理/ECC组织：

- CPU实际指令16/32-bit；
- PMI一次向取指单元返回64-bit；
- PCache/PLB Line为256-bit；
- Flash Prefetch Buffer位于PFI，提前准备后续BTR4数据；
- PLB位于PMI，保存当前non-cache/bypass程序行。

### 验证

1. 让测试代码规模大于PCache，避免只测到热Cache；
2. 分别控制PCache bypass、PLB失效、PFI Demand Mode和FPB配置；
3. 对比线性执行、每Line跳转和随机分支；
4. 使用性能计数器测PMEM stall，并记录PFlash频率、wait-state和ECC配置；
5. 不要用GPIO总时间反推单次Flash阵列访问，除非已扣除流水线、分支和循环开销。

### 可落地系统需求

| ID | 系统需求示例 |
|---|---|
| SYS-PERF-FLASH-001 | 系统应根据CPU/PFlash时钟、数据手册时序上限及温压范围，在升频前配置合法的Flash wait-state。 |
| SYS-PERF-FLASH-002 | Flash最坏执行时间测试应分别覆盖冷Cache、跨Line分支、FPB关闭/Demand Mode及Bank争用场景。 |
| SYS-PERF-FLASH-003 | 性能报告应区分指令宽度、接口传输宽度、Cache/PLB Line宽度和Flash读取/ECC粒度。 |
| SYS-PERF-FLASH-004 | 若安全机制要求禁用或限制预取，软件应验证已有预取数据的处理、失效流程及其时序影响。 |

---

## 3. 案例验证统一格式

每个问题进入项目测试库时，应转成：

```text
CASE ID
目标风险
前置条件
内存/MPU/Cache配置
编译器和优化选项
测试步骤
观测量
预期结果
失败判据
恢复措施
覆盖的系统需求
```

例如非对齐访问不能只写“访问后不死机”，应覆盖：

- 偏移0～访问宽度-1；
- 普通RAM、Device、跨Region、跨Cache Line；
- M7 `UNALIGN_TRP`开关；
- TC3xx不同存储区域；
- Load/Store、16/32/64-bit；
- Fault/Trap寄存器；
- `-O0/-O2`指令差异。

---

## 4. 现场问题最小证据包

### 编译与映像

- 完整ELF；
- Map；
- BIN/HEX hash；
- GCC/Linker版本；
- 编译和链接命令；
- Linker Script；
- `compile_commands.json`。

### M7

- stacked frame；
- CFSR/HFSR/BFAR/MMFAR；
- ICSR/SHCSR；
- MSP/PSP/CONTROL/BASEPRI/PRIMASK；
- MPU Region；
- Cache状态与维护范围。

### TC3xx

- Trap Class/TIN；
- A11/PCXI/CSA；
- DSTR/DATR/DEADD及相关完整性寄存器；
- BIV/BTV/ICR；
- MPU/Safety Protection；
- SMU Alarm；
- Cache、SRI和WDT/ENDINIT状态。

---

## 5. 代码审查Checklist

### C语言

- [ ] 有无越界、悬空、非对齐或别名违规？
- [ ] 有符号/无符号混合是否清晰？
- [ ] 宽运算是否在运算前扩展？
- [ ] volatile是否被误当原子/Cache方案？
- [ ] 结构体是否被直接用于协议/NVM？
- [ ] W1C/Read-Clear是否执行RMW？
- [ ] ISR/任务/多核/DMA读写者是否明确？

### GCC/链接

- [ ] 所有对象ABI/FPU选项一致？
- [ ] `-O2/LTO`回归通过？
- [ ] 关键Section同时有`used/KEEP`策略？
- [ ] VMA/LMA和Copy/Clear Table正确？
- [ ] Map无Orphan/重叠/越界？
- [ ] RAM代码依赖闭包完整？

### M7/TC3xx硬件

- [ ] MPU/Cache属性正确？
- [ ] Cache维护范围按Line？
- [ ] 屏障和Slave完成语义正确？
- [ ] 异常/Trap现场足够？
- [ ] M7栈与TC3xx栈/CSA预算正确？
- [ ] 多核锁为系统级原子？

---

## 6. 最终方法论

一个成熟的故障结论应能够写成：

```text
由于【哪条C/ABI/硬件规则】
在【哪个编译选项、地址属性和并发条件】下
GCC生成了【什么关键指令/Section】
CPU/总线实际执行了【什么事务】
从【反汇编、Map、Fault/Trap、波形】得到证据
因此造成【可复现现象】
修复为【明确机制】
并由【正向＋负向＋边界Case】防止回归
```

如果结论只是“加volatile好了”“关优化好了”“多加一个DSB好了”“Clean Build好了”，说明根因闭环还没有完成。
