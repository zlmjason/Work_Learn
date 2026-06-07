# UDS Protocol — 验证指南

UDS（Unified Diagnostic Services，ISO 14229）是汽车诊断的标准协议，基于 CAN/LIN/Ethernet 传输，提供故障诊断、刷写、数据读写等功能。

## 协议基础

### 诊断会话

| 会话 | ID | 说明 |
|------|-----|------|
| Default Session | 0x01 | 默认会话 |
| Programming Session | 0x02 | 编程会话（刷写） |
| Extended Diagnostic Session | 0x03 | 扩展诊断会话 |
| Safety System Diagnostic Session | 0x04 | 安全系统诊断 |

### 安全访问

| 级别 | 说明 |
|------|------|
| Level 1 | 标定数据访问 |
| Level 3 | 刷写访问 |
| Level 5+ | OEM 自定义 |

**Seed-Key 机制：**
1. 请求 Seed（随机数）
2. 计算 Key（基于 Seed 和算法）
3. 发送 Key 解锁

### 常用服务

| SID | 服务 | 说明 |
|-----|------|------|
| 0x10 | Diagnostic Session Control | 会话控制 |
| 0x11 | ECU Reset | ECU 复位 |
| 0x14 | Clear DTC | 清除故障码 |
| 0x19 | Read DTC | 读取故障码 |
| 0x22 | Read Data By Identifier | 读取 DID |
| 0x2E | Write Data By Identifier | 写入 DID |
| 0x27 | Security Access | 安全访问 |
| 0x28 | Communication Control | 通信控制 |
| 0x31 | Routine Control | 例行程序控制 |
| 0x34 | Request Download | 请求下载 |
| 0x36 | Transfer Data | 传输数据 |
| 0x37 | Request Transfer Exit | 请求传输退出 |
| 0x3E | Tester Present | 保持会话 |
| 0x85 | Control DTC Setting | 控制 DTC 设置 |

### 否定响应码（NRC）

| NRC | 说明 |
|-----|------|
| 0x10 | General Reject |
| 0x11 | Service Not Supported |
| 0x12 | Sub-function Not Supported |
| 0x13 | Incorrect Message Length |
| 0x22 | Conditions Not Correct |
| 0x24 | Request Sequence Error |
| 0x31 | Request Out Of Range |
| 0x33 | Security Access Denied |
| 0x35 | Invalid Key |
| 0x36 | Exceed Number Of Attempts |
| 0x37 | Required Time Delay Not Expired |
| 0x78 | Response Pending |
| 0x7E | Sub-function Not Supported In Active Session |
| 0x7F | Service Not Supported In Active Session |

## 关键测试要点

### 1. 会话控制

**测试要点：**
- [ ] 验证 Default Session 进入
- [ ] 验证 Extended Session 进入
- [ ] 验证 Programming Session 进入
- [ ] 验证会话超时（S3 超时，默认 5s）
- [ ] 验证 Tester Present（0x3E）保持会话
- [ ] 验证会话切换（Default → Extended → Programming）
- [ ] 验证不支持会话的否定响应（NRC 0x7E/0x7F）

### 2. 安全访问

**测试要点：**
- [ ] 验证 Seed 请求
- [ ] 验证 Key 计算和发送
- [ ] 验证正确 Key 解锁成功
- [ ] 验证错误 Key 解锁失败（NRC 0x35）
- [ ] 验证连续错误尝试锁定（NRC 0x36）
- [ ] 验证延时解锁（NRC 0x37）
- [ ] 验证未解锁时访问受保护服务的否定响应（NRC 0x33）

### 3. DTC 管理

**测试要点：**
- [ ] 验证 DTC 读取（0x19，按状态掩码）
- [ ] 验证 DTC 清除（0x14）
- [ ] 验证 DTC 状态字节（Test Failed / Confirmed / Pending...）
- [ ] 验证快照数据（Snapshot / Freeze Frame）
- [ ] 验证扩展数据（Extended Data）

### 4. 数据读写（DID）

**测试要点：**
- [ ] 验证 DID 读取（0x22）
- [ ] 验证 DID 写入（0x2E）
- [ ] 验证只读 DID 写入失败
- [ ] 验证 DID 范围检查（NRC 0x31）
- [ ] 验证 DID 数据长度检查（NRC 0x13）

### 5. 刷写流程

**标准刷写流程：**
```
1. 进入 Extended Session (0x10 0x03)
2. 控制 DTC 设置 (0x85 0x02)
3. 控制通信 (0x28 0x03)
4. 进入 Programming Session (0x10 0x02)
5. 安全访问解锁 (0x27)
6. 请求下载 (0x34)
7. 传输数据 (0x36) × N
8. 请求传输退出 (0x37)
9. 校验（Routine Control 0x31）
10. 软件复位 (0x11 0x01)
```

**测试要点：**
- [ ] 验证完整刷写流程
- [ ] 验证擦除（Erase）
- [ ] 验证数据块大小检查
- [ ] 验证地址范围检查
- [ ] 验证 CRC 校验
- [ ] 验证刷写中断恢复（断点续传）
- [ ] 验证刷写失败回滚

### 6. 否定响应测试

**测试要点：**
- [ ] 验证所有服务的 NRC 0x11（不支持的服务）
- [ ] 验证所有子功能的 NRC 0x12（不支持的子功能）
- [ ] 验证消息长度错误的 NRC 0x13
- [ ] 验证条件不满足的 NRC 0x22（如车速 > 0 时禁止刷写）
- [ ] 验证请求序列错误的 NRC 0x24

## 常见缺陷

1. **会话超时**：未发送 Tester Present，会话自动回到 Default
2. **安全访问未解锁**：尝试访问受保护服务被拒绝
3. **刷写时序错误**：未按标准流程操作，导致刷写失败
4. **DTC 未清除**：清除 DTC 后未验证，故障仍然存在
5. **否定响应处理不当**：NRC 0x78（Response Pending）未正确处理

## 参考文档
- ISO 14229-1:2020 — UDS 协议规范
- ISO 15765-2 — CAN 上的诊断传输（TP）
- ISO 13400 — DoIP（Diagnostic over IP）
