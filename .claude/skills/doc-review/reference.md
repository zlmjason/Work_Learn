# Doc Review — 详细参考

本文件是 `doc-review` Skill 的详细检查规则说明。

---

## 检查类别

### 1. 文件名检查

**规则**：
- 禁止空格
- 使用下划线 `_` 分隔
- 英文缩写统一大写：`SPI`、`CAN`、`ADC`、`GPIO`、`MPU`
- 必须包含对应层次的前缀

**状态判定**：
- `pass`：无空格，有合法前缀
- `warn`：有空格但其他正常；或前缀疑似不正确
- `fail`：存在严重命名问题

**常用前缀示例**：

| 层次 | 前缀 |
|------|------|
| Hardware / Core / AURIX | `AURIX_TC3xx_Core_` |
| Hardware / Memory | `HW_Mem_` |
| Hardware / System | `HW_Sys_` |
| Hardware / Peripherals / Comm | `HW_Periph_Comm_` |
| Hardware / Multicore | `HW_MC_` |
| AUTOSAR / Communication | `AUTOSAR_Comm_` |
| AUTOSAR / System | `AUTOSAR_Sys_` |
| FreeRTOS / Kernel | `FreeRTOS_Kernel_` |
| Safety | `Safety_` |
| Tools | `Tools_` |

---

### 2. 标题结构检查

**规则**：
- 文件必须以 `# 标题` 开头
- `#` 仅用于文档标题
- `##` 用于章节
- `###` 用于小节

**状态判定**：
- `pass`：有 H1 标题，层级正确
- `warn`：有 H1 但后续层级跳跃
- `fail`：缺少 H1 或标题层级严重错误

---

### 3. 必要章节检查

推荐 9 段式模板中的关键章节：

```markdown
## 核心问题
## 结论
## 背景
## 关键机制
## 应用场景
## 关联笔记
## 待补充问题
## 标签
## Agent 整理记录
```

**状态判定**：
- `pass`：包含核心问题、结论、关键机制
- `warn`：缺少部分章节
- `fail`：核心章节大量缺失

---

### 4. 代码块语言标签检查

**规则**：所有代码块必须标注语言类型。

```markdown
✅ ```c
✅ ```bash
✅ ```python

❌ ```
```

**状态判定**：
- `pass`：所有代码块都有语言标签
- `warn`：少量代码块缺失标签
- `fail`：大量代码块缺失标签

---

### 5. 技术术语保留英文检查（抽样）

**规则**：以下术语在正文中应保留英文，而非中文翻译：

`Cortex-M7`, `Cortex-R52`, `AURIX`, `TriCore`, `SPI`, `QSPI`, `I2C`, `CAN`, `CAN-FD`, `LIN`, `UART`, `Ethernet`, `FlexRay`, `ADC`, `DAC`, `GPIO`, `PWM`, `GPT`, `ICU`, `WDG`, `DMA`, `MPU`, `SCU`, `RAM`, `Flash`, `Cache`, `AUTOSAR`, `FreeRTOS`, `ISO 26262`, `E2E`, `DEM`, `DET`, `UDS`, `DTC`, `OBD`, `OS`, `EcuM`, `BswM`, `SchM`

**状态判定**：
- `pass`：未发现明显中文化
- `warn`：发现少量可疑翻译
- `fail`：大量术语被翻译

---

### 6. 目录放置检查

**规则**：文件路径应与文件名前缀一致。

**示例**：
- `HW_Periph_Comm_SPI_...md` 应在 `01_Hardware_硬件层/05_Peripherals/01_Communication/01_SPI/`
- `AUTOSAR_Comm_CAN_...md` 应在 `02_Middleware_中间件层/01_AUTOSAR/01_Communication/01_CAN_CANFD/`

**状态判定**：
- `pass`：路径与前缀匹配
- `warn`：路径与前缀疑似不匹配
- `fail`：明显放错目录

---

### 7. TODO/FIXME 检查

**规则**：检查是否残留 `TODO`、`FIXME`、`待验证`、`待补充` 等未处理标记。

**状态判定**：
- `pass`：无残留
- `warn`：有少量标记（可能是正常的待补充问题章节）
- `fail`：大量未处理标记

---

### 8. Obsidian 双链检查

**规则**：`[[...]]` 格式应成对出现，不应断裂。

**状态判定**：
- `pass`：双链格式正确
- `warn`：发现疑似断裂的双链

---

## 脚本用法

```bash
# 检查单个文件
python .claude/skills/doc-review/scripts/doc-review.py <文件路径>

# 检查目录（递归）
python .claude/skills/doc-review/scripts/doc-review.py <目录路径>

# 输出 JSON
python .claude/skills/doc-review/scripts/doc-review.py <路径> --json

# 只显示 warn/fail
python .claude/skills/doc-review/scripts/doc-review.py <路径> --only-issues
```

---

## 输出格式示例

```text
文件: 01_Hardware_硬件层/.../HW_Periph_Comm_SPI_Specification.md
  文件名        ✅ pass
  标题结构       ✅ pass
  必要章节       ⚠️ warn  缺少: 应用场景
  代码块语言     ✅ pass
  技术术语       ✅ pass
  目录放置       ✅ pass
  TODO/FIXME    ✅ pass
  双链格式       ✅ pass
```

---

## 限制

- **Mermaid 语法校验**：首版只做简单存在性检查，复杂图不深入校验。
- **内部链接有效性**：只检查格式，不保证目标文件一定存在。
- **中文术语判断**：基于关键词列表，可能存在误报。
