# MCU 存储架构 — 验证指南

车规 MCU 的存储子系统直接影响功能安全、实时性和可靠性。存储架构包括 Flash（NVM）、SRAM、TCM、Cache、OTP 等，每种存储介质有不同的特性和测试要求。

## 存储类型与特性

### 1. Flash（Non-Volatile Memory）

**关键参数：**
- 容量：128KB ~ 16MB（车规 MCU 典型范围）
- 位宽：32-bit / 128-bit（按 word/quad-word 读取）
- 擦写周期：10K ~ 100K 次
- 数据保持：10 ~ 20 年（@125°C）
- 读取等待周期：0 ~ 5 个（取决于主频和 Flash 速度）
- ECC：通常每 64-bit 数据带 8-bit ECC

**测试要点：**
- [ ] 验证 Flash 读取速度（0-wait / 1-wait / 2-wait 模式）
- [ ] 验证 Flash 擦除时间（Sector / Block / Mass Erase）
- [ ] 验证 Flash 编程时间（Word / Double-Word / Page）
- [ ] 验证 Flash ECC（单比特纠错、双比特检错）
- [ ] 验证 Flash 保护机制（读保护、写保护、Sector 保护）
- [ ] 验证 Flash 模拟 EEPROM 功能（如果支持）
- [ ] 验证 Flash 预取缓冲区（Prefetch Buffer）性能

**常见缺陷：**
- 主频提升后未增加 Flash 等待周期，导致取指令错误
- Flash 编程时未擦除，导致数据不可靠
- Flash 擦写过程中发生复位，导致数据损坏
- ECC 双比特错误未处理，导致系统崩溃

### 2. SRAM

**关键参数：**
- 容量：16KB ~ 2MB
- 位宽：32-bit / 64-bit
- ECC：每 32-bit 带 7-bit ECC（Hamming Code）或每 64-bit 带 8-bit ECC
- 分区：可配置为 Code SRAM / Data SRAM / TCM

**测试要点：**
- [ ] 验证 SRAM 读写正确性（March 算法：March C-, March LR）
- [ ] 验证 SRAM ECC（单比特纠错、双比特检错）
- [ ] 验证 SRAM 分区（不同 Bank 的独立访问）
- [ ] 验证 SRAM 低功耗模式（Retention / Power Down）
- [ ] 验证 SRAM 的位翻转（Bit Flip）恢复能力
- [ ] 验证 DMA 访问 SRAM 的正确性（与 CPU 并发访问）

**常见缺陷：**
- SRAM 初始化不完整，残留随机值导致未初始化变量错误
- DMA 与 CPU 并发访问同一地址，数据竞争
- ECC 错误中断未使能，静默数据损坏

### 3. TCM（Tightly Coupled Memory）

**关键参数：**
- ITCM：指令 TCM，0 ~ 16MB
- DTCM：数据 TCM，0 ~ 16MB
- 访问延迟：单周期（确定性）
- 无 Cache 不确定性

**测试要点：**
- [ ] 验证 TCM 地址映射（通过 MPU/ATCM 配置）
- [ ] 验证 TCM 单周期访问（与 SRAM/Flash 对比时序）
- [ ] 验证 TCM 与 Cache 的优先级（TCM 命中时 Bypass Cache）
- [ ] 验证 TCM 的 ECC（如果支持）
- [ ] 验证 DMA 访问 TCM（某些架构不支持 DMA 访问 TCM）

**常见缺陷：**
- 代码链接到 TCM 但 TCM 未初始化，导致取指令失败
- TCM 大小配置错误，导致访问越界
- DMA 访问 TCM 导致总线错误（某些架构限制）

### 4. Cache（仅高性能核心如 Cortex-M7、Cortex-R）

**关键参数：**
- I-Cache / D-Cache：4KB ~ 64KB
- Cache Line：32 bytes（8 words）或 64 bytes
- 替换策略：Pseudo-random 或 Round-robin
- Write Policy：Write-through 或 Write-back

**测试要点：**
- [ ] 验证 Cache 使能/禁用（`SCB->CCR`）
- [ ] 验证 Cache 命中率（循环代码、数组访问模式）
- [ ] 验证 Cache 维护操作：
  - Clean：将 D-Cache 脏数据写回 SRAM
  - Invalidate：丢弃 Cache 内容，下次从 SRAM 重新加载
  - Clean + Invalidate：先写回再丢弃
- [ ] 验证 DMA 访问 SRAM 时的 Cache 一致性：
  - DMA 写 SRAM 前：CPU 需 Clean D-Cache（防止旧数据覆盖 DMA 新数据）
  - DMA 写 SRAM 后：CPU 需 Invalidate D-Cache（防止读到旧数据）
- [ ] 验证 MPU 对 Cache 策略的控制（TEX/C/B/S 位）

**常见缺陷：**
- DMA 写 SRAM 后 CPU 读到 Cache 旧值（未 Invalidate）
- CPU 写 SRAM 后 DMA 读到 Cache 值（未 Clean）
- Cache 维护操作顺序错误，导致数据不一致
- 中断处理函数修改全局变量，但 Cache 未刷新

### 5. OTP（One-Time Programmable）

**关键参数：**
- 容量：1KB ~ 4KB
- 用途：芯片唯一标识（UID）、安全密钥、启动配置
- 写入：一次性，不可擦除

**测试要点：**
- [ ] 验证 OTP 读取正确性
- [ ] 验证 OTP 写入后不可修改
- [ ] 验证 OTP ECC（如果支持）
- [ ] 验证 OTP 的读保护机制

## 存储安全机制

### ECC（Error Correcting Code）

**Hamming Code 实现：**
- 32-bit 数据 + 7-bit ECC：可纠正单比特错误，检测双比特错误
- 64-bit 数据 + 8-bit ECC：同上

**测试要点：**
- [ ] 注入单比特错误（通过测试接口或位翻转），验证自动纠正
- [ ] 注入双比特错误，验证检测并触发中断/复位
- [ ] 验证 ECC 错误计数器（记录错误次数）
- [ ] 验证 ECC 错误地址记录（定位故障位置）

### BIST（Built-In Self Test）

**MBIST（Memory BIST）：**
- 上电时自动运行
- 测试算法：March C-, March LR, Checkerboard
- 覆盖所有 SRAM Bank

**LBIST（Logic BIST）：**
- 上电时自动运行
- 测试关键逻辑路径
- 生成签名（Signature）与期望值比较

**测试要点：**
- [ ] 验证 MBIST 覆盖所有 SRAM Bank
- [ ] 验证 LBIST 覆盖关键逻辑路径
- [ ] 验证 BIST 故障后的安全状态（复位/进入安全模式）
- [ ] 验证 BIST 运行时间（影响启动时间）

## 参考文档
- ARM Cortex-M7 TRM：Cache 和 TCM 章节
- ARM Cortex-R52 TRM：TCM 和 ECC 章节
- ISO 26262-5：硬件开发中的存储器安全要求
- 各厂商 Reference Manual 的 Memory 章节
