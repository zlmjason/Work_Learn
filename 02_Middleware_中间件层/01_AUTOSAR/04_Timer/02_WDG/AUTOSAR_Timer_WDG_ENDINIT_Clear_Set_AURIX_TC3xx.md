# AURIX TC3xx：MCAL 视角下 WDT/ENDINIT Clear 与 Set 机制详解

> 主题：为什么 MCAL 不能只看 `clearEndinit()` / `setEndinit()` 两个小函数，而要结合 SchM Exclusive Area、OS 临界区、Spinlock、Trusted Function、SMU 错误处理一起理解。
>
> 适用背景：AURIX TC3xx、AUTOSAR MCAL、RTOS 多任务/多核运行期、Flash/MCU/Port/Fls 等驱动访问 ENDINIT protected SFR。

---

## 0. 先给结论

在 AURIX TC3xx 上，`clear ENDINIT` 和 `set ENDINIT` 的硬件动作本身很短：

```text
clear:  写一次合法 Password Access  -> ENDINIT = 0
set:    写一次合法 Modify Access    -> ENDINIT = 1
```

但是在 MCAL 运行环境中，真正需要保护的不是这两个函数本身，而是整个临界区：

```text
SchM_Enter / OS 临界区 / Spinlock / Trusted Function
    clear ENDINIT
    写 ENDINIT protected SFR
    set ENDINIT
SchM_Exit / 释放锁
```

原因很简单：`ENDINIT = 0` 是一个短暂的硬件访问窗口。如果中途被 ISR、其他 Task、其他 Core 或嵌套驱动打断，另一个上下文执行了 `set ENDINIT`，当前上下文就可能出现：

```text
我刚 clear，为什么 while 等不到 ENDINIT == 0？
```

或者后续写 protected SFR 被丢弃，产生 SMU alarm。

---

## 1. Why：为什么要有 ENDINIT clear/set？

### 1.1 ENDINIT 保护的本质

AURIX 里有很多 SFR 不是普通运行期频繁改的寄存器，而是系统级配置寄存器，例如：

- Clock / PLL / CCU / CLC
- Flash / DMU 控制寄存器
- SCU / Reset / Trap / Protection 相关寄存器
- 部分 CPU CSFR，例如 ISP、SYSCON、PMA、Cache/Memory 配置等
- Safety 关键配置寄存器

这些寄存器一旦在运行期被误写，影响不是局部功能异常，而可能是：

```text
时钟异常、Flash 编程异常、总线错误、复位异常、保护配置破坏、安全机制失效
```

所以 AURIX 引入 ENDINIT / SAFETY_ENDINIT 机制。Safety Manual 里对 ENDINIT 的定义很明确：一些 SFR 通常只在初始化阶段配置，运行期误改会严重影响功能块；如果没有解除 ENDINIT 保护就写这些寄存器，写操作会被丢弃，SFR 不改变，并产生 alarm。典型 alarm 接口包括 `SMU ALM7[20] - SPB Bus Error Event`。

### 1.2 ENDINIT 不是普通 bit 位

以 `SCU_EICON0` 为例，它是 Global ENDINIT Control Register 0：

```text
bit0      Reserved
bit1      ENDINIT
bit[15:2] EPW
bit[31:16] REL
```

其中 `ENDINIT` 当前值由硬件控制：

```text
合法 Password Access 之后，硬件清 ENDINIT -> 0
合法 Modify Access 之后，硬件置 ENDINIT -> 1
```

写入 `ENDINIT` bit 的值只是参与 password-protection 判断，不是普通的“软件写 0/写 1 存进去”。因此下面这种理解是错的：

```c
SCU_EICON0.B.ENDINIT = 0;   // 错误理解：直接写 bit 就能清 ENDINIT
```

正确理解是：必须构造合法的 Password Access 或 Modify Access，一次性 32-bit 写入控制寄存器。

### 1.3 为什么 MCAL 要包临界区？

因为 ENDINIT 打开的窗口是全局/系统状态，并且还有 timeout 监控。

ENDINIT 保护被解除后，软件必须在有限时间内重新 set 回去。Safety Manual 对 ENDINIT watchdog 机制的描述是：如果 Application SW 没有在有限时间窗口内结束 ENDINIT deactivation，会触发 watchdog alarm，并转发到 SMU。

所以 MCAL 的目标不是“方便写寄存器”，而是保证：

| 目标 | 说明 |
|---|---|
| 窗口短 | clear 到 set 中间只做必要 protected SFR 写入 |
| 不可重入 | 防止 ISR/Task/Core 嵌套 clear/set |
| 不被抢占破坏 | 防止另一个上下文提前 set 回去 |
| 错误可诊断 | clear/set 失败、timeout、access error 要有处理 |
| 符合 AUTOSAR 集成 | 通过 SchM / OS / Trusted Function 管理并发与权限 |

---

## 2. What：AURIX TC3xx 里到底有几类 ENDINIT？

### 2.1 CPU ENDINIT

对应 CPU Watchdog 的 `SCU_WDTCPUyCON0.ENDINIT`。

常见用途：访问 CPU 相关 ENDINIT protected CSFR / SFR。

特点：

- 每个 CPU core 有自己的 CPU watchdog。
- `WDTCPUyCON0` 有 `ENDINIT`、`LCK`、`PW`、`REL` 等字段。
- `LCK` 由硬件控制：合法 Password Access 后解锁，合法 Modify Access 后重新锁定。
- `ENDINIT` 在 Password Access / Check Access 期间必须写 1，在 Modify Access 期间写目标更新值。
- `PW` 读出时部分 bit 会 toggle/invert，防止简单 read-write 即可喂狗/解锁。

典型寄存器表里 `SCU_WDTCPUyCON0` 的写访问要求是 32-bit，并且与具体 CPU master 相关。

### 2.2 Global/System ENDINIT

对应 `SCU_EICON0.ENDINIT`。

常见用途：访问 system ENDINIT protected SFR，例如很多模块的 CLC、FDR、SCU 系统配置等。

特点：

- `SCU_EICON0` 是 Global ENDINIT Control Register 0。
- `ENDINIT` 位在 bit1，bit0 是 reserved。
- `EPW` 是独立于 CPU WDT password 的 ENDINIT password。
- Password Access 后 `ENDINIT=0`。
- Modify Access 后 `ENDINIT=1`。
- `REL` 固定读为 `0xFFFC`，Password Access 时要写当前内容。
- TC39x-B Appendix 里 `SCU_EICON0` 写访问条件为 `U,SV,32,P0`。

这点对你的问题很关键：如果写访问不是 32-bit，或者当前 master 不满足 P0 access protection，即使 password 没问题，写操作也可能不生效。

### 2.3 Safety ENDINIT

对应 `SCU_SEICON0.ENDINIT` 或 Safety WDT 相关控制。

常见用途：访问 Safety ENDINIT protected SFR。

特点：

- `SEICON0.ENDINIT` 也是 bit1，bit0 reserved。
- `EPW` 是 Safety ENDINIT password，独立于 CPU WDT / WDTS password。
- `SEICON0` 写访问通常受 P1 类访问保护约束。
- Safety ENDINIT 相关寄存器错误状态在 `SEISR` 中体现。

### 2.4 三者对比

| 类型 | 典型寄存器 | 保护对象 | 是否 per-core | 访问风险 |
|---|---|---|---|---|
| CPU ENDINIT | `WDTCPUyCON0` | CPU/CEy 相关寄存器 | 是 | 本核中断/任务重入、password/LCK 序列错误 |
| Global/System ENDINIT | `EICON0` | 系统 ENDINIT protected SFR | 否，系统级 | 多核/多任务/ISR 竞争，ACCEN/P0，32-bit 访问 |
| Safety ENDINIT | `SEICON0` / `WDTSCON0` | Safety protected SFR | 否，系统级 | Safety 关键配置，P1/SE 保护，SMU alarm |

---

## 3. How：硬件层 clear/set 的具体操作

### 3.1 Global ENDINIT clear：Password Access

目标：打开 Global ENDINIT protected SFR 写窗口。

伪代码：

```c
#define EICON0_ENDINIT_MASK   (1UL << 1U)
#define EICON0_EPW_MASK       (0x3FFFUL << 2U)
#define EICON0_REL_MASK       (0xFFFFUL << 16U)

void ClearGlobalEndinit(uint16 password)
{
    volatile uint32 *EICON0 = (volatile uint32 *)SCU_EICON0_ADDR;

    uint32 before  = *EICON0;
    uint32 rel     = before & EICON0_REL_MASK;
    uint32 epw     = ((uint32)password << 2U) & EICON0_EPW_MASK;
    uint32 writeV  = rel | epw;          // ENDINIT bit1 = 0, bit0 = 0

    *EICON0 = writeV;                    // 必须 32-bit write
    __dsync();                           // 确保外设写完成，按编译器/平台替换

    while ((*EICON0 & EICON0_ENDINIT_MASK) != 0U)
    {
        /* 加 timeout，不要死等 */
    }
}
```

关键点：

| 点 | 要求 |
|---|---|
| 写宽度 | 32-bit |
| ENDINIT bit | Password Access 时写 0 |
| EPW | 写当前合法 password |
| REL | Password Access 时写当前读出值，通常 `0xFFFC0000` |
| 轮询 | 看 bit1，不是 bit0 |
| 错误处理 | 不能永久 while，必须有 timeout + dump |

### 3.2 Global ENDINIT set：Modify Access

目标：关闭 Global ENDINIT protected SFR 写窗口。

伪代码：

```c
void SetGlobalEndinit(uint16 password)
{
    volatile uint32 *EICON0 = (volatile uint32 *)SCU_EICON0_ADDR;

    uint32 epw    = ((uint32)password << 2U) & EICON0_EPW_MASK;
    uint32 writeV = epw | EICON0_ENDINIT_MASK;  // ENDINIT bit1 = 1

    *EICON0 = writeV;                           // Modify Access
    __dsync();

    while ((*EICON0 & EICON0_ENDINIT_MASK) == 0U)
    {
        /* 加 timeout */
    }
}
```

注意：`set` 时必须写 ENDINIT bit1 = 1。若误写 `(1U << 0U)`，对 AURIX 原厂 EICON0/SEICON0 来说就是写 reserved bit，不是写 ENDINIT。

### 3.3 CPU ENDINIT clear/set：带 LCK 的两步访问

CPU WDT 的 `WDTCPUyCON0` 多了 `LCK` 机制。

clear CPU ENDINIT 的典型逻辑：

```text
Step 1: Password Access
    ENDINIT = 1
    LCK     = 0
    PW      = current password
    REL     = current reload
    写 WDTCPUyCON0
    等 LCK == 0

Step 2: Modify Access
    ENDINIT = 0
    LCK     = 1
    PW      = current password / next password
    REL     = current reload
    写 WDTCPUyCON0
    等 LCK == 1
```

set CPU ENDINIT 类似，只是 Modify Access 时 `ENDINIT = 1`。

CPU WDT 的关键不是只看 `ENDINIT`，还要看 `LCK` 是否完成硬件状态转换。

---

## 4. MCAL 层到底怎么做？

### 4.1 MCAL 不应只保护 clear 函数

错误设计：

```c
SchM_Enter();
ClearGlobalEndinit();
SchM_Exit();

/* 中间暴露 */
MODULE_CLC.U = xxx;

SchM_Enter();
SetGlobalEndinit();
SchM_Exit();
```

这个设计没有意义。因为真正危险的窗口是：

```text
clear ENDINIT 之后，到 set ENDINIT 之前
```

正确设计：

```c
SchM_Enter_Module_EXCLUSIVE_AREA();

ClearGlobalEndinit();
MODULE_CLC.U = xxx;
(void)MODULE_CLC.U;      // readback / sync
SetGlobalEndinit();

SchM_Exit_Module_EXCLUSIVE_AREA();
```

也就是说，MCAL 的保护点通常在模块驱动操作层，而不是在 `Wdt_ClearEndinit()` 内部。

### 4.2 典型 MCAL 调用模型

以 Fls / Mcu / Port / Gtm / Can 等 MCAL 模块为例，典型结构如下：

```c
void Fls_lProtectedDmuWrite(...)
{
    SchM_Enter_Fls_FLS_EXCLUSIVE_AREA_0();

    Mcal_ResetENDINIT();      /* clear */

    DMU_REGISTER.U = value;
    dummy = DMU_REGISTER.U;   /* readback */

    Mcal_SetENDINIT();        /* set */

    SchM_Exit_Fls_FLS_EXCLUSIVE_AREA_0();
}
```

`SchM_Enter` 最终展开成什么，由 AUTOSAR OS / MCAL 集成决定。

常见实现：

| SchM 实现 | 能防什么 | 不能防什么 |
|---|---|---|
| 空宏 | 什么都不防 | ISR、Task、多核都不防 |
| SuspendAllInterrupts | 本核中断抢占 | 其他 Core，不一定防所有 Task 资源竞争 |
| SuspendOSInterrupts | OS 管理中断 | 非 OS 管理中断、其他 Core |
| GetResource | Task 级互斥 | 高优先级 ISR、其他 Core |
| GetSpinlock | 多核互斥 | 本核 ISR 仍需结合中断屏蔽 |
| Trusted Function | 用户态切特权态 | 并发仍需 SchM/Spinlock |

### 4.3 为什么 iLLD 看起来没这么复杂？

iLLD 更多是 low-level/demo 风格，常见假设是：

```text
启动阶段调用
中断未完全打开
单核主控
没有 RTOS 并发
调用者自己保证上下文安全
```

因此 iLLD 代码可能只是：

```c
password = getPassword();
clearEndinit(password);
MODULE_CLC.U = value;
setEndinit(password);
```

这在 startup 阶段通常够用。但在 MCAL + RTOS + 多核运行期，就不够了。MCAL 需要通过 SchM / OS integration / Spinlock 把“ENDINIT 访问窗口”保护起来。

---

## 5. RTOS/ISR 重入 clear/set ENDINIT 的具体场景

### 5.1 场景一：Task A clear 后，被 ISR set 回去

```text
T0  Task A: Flash_ProgramDFlash()
T1  Task A: ClearGlobalEndinit()
T2  硬件 ENDINIT = 0
T3  Task A 还没读到 ENDINIT == 0
T4  STM ISR 进入
T5  ISR 内某驱动：ClearGlobalEndinit(); 写 CLC; SetGlobalEndinit();
T6  硬件 ENDINIT = 1
T7  返回 Task A
T8  Task A while (ENDINIT != 0) 永远等不到 0
```

此时密码没变，地址没错，clear 也可能短暂成功过。但因为另一个上下文把 ENDINIT set 回去了，所以 Task A 看到的是 1。

### 5.2 场景二：两个 Task 都访问 protected SFR

```text
Task_Flash:
    clear ENDINIT
    写 DMU
    set ENDINIT

Task_Mcu:
    clear ENDINIT
    写 PLL/CLC
    set ENDINIT
```

如果没有 SchM/Resource/Spinlock，两个 Task 之间可能交错，导致：

```text
Task_Flash 以为窗口开着，但 Task_Mcu 已经 set 回去了
```

后果：

- clear while 卡住；
- protected SFR 写不进去；
- EISR.AE / OE；
- SMU ALM7[20] SPB Bus Error；
- ENDINIT watchdog alarm。

### 5.3 场景三：多核并发

```text
CPU0:
    clear Global ENDINIT
    写 DMU
    set Global ENDINIT

CPU1:
    clear Global ENDINIT
    写 SCU/CLC
    set Global ENDINIT
```

`SuspendAllInterrupts()` 只能防 CPU0 本核 ISR，不能防 CPU1。因此多核 TC3xx 上，Global ENDINIT / Safety ENDINIT 的访问窗口需要全局 spinlock。

### 5.4 场景四：嵌套驱动调用

```c
Flash_Program()
{
    ClearGlobalEndinit();

    Dmu_Prepare();      // 里面也 clear/set
    Dmu_Start();        // 里面也 clear/set

    SetGlobalEndinit();
}
```

如果底层函数也封装 ENDINIT，而外层也封装 ENDINIT，就可能出现嵌套不匹配。MCAL 一般通过模块层级设计避免这种“外层开窗，内层关窗”的不清晰结构。

---

## 6. MCAL 推荐的工程化设计

### 6.1 把 ENDINIT 当作“全局临界资源”

建议设计成：

```c
void Mcal_Endinit_Enter(Mcal_EndinitType type)
{
    Mcal_SuspendLocalInterrupts();
    Mcal_GetSpinlock(ENDINIT_LOCK);

    if (type == GLOBAL_ENDINIT)
    {
        Mcal_ClearGlobalEndinit();
    }
    else if (type == SAFETY_ENDINIT)
    {
        Mcal_ClearSafetyEndinit();
    }
    else
    {
        Mcal_ClearCpuEndinit();
    }
}

void Mcal_Endinit_Exit(Mcal_EndinitType type)
{
    if (type == GLOBAL_ENDINIT)
    {
        Mcal_SetGlobalEndinit();
    }
    else if (type == SAFETY_ENDINIT)
    {
        Mcal_SetSafetyEndinit();
    }
    else
    {
        Mcal_SetCpuEndinit();
    }

    Mcal_ReleaseSpinlock(ENDINIT_LOCK);
    Mcal_ResumeLocalInterrupts();
}
```

模块驱动使用：

```c
SchM_Enter_Fls_FLS_EXCLUSIVE_AREA_0();

Mcal_Endinit_Enter(GLOBAL_ENDINIT);

DMU_HF_PROCON.U = value;
(void)DMU_HF_PROCON.U;

Mcal_Endinit_Exit(GLOBAL_ENDINIT);

SchM_Exit_Fls_FLS_EXCLUSIVE_AREA_0();
```

### 6.2 单核 RTOS 最低要求

如果确定单核：

```text
至少 SuspendAllInterrupts / SuspendOSInterrupts
```

因为 ISR 可以打断 Task。

### 6.3 多核 RTOS 最低要求

如果是多核：

```text
本核中断屏蔽 + OS Spinlock
```

只关中断不够，因为其他 core 仍然能写 `SCU_EICON0` / `SCU_SEICON0`。

### 6.4 用户态/非特权任务

如果 OS 开了 memory/protection：

```text
ENDINIT clear/set 应该在 trusted context / supervisor context 执行
```

典型做法：

```text
非特权 Task -> CallTrustedFunction -> 特权函数里 SchM + clear/write/set
```

不要让非特权 Task 直接访问 SCU/DMU/SFR。

---

## 7. clear while 卡死时，MCAL 级诊断应该怎么做？

### 7.1 永远不要永久 while

错误：

```c
while (EICON0.ENDINIT != 0U)
{
}
```

建议：

```c
uint32 timeout = ENDINIT_TIMEOUT_LOOP;

while (((SCU_EICON0.U & EICON0_ENDINIT_MASK) != 0U) && (timeout-- > 0U))
{
    MCAL_NOP();
}

if (timeout == 0U)
{
    Mcal_Endinit_DumpAndTrap();
}
```

### 7.2 dump 信息

至少保存：

```c
g_dbg_eicon0_before;
g_dbg_eicon0_write;
g_dbg_eicon0_after;
g_dbg_eisr;
g_dbg_seicon0;
g_dbg_seisr;
g_dbg_accen00;
g_dbg_accen01;
g_dbg_smu_ag7;
g_dbg_smu_ag8;
g_dbg_core_id;
g_dbg_task_id;
g_dbg_last_clear_pc;
g_dbg_last_set_pc;
g_dbg_clear_cnt;
g_dbg_set_cnt;
```

### 7.3 关键判断表

| 现象 | 可能原因 |
|---|---|
| `EICON0.ENDINIT` 一直 1，`EISR.AE=1` | Password Access / Modify Access 非法 |
| `EICON0.ENDINIT` 一直 1，SMU AG7[20] | 总线访问保护、ACCEN、访问宽度、特权级问题 |
| `EICON0.ENDINIT` 曾短暂为 0 后变 1 | ISR/Task/Core 重入 set 回去了 |
| `EISR.OE=1` | ENDINIT 窗口 timeout overflow |
| 只有某个 core 会卡 | CPU master access / ACCEN / Spinlock 缺失 |
| O0 不复现，O2/O3 复现 | MMIO volatile / bitfield 访问问题 |

---

## 8. 针对你当前问题的重点理解

你当前问题是：

```text
RTOS 运行一段时间后，卡在 ClearGlobalEndinit 的 while 里
```

这说明不是“最基础地址一开始就错”的典型现象，而更像运行期条件变化或并发条件触发。

如果排除 password 被改，那么优先看：

1. 是否有 ISR/Task/Core 在你的 clear 与 while 之间 set 回 ENDINIT；
2. 是否 SchM Exclusive Area 没有包住 clear/write/set 整段；
3. 是否某些测试 case 改了 ACCEN/P0/P1/master 权限；
4. 是否 `WDT_CTRL0.reg` 不是 `volatile uint32` 访问；
5. 是否 bit 定义把 ENDINIT bit1 写成 bit0；
6. 是否 clear/set 函数没有 timeout 和错误 dump。

尤其你是在 `Flash_Im_ProgramDFlash()` 这种运行期 Flash 编程路径里触发，MCAL 风格必须按：

```text
SchM Enter
    ENDINIT clear
    DMU/FLS protected register write
    ENDINIT set
SchM Exit
```

不能只照 iLLD startup/demo 风格裸跑。

---

## 9. 一句话总结

MCAL 的 WDT/ENDINIT clear-set 不是一个单纯的“写密码清 bit，再写密码置 bit”的小技巧，而是一个受以下约束共同支配的系统级临界区：

```text
硬件 password 机制
+ ENDINIT timeout watchdog
+ SFR access protection / ACCEN
+ Supervisor / Trusted Function
+ SchM Exclusive Area
+ OS interrupt lock
+ 多核 spinlock
+ SMU alarm handling
```

iLLD 可以假设调用者在 startup 阶段自己保证上下文安全；MCAL 不能这么假设。MCAL 应该把 clear/write/set 作为一个不可重入的受控访问窗口来设计。🔒

---

## 10. 参考依据

- AURIX TC3xx User Manual，SCU / EICON0 / SEICON0 / EISR / SEISR 章节。
- TC39x-B User Manual Appendix，SCU register overview：`SCU_EICON0` 写访问条件 `U,SV,32,P0`，`SCU_SEICON0` 写访问条件 `U,SV,32,P1`。
- AURIX TC3xx Safety Manual，`SM[HW]:SCU:ENDINIT`、`SM[HW]:SCU:ENDINIT_WATCHDOG`、`SM[HW]:FPI:ENDINIT`、`SM[HW]:FPI:CFG_AS_AP`。
- AURIX TC3xx User Manual，MSC 示例代码中 `SCU_vResetENDINIT()` -> 写 CLC/FDR -> `SCU_vSetENDINIT()` 的典型 protected-register 访问顺序。

