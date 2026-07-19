---
name: mcu-note-creator
description: Create new automotive MCU knowledge base notes following project conventions. Trigger when the user asks to create a new note, asks where to place a topic, or mentions "new note", "create note", "这个该放哪", "怎么命名". Do NOT use for moving or renaming existing notes (use note-organizer) or for reviewing existing notes against conventions (use doc-review).
metadata:
---

# MCU Note Creator

按本仓库规范创建新的车规 MCU 知识库笔记。覆盖文件命名、目录选择、笔记模板、写作风格。

## 触发条件

用户提到以下任一表达时调用本 skill：

- "创建新笔记"
- "新建一个关于...的笔记"
- "这个主题应该放在哪个目录"
- "这个文件名该怎么命名"
- "帮我写个笔记模板"
- "怎么命名"
- "这个该放哪"

## 快速参考

| 情况 | 操作 |
|------|------|
| 不确定主题归属 | 先问清：Hardware / Middleware / Safety / Tools / Application |
| 不确定文件名 | 查 [`reference.md`](./reference.md) 的命名前缀表 |
| 临时/未整理内容 | 先放入 `00_Inbox_临时收集/` |
| 需要模板 | 使用 9 段式模板（核心问题、结论、背景、关键机制、应用场景、关联笔记、待补充问题、标签、Agent 整理记录） |
| 要删除旧笔记 | 禁止直接删除，先移入 `90_Archive_归档/` |

## 一分钟示例

**用户**："我要新建一篇关于 AURIX TC3xx DMA 通道配置的笔记"

**Claude**：
1. 确定层次：Hardware / System / DMA
2. 目录：`01_Hardware_硬件层/03_System/05_DMAMove/`
3. 文件名：`AURIX_TC3xx_Sys_DMA_Channel_Config.md`
4. 生成 9 段式模板并写入文件

## 文件结构

```
mcu-note-creator/
├── SKILL.md      ← 本文件（入口与触发条件）
├── reference.md  ← 28 条命名规则、目录树、9 段式模板、写作风格
├── gotchas.md    ← 常见错误（空格、中文术语、目录放错等）
└── config.json   ← 模板章节与关键目录
```

## 常见陷阱

- 文件名带空格
- 技术术语未保留英文（如把 SPI 写成中文）
- 把 AUTOSAR 内容放到 Hardware 层
- 直接删除旧笔记而不是归档
- 破坏 Obsidian 双链 `[[...]]`

详见 [`gotchas.md`](./gotchas.md)。

## 详细规范

完整命名规则、目录结构、笔记格式、写作风格见 [`reference.md`](./reference.md)。
