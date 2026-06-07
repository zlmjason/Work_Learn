# ARM Cortex-M 系列核心 — 车规 MCU 验证指南

Cortex-M 系列是车规 MCU 中使用最广泛的处理器核心，从低成本的 M0+ 到高性能的 M85，覆盖车身、动力、底盘、ADAS 等全场景。

## 核心家族对比

| 核心 | 流水线 | MPU | FPU | DSP | TrustZone | 典型车规应用 |
|------|--------|-----|-----|-----|-----------|-------------|
| Cortex-M0+ | 2-stage | No | No | No | No | 车门模块、座椅控制 |
| Cortex-M3 | 3-stage | Yes | No | Yes | No | 车身控制器、BCM |
| Cortex-M4 | 3-stage | Yes | SP | Yes | No | 电机控制、通用车身 |
| Cortex-M7 | 6-stage superscalar | Yes | DP+SP | Yes | No | 动力域、底盘域、网关 |
| Cortex-M33 | 3-stage | Yes | SP | Yes | Yes | 区域控制器、安全网关 |
| Cortex-M55 | 4-stage | Yes | SP | Yes | Yes | AI 推理、传感器融合 |
| Cortex-M85 | 7-stage | Yes | DP+SP | Yes | Yes | 高性能实时控制 |

## 关键架构特性与测试要点

### 1. NVIC (Nested Vectored Interrupt Controller)

**关键参数：**
- 中断数量：16 (M0+) ~ 480 (M7)
- 优先级位数：2 (M0+) ~ 8 (M7/M33)
- 优先级分组：Preemption + Subpriority

**测试要点：**
- [ ] 验证所有中断向量是否正确映射到 NVIC
- [ ] 验证优先级配置（抢占优先级 vs 子优先级）
- [ ] 验证嵌套中断行为（高优先级打断低优先级）
- [ ] 验证中断使能/禁用（`NVIC_EnableIRQ` / `NVIC_DisableIRQ`）
- [ ] 验证中断挂起/清除挂起
- [ ] 验证 SysTick 定时器中断（作为基准时钟）
- [ ] 验证 HardFault/MemManage/BusFault/UsageFault 处理

**常见缺陷：**
- 优先级位数少于 8 位时，高位被截断，导致优先级重排
- 同一抢占优先级的中断不能嵌套，可能导致响应延迟
- 中断处理函数中未清除中断标志，导致连续触发

### 2. MPU (Memory Protection Unit)

**关键参数：**
- Region 数量：8 (M3/M4) ~ 16 (M7/M33)
- 子区域：每个 Region 可划分 8 个子区域
- 属性：XN (Execute Never)、AP (Access Permission)、TEX/C/B/S (缓存策略)

**测试要点：**
- [ ] 验证 MPU Region 配置（基地址、大小、属性）
- [ ] 验证越界访问是否触发 MemManage Fault
- [ ] 验证 XN 区域执行是否触发 MemManage Fault
- [ ] 验证不同 Privilege 级别的访问权限
- [ ] 验证 Sub-Region Disable 功能
- [ ] 验证背景 Region（Region 0 默认属性）

**常见缺陷：**
- Region 大小不是 2 的幂次，导致 MPU 配置失败
- 重叠 Region 的优先级（高 Region 号覆盖低 Region 号）未理解
- 未使能 MPU（`CTRL.ENABLE`），配置无效

### 3. FPU (Floating Point Unit)

**关键参数：**
- SP (Single Precision)：M4, M33
- DP+SP (Double + Single Precision)：M7, M85
- Lazy Stacking：自动保存 FPU 寄存器到栈

**测试要点：**
- [ ] 验证单精度浮点运算精度（IEEE 754 合规）
- [ ] 验证双精度浮点运算精度（仅 M7/M85）
- [ ] 验证 FPU 异常（Invalid Operation、Divide by Zero、Overflow、Underflow）
- [ ] 验证 Lazy Stacking 机制（中断时自动保存 FPU 寄存器）
- [ ] 验证 FPU 上下文切换（RTOS 环境下）
- [ ] 验证 FPU 使能/禁用

**常见缺陷：**
- 未使能 FPU 协处理器访问（CPACR），导致 HardFault
- 中断中未保存 FPU 寄存器，导致上下文破坏
- 浮点运算精度不满足控制算法要求

### 4. DSP 指令集

**关键指令：**
- SIMD：单指令多数据（16-bit × 2 或 8-bit × 4）
- MAC：乘累加（`SMLAL`, `UMLAL`）
- SSAT/USAT：饱和运算

**测试要点：**
- [ ] 验证 SIMD 指令结果正确性
- [ ] 验证 MAC 指令的累加器溢出行为
- [ ] 验证饱和指令的边界值处理
- [ ] 对比 DSP 指令 vs 软件实现的性能差异

### 5. Cache (仅 Cortex-M7)

**关键参数：**
- I-Cache：0~16KB（可配置）
- D-Cache：0~16KB（可配置）
- Cache Line：32 bytes (8 words)
- 替换策略：Pseudo-random

**测试要点：**
- [ ] 验证 Cache 使能/禁用
- [ ] 验证 Cache 命中率（循环代码、数组访问）
- [ ] 验证 Cache 一致性（DMA 访问 SRAM 时的 invalidate/flush）
- [ ] 验证 Cache 维护操作（Clean/Invalidate/Clean+Invalidate）
- [ ] 验证 MPU 对 Cache 策略的控制（TEX/C/B/S）

**常见缺陷：**
- DMA 写 SRAM 后 CPU 读到的数据是 Cache 中的旧值（未 invalidate）
- CPU 写 SRAM 后 DMA 读到的数据在 Cache 中（未 clean）
- Cache 未命中导致实时性不满足要求

### 6. TCM (Tightly Coupled Memory, 仅 M7)

**关键参数：**
- ITCM：0~16MB（指令 TCM）
- DTCM：0~16MB（数据 TCM）
- 访问延迟：单周期（确定性）

**测试要点：**
- [ ] 验证 TCM 地址映射（通过 MPU/ATCM）
- [ ] 验证 TCM 单周期访问（与 SRAM/Flash 对比）
- [ ] 验证 TCM 与 Cache 的优先级（TCM 命中时 Bypass Cache）
- [ ] 验证 TCM 的 ECC（如果支持）

## 车规特殊要求

### 1. 锁步核心（Lockstep）
部分车规 MCU（如 AURIX、某些双核 M7）实现锁步：
- 两个核心执行相同指令流
- 每个周期比较输出
- 不一致时触发安全错误

**测试要点：**
- [ ] 验证锁步比较逻辑（注入单比特错误，验证检测）
- [ ] 验证锁步故障后的安全状态（复位/中断）
- [ ] 验证锁步模式下的性能影响（延迟增加）

### 2. ECC 支持
- SRAM ECC：单比特纠错，双比特检错
- Flash ECC：类似机制

**测试要点：**
- [ ] 验证单比特错误自动纠正（Silent Error Correction）
- [ ] 验证双比特错误触发中断/复位
- [ ] 验证 ECC 错误计数器

## 参考文档
- ARM Cortex-M7 Technical Reference Manual (ARM DDI 0489)
- ARM Cortex-M4 Technical Reference Manual (ARM DDI 0439)
- ARM Cortex-M33 Technical Reference Manual (ARM DDI 0553)
