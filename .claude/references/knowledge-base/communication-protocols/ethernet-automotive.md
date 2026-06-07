# Automotive Ethernet — 验证指南

车载以太网是新一代汽车网络技术，主要用于 ADAS、信息娱乐、OTA、诊断等高带宽应用。

## 协议基础

### 物理层（100BASE-T1 / 1000BASE-T1）
- 单对双绞线（Unshielded Twisted Pair）
- 波特率：100 Mbps / 1 Gbps
- 编码：PAM3（100BASE-T1）/ PAM4（1000BASE-T1）
- 传输距离：最长 15m（车内）
- 连接器：单对非屏蔽（Mini50, MATEnet）

### TSN（Time-Sensitive Networking）

| 标准 | 功能 | 说明 |
|------|------|------|
| IEEE 802.1Qbv | 门控调度 | 时间感知整形器 |
| IEEE 802.1Qbu | 帧抢占 | 高优先级打断低优先级 |
| IEEE 802.1CB | 帧复制和消除 | 冗余传输 |
| IEEE 802.1AS | 时钟同步 | gPTP（通用精确时间协议） |
| IEEE 802.1Qci | 逐流过滤和监管 | 入口控制 |

### SOME/IP（Scalable service-Oriented Middleware over IP）
- 服务发现（Service Discovery）
- 远程过程调用（RPC）
- 事件通知（Event）
- 字段通知（Field）

## 关键测试要点

### 1. 物理层信号

**测试要点：**
- [ ] 验证信号完整性（眼图测试）
- [ ] 验证发射功率
- [ ] 验证回波损耗
- [ ] 验证共模噪声
- [ ] 验证 EMC 特性（CISPR 25）

### 2. MAC 层

**测试要点：**
- [ ] 验证帧格式（前导码、SFD、MAC 地址、类型/长度）
- [ ] 验证 VLAN 标签（802.1Q）
- [ ] 验证帧过滤（单播/多播/广播）
- [ ] 验证 CRC 校验
- [ ] 验证巨型帧（Jumbo Frame）

### 3. TSN 时间感知调度

**测试要点：**
- [ ] 验证门控调度表（GCL）
- [ ] 验证时间窗口精度（±1μs）
- [ ] 验证帧抢占（低优先级帧被打断）
- [ ] 验证时钟同步（gPTP，精度 < 1μs）

### 4. SOME/IP

**测试要点：**
- [ ] 验证服务发现（Offer Service / Find Service）
- [ ] 验证远程过程调用（Request / Response）
- [ ] 验证事件订阅（Subscribe / Notify）
- [ ] 验证字段更新（Getter / Setter / Notifier）
- [ ] 验证 SD 消息周期和超时

## 常见缺陷

1. **时钟不同步**：gPTP 未正确配置，导致 TSN 调度失效
2. **网络拥塞**：未配置 QoS，高优先级帧被低优先级帧阻塞
3. **服务发现失败**：SD 消息被防火墙过滤
4. **信号完整性差**：线缆长度过长或连接器质量差

## 参考文档
- IEEE 802.3bw（100BASE-T1）
- IEEE 802.3bp（1000BASE-T1）
- IEEE 802.1 TSN 标准族
- AUTOSAR SOME/IP Specification
