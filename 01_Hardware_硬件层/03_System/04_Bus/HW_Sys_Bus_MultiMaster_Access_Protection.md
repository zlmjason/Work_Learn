# 多主访问与寄存器写保护（AURIX 通用能力）

> **状态：stub（待写）**。本页只记录已核实的事实和待核清单，正文尚未展开。

## 核心问题

多核 MCU 上，CPU0、CPU1、DMA、调试主机都能写同一个外设寄存器。两个主同时改一处配置时，谁保证写序列不被插队？哪些保护是硬件给的，哪些必须软件自己做？

## 结论

- **已确认的一条**：AURIX 外设提供 **RMW（read-modify-write）原子序列**——读改写之间其他主无法介入该模块；但**模块不提供硬件信号量**，互斥只能靠总线级原子序列或软件协议。原文：“Read-modify-write feature provides an atomic read/write sequence where no other master can access the module in between. Module hardware semaphores are not supported.”（TC3xx UM Part 2 §37 开篇）
- **待核**：ACCEN 访问使能、按主标签（TAG-ID）的写保护、非法访问的总线错误响应。见「关键机制」清单。

## 背景

- 触发：整理 QSPI 学习页时判定，TAG-ID 写保护、原子 RMW、无硬件信号量属于 SoC 通用能力，塞进模块文档会稀释主题，故拆出到本页。
- 适用范围：所有 AURIX 外设，不限 QSPI。
- 时间：2026-10-29 建立。

## 关键机制（待核清单）

| 主题 | 待回答的问题 | 依据状态 |
|---|---|---|
| RMW 原子性 | 哪些访问算一次原子序列？跨几个寄存器？DMA 访问是否同样受保护？ | 已核一句（UM Part 2 §37 开篇），细节待查 |
| 硬件信号量 | “module hardware semaphores are not supported” 的适用范围：全部外设还是特定模块？ | 同上，待扩查 |
| ACCEN 访问使能 | 每个外设的 ACCEN0/1 按位授权，位对应哪个 master？改权限需要什么前置条件？ | 待核：各外设寄存器章节 + Part 1 |
| TAG-ID 写保护 | 是否按 master tag 过滤写操作？范围是整模块还是单寄存器？读是否也受限？ | 待核（QSPI 分片扫描提及，尚未在原文核实，暂按“未证实”处理） |
| 总线错误响应（BE/nBE） | 非法访问是挂起总线、返回错误码，还是静默丢弃？ | 待核：寄存器表访问类型列的 BE 标注 |

## 应用场景

- 多核共享同一 QSPI 实例：一核正在发帧，另一核要改 `ECON`。
- DMA 与 CPU 同时操作同一 FIFO（一方写 TXFIFO、一方读 RXFIFO）。
- 安全核需要阻止非安全核修改安全相关外设配置。
- 调试器在线改写寄存器时，与运行中的软件争用同一配置。

## 关联笔记

- 模块侧的“改配置必须落在静止点”：`AURIX_TC3xx_QSPI_Study_Atlas.html` 第 14 章（生命周期：PAUSE / 复位粒度）。
- 同目录：[AURIX_TC3xx_Sys_Bus_Overview.md](AURIX_TC3xx_Sys_Bus_Overview.md)
- 待写：中断系统的“事件标志 vs 中断请求”两级分离（`03_System/06_Interrupt/`）
- 待写：CLC 时钟门控与时钟源切换的强制间隔（`03_System/01_Clock/`）

## 待补充问题

1. ACCEN 的位与 master 的映射表在哪一章？有没有“一主一外设”的推荐分配表？
2. TAG-ID 写保护是只对写有效，还是读也受限？
3. RMW 原子性在 DMA 突发（burst）传输下是否仍然成立？
4. 无硬件信号量时，多核共用一个 QSPI 的推荐互斥协议是什么（自旋锁放 SRI？还是按核分配实例）？

## 标签

`#AURIX` `#TC3xx` `#总线` `#多主` `#访问控制` `#待写`

## Agent 整理记录

- 2026-10-29：从 QSPI 学习页的剔除项中拆出，建立 stub。仅 §37 开篇一句已核，其余字段标记为待核，未写入推测内容。
