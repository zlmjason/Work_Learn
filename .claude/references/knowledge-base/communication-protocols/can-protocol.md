# CAN / CAN FD Protocol — 验证指南

控制器局域网（Controller Area Network）是汽车电子系统中最广泛使用的串行通信协议。CAN FD（Flexible Data-rate）是 CAN 的升级版，支持更高的数据速率和更长的数据帧。

## 协议基础

### CAN 2.0B 帧格式

| 字段 | 长度 | 说明 |
|------|------|------|
| SOF | 1 bit | 帧起始 |
| Arbitration Field | 29 bit | 扩展 ID（IDE=1） |
| Control Field | 6 bit | DLC、RTR、IDE |
| Data Field | 0~8 bytes | 数据负载 |
| CRC Field | 15 bit | 循环冗余校验 |
| ACK Field | 2 bit | 应答 |
| EOF | 7 bit | 帧结束 |

### CAN FD 帧格式差异

| 特性 | CAN 2.0 | CAN FD |
|------|---------|--------|
| 数据段速率 | ≤1 Mbps | ≤8 Mbps（数据段） |
| 数据长度 | 0~8 bytes | 0~64 bytes |
| DLC 编码 | 0~8 | 0~8, 12, 16, 20, 24, 32, 48, 64 |
| CRC 长度 | 15 bit | 17 bit（≤16 bytes）/ 21 bit（>16 bytes） |
| BRS 位 | 无 | 速率切换位 |

## 关键测试要点

### 1. 位时序（Bit Timing）

**参数：**
- 波特率预分频器（BRP）
- 同步段（Sync_Seg）：固定 1 TQ
- 传播段（Prop_Seg）
- 相位缓冲段 1（Phase_Seg1）
- 相位缓冲段 2（Phase_Seg2）
- 同步跳转宽度（SJW）

**测试要点：**
- [ ] 验证不同波特率配置（125K/250K/500K/1M/2M/5M/8M）
- [ ] 验证采样点位置（推荐 75%~87.5%）
- [ ] 验证 SJW 配置（建议 ≤ Phase_Seg1）
- [ ] 验证总线长度与波特率的匹配（长距离需低波特率）

### 2. 过滤与掩码

**接收过滤器：**
- 标准过滤器（11-bit ID）
- 扩展过滤器（29-bit ID）
- 掩码模式（Mask Mode）：ID & Mask == Filter
- 列表模式（List Mode）：精确匹配

**测试要点：**
- [ ] 验证过滤器匹配（符合 filter 的报文被接收）
- [ ] 验证过滤器拒绝（不符合 filter 的报文被丢弃）
- [ ] 验证掩码模式的位操作
- [ ] 验证过滤器优先级（FIFO 0 vs FIFO 1）

### 3. 发送与接收

**测试要点：**
- [ ] 验证标准帧发送（11-bit ID）
- [ ] 验证扩展帧发送（29-bit ID）
- [ ] 验证数据帧（Data Frame）
- [ ] 验证远程帧（Remote Frame）
- [ ] 验证 FIFO 接收（先进先出）
- [ ] 验证优先级发送（ID 小的优先）
- [ ] 验证仲裁丢失后的自动重发

### 4. 错误处理

**错误类型：**
- 位错误（Bit Error）
- 填充错误（Stuff Error）
- CRC 错误（CRC Error）
- 格式错误（Form Error）
- 应答错误（ACK Error）

**测试要点：**
- [ ] 验证错误帧的发送和接收
- [ ] 验证错误计数器（TEC/REC）的递增/递减
- [ ] 验证总线关闭状态（Bus-Off，TEC > 255）
- [ ] 验证从 Bus-Off 恢复（128 次连续隐性位）
- [ ] 验证错误中断（Error Warning / Error Passive / Bus-Off）

### 5. CAN FD 特有测试

**测试要点：**
- [ ] 验证 BRS（Bit Rate Switch）功能（仲裁段 vs 数据段速率切换）
- [ ] 验证 ESI（Error State Indicator）位
- [ ] 验证 DLC > 8 时的数据长度（12/16/20/24/32/48/64 bytes）
- [ ] 验证 CAN FD 与 CAN 2.0 节点的混网通信
- [ ] 验证 CRC  stuff-bit 计数

## 常见缺陷

1. **采样点配置不当**：导致高波特率下通信不稳定
2. **终端电阻缺失**：120Ω 终端电阻未接或阻值不对，导致信号反射
3. **过滤器配置错误**：掩码位设置错误，导致接收不到目标报文
4. **FIFO 溢出**：接收速度低于发送速度，导致报文丢失
5. **Bus-Off 恢复**：未处理 Bus-Off 中断，模块一直停留在错误状态

## 参考文档
- ISO 11898-1:2015 — CAN 数据链路层和物理层信号
- ISO 11898-2:2016 — CAN 高速物理层
- Bosch CAN Specification Version 2.0
- CAN FD Protocol Specification (Bosch)
