# I2C Protocol — 验证指南

I2C（Inter-Integrated Circuit）是一种低速串行通信协议，使用两根线（SDA + SCL）实现多主多从通信。

## 协议基础

### 信号线
| 信号 | 类型 | 说明 |
|------|------|------|
| SDA | 开漏 | 数据线 |
| SCL | 开漏 | 时钟线 |

- 上拉电阻：通常 2.2kΩ ~ 10kΩ
- 最大节点数：理论 127（7-bit 地址）/ 1023（10-bit 地址）
- 总线电容：≤ 400 pF

### 速率模式
| 模式 | 速率 | 说明 |
|------|------|------|
| Standard | 100 Kbps | 标准模式 |
| Fast | 400 Kbps | 快速模式 |
| Fast+ | 1 Mbps | 快速模式+ |
| High Speed | 3.4 Mbps | 高速模式（需电流源上拉） |

### 帧格式

| 字段 | 长度 | 说明 |
|------|------|------|
| START | 1 bit | SCL 高时 SDA 下降沿 |
| 地址 | 7/10 bit | 从机地址 |
| R/W | 1 bit | 读/写方向 |
| ACK | 1 bit | 应答 |
| Data | 8 bit × N | 数据字节 |
| STOP | 1 bit | SCL 高时 SDA 上升沿 |

## 关键测试要点

### 1. 起始/停止条件

**测试要点：**
- [ ] 验证 START 条件（SCL=1 时 SDA 下降沿）
- [ ] 验证 STOP 条件（SCL=1 时 SDA 上升沿）
- [ ] 验证重复 START（Sr，不发 STOP 直接发新的 START）
- [ ] 验证非法 START/STOP（SCL=0 时 SDA 变化）

### 2. 地址寻址

**测试要点：**
- [ ] 验证 7-bit 地址寻址（0x00 ~ 0x7F）
- [ ] 验证 10-bit 地址寻址（11110 + 2-bit + R/W + 8-bit）
- [ ] 验证广播地址（0x00，General Call）
- [ ] 验证地址不匹配（从机不应答 NACK）

### 3. 读写传输

**测试要点：**
- [ ] 验证单字节写
- [ ] 验证多字节写（页写）
- [ ] 验证单字节读
- [ ] 验证多字节读（连续读，最后字节 NACK）
- [ ] 验证组合传输（写地址 → 重复 START → 读数据）

### 4. 仲裁与同步

**测试要点：**
- [ ] 验证多主机仲裁（SDA 线与逻辑，先发送 0 的获胜）
- [ ] 验证时钟同步（SCL 低电平时间由最长周期决定）
- [ ] 验证从机时钟延展（Slave Clock Stretching）

### 5. 错误检测

| 错误 | 检测条件 |
|------|---------|
| Bus Error | START/STOP 在数据传输中出现 |
| Arbitration Lost | 多主机仲裁失败 |
| ACK Failure | 未收到 ACK |
| Overrun/Underrun | 数据未及时读写 |
| Bus Busy | SDA/SCL 被拉低超时 |

## 常见缺陷

1. **上拉电阻过大**：SDA/SCL 上升沿过慢，导致通信失败
2. **总线电容过大**：超过 400pF，信号畸变
3. **时钟延展超时**：从机拉低 SCL 太久，主节点超时
4. **地址冲突**：两个从机使用相同地址
5. **START 后未发 STOP**：总线一直处于忙状态

## 参考文档
- NXP I2C-bus Specification and User Manual (UM10204)
- Philips I2C Specification v3.0
