# SafeSPI Evaluator — 详细参考

本文件是 `safespi-evaluator` Skill 的详细评估框架。完整实例见：

`01_Hardware_硬件层/05_Peripherals/01_Communication/01_SPI/HW_Periph_Comm_SafeSPI_Origin_Background_13K_MCU_Support_Analysis.md`

---

## 1. 评估原则

评估不是逐字翻译规范，而是回答一个问题：**MCU 的 SPI 控制器 + 软件实现能否满足 SafeSPI Rev 2.0 的要求？**

每层评估使用统一标记：

| 标记 | 含义 |
|------|------|
| `[✅]` | 明确支持 |
| `[⚠️]` | 部分支持，需额外软件处理或验证 |
| `[❌]` | 不支持 |
| `[?]` | 信息不足，需查手册 |

---

## 2. 5 层评估框架

### Layer 1：物理/IO 层

**关注点**：
- 工作电压范围（如 VIO 3.0–3.6V）
- 输入/输出高低电平阈值（VIH、VIL、VOH、VOL）
- 引脚容性负载、迟滞、上拉/下拉
- MISO 高阻态漏电流
- 驱动能力

**评估动作**：
- 查阅 MCU Pad Datasheet
- 与 SafeSPI 电气参数表逐项对比

---

### Layer 2：SPI 传输层

**关注点**：
- SPI 模式：CPOL=0，CPHA=0 或 CPHA=1
- 帧大小：32-bit、48-bit
- 波特率范围（SafeSPI 典型 0.095–10.5 MHz）
- 时序参数：
  - MISO valid after CS
  - MISO valid after SCK
  - MISO disable lag
  - SCK 周期、占空比
- MSB first

**评估动作**：
- 查阅 SPI 控制器时序表
- 确认支持可编程帧大小
- 确认波特率可配置到目标范围

---

### Layer 3：SafeSPI 逻辑层

**关注点**：
- 32-bit 帧格式：
  - TA9:0 / SA9:0（地址）
  - D bit
  - S1:0 / S0 状态位
  - 3-bit CRC（polynomial 0x5）
- 48-bit 帧格式：
  - TA9:0 / SA9:0
  - DATAO19:0
  - D bit、CE、IDS、S1:0、DCnt
  - 8-bit CRC（polynomial 0x97）
- in-frame 和 out-of-frame 支持

**评估动作**：
- 确认 SPI 控制器能否发送/接收 32-bit 和 48-bit 帧
- 确认 CRC 可由硬件计算或必须由软件实现
- 确认帧字段可灵活映射到寄存器/数据缓冲

---

### Layer 4：协议行为

**关注点**：
- 同帧响应（in-frame response）
- 下一帧响应（out-of-frame response）
- 多从机地址匹配（TA9/TA9:8）
- 错误指示：
  - 状态位
  - MISO 高阻态
  - CE bit
  - 故意 CRC 取反
- 故障管理：超时、重试、看门狗

**评估动作**：
- 确认 SPI 控制器支持从机模式地址过滤
- 确认可实现 in-frame / out-of-frame 时序
- 评估软件实现错误管理的复杂度

---

### Layer 5：监听/监控

**关注点**：
- 被动监听总线（不驱动 MOSI/MISO）
- 同时采样 MOSI + MISO
- 外部 SCK 作为采样时钟
- 10 MHz 下无丢帧重建
- 独立 CRC 校验

**评估动作**：
- 确认 SPI 控制器有无监听/只收模式
- 确认 GPIO + DMA 能否实现外部时钟同步采样
- 评估监控通道的实时性

---

## 3. 7 类需求映射

将 SafeSPI 要求映射到 7 个检查维度：

| 类别 | 关键问题 |
|------|----------|
| Physical/IO | 电气参数是否匹配？ |
| Timing | 时序是否满足 SafeSPI 边界？ |
| SPI Transfer Mode | 是否支持所需 CPOL/CPHA、帧大小、波特率？ |
| Logical Layer/Frame Format | 是否支持 32/48-bit 帧和 CRC？ |
| Protocol Behavior | 是否支持 in/out-of-frame、多从机、错误指示？ |
| Fault Management/Diagnostics | 超时、重试、看门狗、CRC 错误如何处理？ |
| Monitor/Listener | 能否被动监听并重建帧？ |

---

## 4. 输出模板

评估完成后，建议输出以下结构：

```markdown
# {MCU} SafeSPI 支持性评估

## 评估结论
[一句话结论]

## 5 层检查表

| 层次 | 状态 | 说明 |
|------|------|------|
| 物理/IO 层 | [✅/⚠️/❌/?] | ... |
| SPI 传输层 | [✅/⚠️/❌/?] | ... |
| SafeSPI 逻辑层 | [✅/⚠️/❌/?] | ... |
| 协议行为 | [✅/⚠️/❌/?] | ... |
| 监听/监控 | [✅/⚠️/❌/?] | ... |

## 关键风险
1. ...
2. ...

## 建议
- ...

## 参考
- MCU 手册章节
- SafeSPI Rev 2.0 规范章节
```

---

## 5. 软件架构建议

若硬件不完全支持 SafeSPI，可考虑软件补偿：

- **CRC**：软件查表法或调用硬件 CRC 单元
- **帧组装/解析**：位操作 + DMA 缓冲
- **in/out-of-frame**：GPIO 中断 + 定时器控制 CS
- **监听模式**：SPI 从机模式或 GPIO + DMA 捕获

评估时需明确：**哪些由硬件完成，哪些必须由软件实现，软件实现的实时性风险。**
