# MCU 中断与 DMA 系统 — 验证指南

中断和 DMA 是 MCU 与外设交互的核心机制。车规 MCU 对中断响应的确定性、DMA 传输的可靠性有严格要求，任何中断丢失或 DMA 错误都可能导致功能安全事件。

## 中断系统

### 1. NVIC（Cortex-M 系列）

**关键参数：**
- 中断数量：16（内建）+ 外部 IRQ（M0+: 32, M3/M4: 240, M7: 480）
- 优先级位数：M0+/M3: 4-bit, M4/M7: 8-bit（但实际实现可能截断）
- 优先级分组：抢占优先级（Preemption）+ 子优先级（Subpriority）

**测试要点：**
- [ ] 验证中断向量表正确映射（VTOR 寄存器）
- [ ] 验证优先级配置（`NVIC_SetPriority`）
- [ ] 验证抢占优先级和子优先级的分组（`NVIC_SetPriorityGrouping`）
- [ ] 验证中断使能/禁用（`NVIC_EnableIRQ` / `NVIC_DisableIRQ`）
- [ ] 验证中断挂起/清除挂起（`NVIC_SetPendingIRQ` / `NVIC_ClearPendingIRQ`）
- [ ] 验证活动状态读取（`NVIC_GetActive`）
- [ ] 验证 SysTick 中断（作为基准时钟源）

**优先级规则（关键）：**
- 数值越小，优先级越高
- 抢占优先级高的中断可以打断抢占优先级低的中断
- 相同抢占优先级的中断不能互相打断（按到达顺序执行）
- 子优先级仅在相同抢占优先级时决定响应顺序

**常见缺陷：**
- 优先级位数被截断（如只实现 3-bit，写 0xFF 实际为 0xE0），导致优先级重排
- 中断处理函数中未清除中断标志，导致连续触发
- 中断优先级分组设置错误，导致抢占行为不符合预期

### 2. 外部中断（EXTI）

**关键参数：**
- 触发方式：上升沿、下降沿、双边沿
- 滤波：可配置消抖时间
- 唤醒：部分 EXTI 可作为低功耗唤醒源

**测试要点：**
- [ ] 验证上升沿触发
- [ ] 验证下降沿触发
- [ ] 验证双边沿触发
- [ ] 验证消抖滤波（快速毛刺不触发）
- [ ] 验证 EXTI 作为低功耗唤醒源
- [ ] 验证多个 EXTI 同时触发的响应

### 3. 故障异常（Fault Handlers）

| 异常 | 触发条件 | 处理要求 |
|------|---------|---------|
| HardFault | 任何未处理的故障 | 必须处理，记录故障信息 |
| MemManage | MPU 违规访问 | 检查地址和访问权限 |
| BusFault | 总线错误（非法地址） | 检查外设是否使能 |
| UsageFault | 未定义指令、非对齐访问 | 检查代码正确性 |
| NMI | 不可屏蔽中断 | 最高优先级，必须处理 |

**测试要点：**
- [ ] 注入 MPU 违规，验证 MemManage Fault
- [ ] 访问未使能的外设，验证 BusFault
- [ ] 执行未定义指令，验证 UsageFault
- [ ] 验证 Fault 寄存器（CFSR、HFSR、MMFAR、BFAR）的记录
- [ ] 验证 NMI 的不可屏蔽性（不能被任何中断打断）

## DMA 系统

### 1. DMA 基本特性

**关键参数：**
- 通道数量：4 ~ 32 通道
- 传输宽度：Byte / Half-Word / Word / Double-Word
- 传输模式：单次 / 循环（Circular）
- 地址模式：固定 / 递增 / 外设到内存 / 内存到内存
- 突发传输（Burst）：4 / 8 / 16 beat

**测试要点：**
- [ ] 验证内存到内存传输（数据正确性）
- [ ] 验证外设到内存传输（ADC 采样数据）
- [ ] 验证内存到外设传输（DAC 输出数据）
- [ ] 验证传输完成中断（TCIF）
- [ ] 验证半传输中断（HTIF，用于双缓冲）
- [ ] 验证传输错误中断（TEIF）
- [ ] 验证循环模式（DMA 自动重载，无限循环）

### 2. DMA 与 Cache 一致性

**关键问题：**
当 CPU 带有 Cache（如 Cortex-M7）时，DMA 访问 SRAM 可能导致数据不一致：
- **DMA 写 SRAM**：CPU Cache 中可能保留旧数据
- **CPU 写 SRAM**：数据可能只在 Cache 中，DMA 读 SRAM 读到旧值

**解决方案：**
```c
// DMA 写 SRAM 前：CPU 先 Clean D-Cache（防止旧数据覆盖 DMA 新数据）
SCB_CleanDCache_by_Addr((uint32_t *)buffer, size);

// DMA 写 SRAM 后：CPU Invalidate D-Cache（防止读到旧数据）
SCB_InvalidateDCache_by_Addr((uint32_t *)buffer, size);

// CPU 写 SRAM 后：DMA 读前 Clean D-Cache
SCB_CleanDCache_by_Addr((uint32_t *)buffer, size);
```

**测试要点：**
- [ ] 验证 DMA 写后 CPU 读的正确性（必须 Invalidate）
- [ ] 验证 CPU 写后 DMA 读的正确性（必须 Clean）
- [ ] 验证 Cache 维护操作的范围（地址对齐到 Cache Line 边界）

**常见缺陷：**
- 未执行 Cache 维护操作，导致数据不一致
- Cache 维护范围未对齐到 Cache Line（32 bytes），导致部分数据未刷新
- 中断中修改 DMA 缓冲区，但未刷新 Cache

### 3. DMA 链表（Linked List）

部分高级 DMA 控制器支持链表传输：
- 多个 DMA 描述符链接
- 自动切换缓冲区（Scatter-Gather）
- 无需 CPU 干预完成复杂传输序列

**测试要点：**
- [ ] 验证链表描述符的链接正确性
- [ ] 验证链表传输的自动切换
- [ ] 验证链表结束后的中断

## 中断与 DMA 的协同

### 典型场景：ADC + DMA
```
ADC 采样完成 → DMA 传输到 SRAM → DMA TCIF 中断 → CPU 处理数据
```

**测试要点：**
- [ ] 验证 ADC 采样频率与 DMA 传输速率的匹配
- [ ] 验证 DMA 缓冲区溢出（CPU 处理速度低于采样速度）
- [ ] 验证双缓冲机制（Ping-Pong Buffer）：
  - Buffer A：DMA 正在写入
  - Buffer B：CPU 正在读取
  - 半传输中断切换 Buffer

### 典型场景：UART + DMA
```
UART 接收数据 → DMA 传输到 Ring Buffer → DMA TCIF 中断 → CPU 解析数据
```

**测试要点：**
- [ ] 验证 UART 波特率与 DMA 传输的匹配
- [ ] 验证 Ring Buffer 的溢出处理
- [ ] 验证 DMA 空闲中断（UART 接收停顿后触发）

## 功能安全要求

### 中断安全
- **中断丢失检测**：监控中断计数器，检测丢失的中断
- **中断风暴保护**：限制中断频率，防止 CPU 被中断淹没
- **ISR 执行时间监控**：WWDG 监控 ISR 执行时间

### DMA 安全
- **DMA 传输校验**：CRC 校验传输数据完整性
- **DMA 地址范围检查**：MPU 限制 DMA 只能访问合法内存
- **DMA 双缓冲冗余**：关键数据使用双缓冲 + 比较

## 参考文档
- ARM Cortex-M7 TRM：NVIC 和 DMA 章节
- ARM Cortex-R52 TRM：GIC 和 DMA 章节
- 各厂商 Reference Manual：NVIC/DMA 章节
- ISO 26262-6：软件级中断和 DMA 的安全要求
