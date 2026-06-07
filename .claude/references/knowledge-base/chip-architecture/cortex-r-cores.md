# ARM Cortex-R 系列核心 — 车规 MCU 验证指南

Cortex-R 系列是面向实时应用的高性能处理器核心，相比 Cortex-M 具有更强的确定性、更高的主频、更丰富的存储子系统，广泛应用于汽车动力域、底盘域、ADAS 等对实时性和可靠性要求极高的场景。

## 核心家族对比

| 核心 | 流水线 | 双核 | FPU | MPU | L1 Cache | 典型车规应用 |
|------|--------|------|-----|-----|----------|-------------|
| Cortex-R4F | 8-stage | Split-Lock | SP VFPv3 | Yes | I-Cache 4~64KB | 通用实时控制 |
| Cortex-R5F | 8-stage | Split-Lock | SP+DP VFPv3 | Yes | I/D-Cache 4~64KB | 车身、底盘 |
| Cortex-R7 | 11-stage superscalar | Yes | SP+DP VFPv3 | Yes | I/D-Cache 4~64KB | 网关、ADAS |
| Cortex-R8 | 11-stage superscalar | Yes | SP+DP VFPv3 | Yes | I/D-Cache 4~64KB | 高性能实时 |
| Cortex-R52 | 8-stage | Yes (up to 4) | SP VFPv3 | Yes | I-Cache 4~64KB | 功能安全关键 |
| Cortex-R82 | 8-stage | Yes (up to 4) | SP+DP | Yes | I/D-Cache 4~64KB | 下一代安全应用 |

## 关键架构特性与测试要点

### 1. Split-Lock 模式（R4F/R5F/R52）

Split-Lock 是 Cortex-R 的核心安全特性，支持两种模式：
- **Split 模式**：两个核心独立运行，性能最大化
- **Lock 模式**：两个核心执行相同指令流，输出比较，安全性最大化

**测试要点：**
- [ ] 验证 Split 模式下双核独立运行
- [ ] 验证 Lock 模式下输出比较逻辑
- [ ] 验证 Split↔Lock 动态切换（R52 支持运行时切换）
- [ ] 验证 Lock 模式下注入单比特错误的检测
- [ ] 验证 Lock 模式下故障后的安全响应（中断/复位）
- [ ] 验证 Lock 模式下的性能下降（通常 30~50%）

**常见缺陷：**
- Split↔Lock 切换时未保存/恢复上下文，导致数据丢失
- Lock 模式下对非确定性事件（中断时机）的处理不一致
- 两个核心的时钟偏移导致比较失败

### 2. 更强大的 MPU

Cortex-R 的 MPU 比 Cortex-M 更灵活：
- Region 数量：12 (R4) ~ 24 (R52)
- 重叠 Region：支持复杂的内存映射
- 背景 Region：默认属性配置

**测试要点：**
- [ ] 验证 12~24 个 Region 的独立配置
- [ ] 验证重叠 Region 的优先级（高 Region 号覆盖低 Region 号）
- [ ] 验证背景 Region 的默认访问权限
- [ ] 验证 MPU 对 TCM/Cache/外设的覆盖

### 3. 确定性响应

Cortex-R 提供确定性中断响应：
- 固定中断延迟（通常 12~24 个时钟周期）
- 无缓存未命中的不确定性（TCM 或 Cache Lock）

**测试要点：**
- [ ] 测量中断响应时间（从中断信号到 ISR 第一条指令）
- [ ] 验证不同中断优先级下的响应时间一致性
- [ ] 验证 Cache Lock 功能（关键代码锁定在 Cache 中）
- [ ] 验证 TCM 访问的确定性（单周期延迟）

### 4. TCM（Tightly Coupled Memory）

Cortex-R 提供多个 TCM Bank：
- ATCM：指令 TCM，0~16MB
- BTCM：数据 TCM Bank 0，0~16MB
- BTCM：数据 TCM Bank 1，0~16MB

**测试要点：**
- [ ] 验证 ATCM/BTCM 的独立访问
- [ ] 验证 TCM 的 ECC（单比特纠错/双比特检错）
- [ ] 验证 TCM 与 Cache 的协同工作
- [ ] 验证 DMA 访问 TCM 的正确性

### 5. 向量浮点单元（VFPv3）

Cortex-R 集成更强大的 VFP：
- 单精度（SP）和双精度（DP）运算
- 向量运算（SIMD）
- 硬件除法和平方根

**测试要点：**
- [ ] 验证单精度/双精度运算精度
- [ ] 验证 VFP 异常处理
- [ ] 验证 VFP 上下文保存/恢复（中断/任务切换）
- [ ] 对比 VFP 与软件浮点的性能差异

## 车规特殊要求

### 1. 功能安全（以 Cortex-R52 为例）

R52 专为功能安全设计：
- 最多 4 个核心，支持多种配置（单核、双核 Lock、四核 Split）
- 硬件虚拟化支持（Hypervisor）
- 独立的 MPU 和 TrustZone 扩展

**测试要点：**
- [ ] 验证多核配置的正确性（1+1 Lock、2+2 Split 等）
- [ ] 验证硬件虚拟化的上下文隔离
- [ ] 验证 TrustZone 的安全/非安全世界切换
- [ ] 验证安全监控器（Safety Monitor）的错误检测

### 2. ECC 和 BIST

- **SRAM ECC**：单比特纠错，双比特检错
- **TCM ECC**：类似机制
- **MBIST**：上电内存自检
- **LBIST**：上电逻辑自检

**测试要点：**
- [ ] 验证 MBIST 覆盖所有 SRAM Bank
- [ ] 验证 LBIST 覆盖关键逻辑路径
- [ ] 验证 ECC 错误注入（通过测试接口）
- [ ] 验证 BIST 故障后的安全状态

## 典型车规 MCU 案例

### TI TMS570LC4357
- 核心：双核 Cortex-R5F（Lockstep）
- 主频：300MHz
- Flash：4MB，SRAM：512KB
- 外设：CAN FD × 4、LIN × 2、FlexRay × 2、ADC × 2
- 安全：ECC、MPU、看门狗、时钟监控
- 应用：电动助力转向（EPS）、电子驻车制动（EPB）

### NXP S32G2
- 核心：8× Cortex-A53 + 4× Cortex-M7
- 附加：Cortex-M7 用于实时控制
- 安全：ASIL-D 支持
- 应用：中央网关、区域控制器

## 参考文档
- ARM Cortex-R52 Technical Reference Manual (ARM DDI 0571)
- ARM Cortex-R5 Technical Reference Manual (ARM DDI 0460)
- TI TMS570LC4357 TRM (SPNU563)
