# .claude/ 目录说明

本目录为 `MarkDown_Learn` 知识库项目的辅助资料区，供 Claude Code 在回答车规 MCU 相关问题时按需参考。

## 当前内容

### references/knowledge-base/ — 知识库参考资料

车规 MCU 领域的结构化参考资料，按主题分类：

| 目录 | 内容 | 文件数 |
|------|------|--------|
| `chip-architecture/` | MCU 架构（核心、存储器、时钟复位、中断 DMA、多核、电源管理、调试跟踪） | 9 |
| `communication-protocols/` | 车载通信协议（CAN、LIN、FlexRay、Ethernet、SPI、I2C、UART、UDS） | 8 |
| `diagnostics-source/` | 诊断知识（UDS/ISO14229、DTC、DoIP、OBD-II、ODX、刷写、诊断工具） | 8 |
| `peripheral-test-points/` | 外设测试要点（GPIO、ADC、DAC、DMA、Timer/PWM、RTC、WDG、CRC、Crypto） | 10 |
| `safety-standards-source/` | 功能安全（ISO 26262、HARA、FMEA/FTA、安全机制、软件安全需求、验证确认） | 7 |
| `test-methodology/` | 测试方法论（需求分解） | 1 |
| `zonal-source/` | 区域架构（区域控制器、车载以太网、SOA、网络安全） | 8 |

**使用方式**：Claude Code 在处理相关主题任务时，可读取对应目录下的文件作为背景知识补充。

### skills/mineru-pdf-parser/ — PDF 转 Markdown 技能

基于 MinerU 云端 API 的文档解析工具，支持将 PDF/Word/PPT/Excel/图片转换为结构化 Markdown。

- 触发条件：用户提到"PDF转Markdown"、"解析文档"、"提取文档内容"等
- 详细用法见 `skills/mineru-pdf-parser/SKILL.md`

## 与根目录的关系

| 根目录 | 用途 |
|--------|------|
| `CLAUDE.md` | 项目级工作指南（文档规范、目录结构、工具说明） |
| `AGENTS.md` | 代理指令（技能工作流、持续改进机制） |
| `.learnings/` | 持续改进日志 |
| `skills/` | 项目技能（PDF 处理、内容提取、持续改进） |

本目录（`.claude/`）仅保留**参考资料**和**PDF解析技能**，不作为项目的主要配置入口。
