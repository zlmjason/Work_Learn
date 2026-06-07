# LIN Protocol — 验证指南

LIN（Local Interconnect Network）是一种低成本的串行通信协议，主要用于车门、座椅、灯光、雨刷等对成本敏感的节点。

## 协议基础

### 物理层
- 单线总线（12V 电平）
- 波特率：1Kbps ~ 20Kbps（常用 19.2Kbps）
- 最大节点数：16（1 主 + 15 从）
- 最大线缆长度：40m
- 终端电阻：无（主节点上拉电阻 1kΩ）

### 帧格式

| 字段 | 长度 | 说明 |
|------|------|------|
| Break Field | 13+ bit | 帧起始（至少 13 个显性位） |
| Sync Field | 8 bit | 同步字节（0x55） |
| PID | 8 bit | 受保护标识符（6-bit ID + 2-bit 校验） |
 | Data | 1~8 bytes | 数据负载 |
| Checksum | 8 bit | 校验和（Classic/Enhanced） |

### PID 校验
- PID[6:0] = ID[5:0] + P0 + P1
- P0 = ID[0] XOR ID[1] XOR ID[2] XOR ID[4]
- P1 = NOT(ID[1] XOR ID[3] XOR ID[4] XOR ID[5])

## 关键测试要点

### 1. 主节点调度

**调度表（Schedule Table）：**
- 固定周期调度
- 事件触发调度
- 诊断调度（0x3C/0x3D）

**测试要点：**
- [ ] 验证固定周期调度（按配置周期发送帧）
- [ ] 验证事件触发调度（变化时发送，无变化时跳过）
- [ ] 验证调度表切换（正常运行 ↔ 诊断模式）
- [ ] 验证主节点丢失后的从节点超时行为

### 2. 从节点响应

**测试要点：**
- [ ] 验证从节点在接收到 Header 后正确响应 Data
- [ ] 验证从节点响应超时（Header 发送后从节点未响应）
- [ ] 验证从节点睡眠/唤醒（总线空闲 4s 进入睡眠，Break 唤醒）
- [ ] 验证从节点配置（NAD、PID 映射）

### 3. 诊断帧

| ID | 用途 |
|----|------|
| 0x3C | 主节点请求帧（Diagnostic Request） |
| 0x3D | 从节点响应帧（Diagnostic Response） |

**测试要点：**
- [ ] 验证诊断请求帧格式
- [ ] 验证诊断响应帧格式
- [ ] 验证诊断超时（请求后未收到响应）
- [ ] 验证诊断错误处理（NRC 响应）

### 4. 错误检测

| 错误类型 | 检测条件 |
|---------|---------|
| Bit Error | 发送与总线电平不一致 |
| Checksum Error | 校验和不匹配 |
| PID Parity Error | PID 校验位错误 |
| Timeout Error | 响应超时 |
| Framing Error | 停止位错误 |

**测试要点：**
- [ ] 注入 Bit Error，验证检测
- [ ] 注入 Checksum Error，验证检测
- [ ] 注入 PID Parity Error，验证检测
- [ ] 模拟从节点不响应，验证 Timeout

## 常见缺陷

1. **Break 场太短**：主节点发送的 Break 不足 13 个 bit，从节点无法识别
2. **波特率偏差**：主从节点波特率偏差超过 ±2%，导致通信失败
3. **从节点未初始化**：NAD 或 PID 映射未配置，导致从节点不响应
4. **睡眠唤醒冲突**：多个从节点同时发送唤醒信号，总线冲突

## 参考文档
- LIN Specification Package 2.2A
- ISO 17987（LIN 国际标准）
