---
name: safespi-evaluator
description: Evaluate MCU SPI controller support for SafeSPI Rev 2.0 using a 5-layer framework. Trigger when the user asks "评估 SafeSPI", "这个 MCU 支持 SafeSPI 吗", "SPI 控制器符合 SafeSPI 吗", "SafeSPI 兼容性分析", or needs to check SafeSPI support.
metadata:
---

# SafeSPI Evaluator

按 SafeSPI Rev 2.0 规范，从 5 个层次评估 MCU SPI 控制器是否满足要求。

## 触发条件

用户提到以下任一表达时调用本 skill：

- "评估 SafeSPI"
- "这个 MCU 支持 SafeSPI 吗"
- "SPI 控制器符合 SafeSPI 吗"
- "SafeSPI 兼容性分析"
- "SafeSPI 5 层分析"
- 需要判断 MCU SPI 控制器能否实现 SafeSPI

## 快速参考

| 层次 | 关注点 |
|------|--------|
| 1. 物理/IO 层 | 电气参数、引脚映射、驱动能力 |
| 2. SPI 传输层 | CPOL/CPHA、帧大小、波特率、时序 |
| 3. SafeSPI 逻辑层 | 帧格式、CRC、地址/状态位 |
| 4. 协议行为 | in-frame / out-of-frame、故障管理 |
| 5. 监听/监控 | 被动监听、错误注入、CRC 校验 |

## 一分钟示例

**用户**："评估一下 AURIX TC3xx 的 QSPI 是否支持 SafeSPI"

**Claude**：
1. 收集 MCU SPI/QSPI 手册的电气参数和时序表
2. 逐层对照 SafeSPI Rev 2.0 要求
3. 输出检查表：`[✅]` 满足、`[⚠️]` 需确认、`[❌]` 不满足、`[?]` 信息不足
4. 给出结论和改进建议

## 文件结构

```
safespi-evaluator/
├── SKILL.md      ← 本文件（入口与触发条件）
├── reference.md  ← 5 层框架详解、7 类需求映射、检查表格式
├── gotchas.md    ← 常见陷阱（普通 SPI 混淆、CRC、in/out-of-frame 等）
└── config.json   ← 完整参考笔记路径与评估层定义
```

## 常见陷阱

- 把普通 SPI 时序当作 SafeSPI 充分条件
- 忽略 CRC 硬件支持
- 混淆 in-frame 与 out-of-frame 响应
- 漏掉监听/监控模式要求

详见 [`gotchas.md`](./gotchas.md)。

## 详细评估框架

5 层框架、7 类需求映射、检查表模板见 [`reference.md`](./reference.md)。

## 完整参考

本项目已有完整 SafeSPI 分析实例：

`01_Hardware_硬件层/05_Peripherals/01_Communication/01_SPI/HW_Periph_Comm_SafeSPI_Origin_Background_13K_MCU_Support_Analysis.md`
