---
name: purpose-driven-book-study
description: Build and run a purpose-driven, question-led study program for technical books, standards, manuals, and long documents, with staged Markdown summaries tied to the user's workstream. Trigger when the user says "精读", "带读这本书", "建学习路线", "目的驱动学习", "书籍伴读", "这本书帮我规划怎么学", or starts a multi-session book/document study. Do NOT use for one-shot summarization (use summarize), PDF/document format conversion (use mineru-pdf-parser), or casual Q&A with no persistent study output.
---

# 目的驱动型精读（Purpose-Driven Book Study）

朝着"能力/工作问题"学习，而不是朝着"读完页码"学习。把目录当知识索引用，不当必须遵守的顺序用。

> 来源：由 GPT 版 skill 内化而来（原件已归档至 `90_Archive_归档/`）。
> 参考实现：`SoC设计基础教程` 精读会话（跳读路线 + 每阶段专区沉淀 + ✅🟡❓ 疑点分级 + 复述验收 + 讨论点收尾）。

## 触发条件

用户提到以下任一表达，或开始一个跨会话的书籍/标准/长文档学习任务时调用本 skill：

- "精读"、"带读这本书"、"书籍伴读"
- "建学习路线"、"规划怎么学"、"目的驱动学习"
- "我们专门开个会话来学 XXX 这本书"
- 上传整本书/长文档并要求系统性学习

**不要用于**：一次性网页/PDF 摘要（→ `summarize`）、文档格式转换（→ `mineru-pdf-parser`）、无沉淀产出的零散问答。

## 核心规则

1. 先建立全书视角，再教具体章节（先森林后树木）。
2. 先搞清用户当前工作主线、目标能力、具体问题——优先从可见上下文（仓库、会话）推断，只问缺了会改变路线的信息。
3. 围绕**问题、机制、依赖**组织学习，不默认按章节顺序。
4. 素材分级：`精读 / 支撑读 / 略读 / 暂缓`，并说明分级理由。
5. 辩证阅读：区分观点、机制、证据、假设、边界、反例、迁移条件。
6. **来源纪律**：原书观点 / 我的解读 / 对用户的延伸 / 外部验证——四类内容分开标注，不混说。
7. 每个概念阶段结束落盘一篇 Markdown 阶段总结，绑定当前工作主线。
8. 新问题或错误认识暴露更优依赖顺序时，修订路线。

## 七步工作流（详见 reference.md）

| 步骤 | 名称 | 产出 |
|------|------|------|
| 1 | 审读原书 | 作者意图/读者/结构/证据类型/适用范围判断 |
| 2 | 全书定位图 | `00-学习路线与问题地图.md`（长期项目时落盘） |
| 3 | 问题驱动路线 | 阶段表：核心问题/能力目标/章节映射/深度/工作关联/验证方式/输出物 |
| 4 | 教学单元 | 提问→原书立场→机制→证据→边界→挑战→迁移→验证 |
| 5 | 来源纪律 | 四类标签贯穿全程 |
| 6 | 阶段收尾 | `阶段NN-主题总结.md` + 路线更新 |
| 7 | 全书综合 | `全书综合总结与实践路线.md` |

## 本库输出约束（内化）

- **对话内**：不用 LaTeX/Mermaid（渲染不了）——公式用纯文本，图用 ASCII 字符画或表格（LRN-20260815-001）。
- **落盘笔记**：遵循 CLAUDE.md §9.2 模板与 §3.2 命名规范；原始素材（PDF/MinerU 解析）入 `99_Attachments_附件`，消化产出入笔记层专区（§9.1 规则 12，引用方向：笔记 → 附件）。doc-review hook 会自动校验。
- **路线变更/批量落盘前**：先给方案等用户确认（LRN-20260717-001）。
- **疑点分级**：✅确定 / 🟡有出入 / ❓未验证。
- 学习过程中产生的错误纠正、好方法，按 self-improving-agent 记入 `.learnings/`。

## 配套文件

| 文件 | 用途 |
|------|------|
| `reference.md` | 七步工作流完整细则 + 本库内化细则 + 参考实现案例 |
| `gotchas.md` | 陷阱与失败模式 |
| `config.json` | 文档名/标签/输出约束等默认值 |
| `references/document-templates.md` | 路线文档、阶段总结、全书综合三个模板 |
| `references/kimi-code-instruction.md` | 同方法论的 Kimi Code 自包含指令版（粘贴即用） |
