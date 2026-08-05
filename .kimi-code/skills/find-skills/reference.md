# Find Skills — 详细参考

本文件是 `find-skills` Skill 的详细用法参考。如果你只想知道触发条件和快速入口，请阅读 [`SKILL.md`](./SKILL.md)。

---

## Skills CLI 是什么

`npx skills` 是开放 Agent Skills 生态的包管理器。Skill 是模块化包，通过专业知识、工作流和工具扩展 Agent 能力。

**核心命令**：

| 命令 | 用途 |
|------|------|
| `npx skills find [query]` | 按关键词搜索 Skill |
| `npx skills add <package>` | 从 GitHub 等源安装 Skill |
| `npx skills check` | 检查 Skill 更新 |
| `npx skills update` | 更新所有已安装 Skill |

**浏览地址**：https://skills.sh/

---

## 如何帮用户找 Skill

### 步骤 1：理解需求

明确：
1. 领域（如 React、testing、design、deployment）
2. 具体任务（如写测试、创建动画、PR review）
3. 是否足够通用，可能存在现成 Skill

### 步骤 2：搜索 Skill

```bash
npx skills find [query]
```

示例：

- 用户问 "how do I make my React app faster?" → `npx skills find react performance`
- 用户问 "can you help me with PR reviews?" → `npx skills find pr review`
- 用户问 "I need to create a changelog" → `npx skills find changelog`

典型返回结果：

```
Install with npx skills add <owner/repo@skill>

vercel-labs/agent-skills@vercel-react-best-practices
└ https://skills.sh/vercel-labs/agent-skills/vercel-react-best-practices
```

### 步骤 3：向用户展示选项

展示内容：
1. Skill 名称和作用
2. 安装命令
3. 链接到 skills.sh

示例回复：

```
I found a skill that might help! The "vercel-react-best-practices" skill provides
React and Next.js performance optimization guidelines from Vercel Engineering.

To install it:
npx skills add vercel-labs/agent-skills@vercel-react-best-practices

Learn more: https://skills.sh/vercel-labs/agent-skills/vercel-react-best-practices
```

### 步骤 4：安装 Skill

如果用户同意，可直接安装：

```bash
npx skills add <owner/repo@skill> -g -y
```

- `-g`：全局安装（用户级）
- `-y`：跳过确认提示

---

## 常见 Skill 类别

| 类别 | 示例查询 |
|------|----------|
| Web Development | react, nextjs, typescript, css, tailwind |
| Testing | testing, jest, playwright, e2e |
| DevOps | deploy, docker, kubernetes, ci-cd |
| Documentation | docs, readme, changelog, api-docs |
| Code Quality | review, lint, refactor, best-practices |
| Design | ui, ux, design-system, accessibility |
| Productivity | workflow, automation, git |

---

## 搜索技巧

1. **使用具体关键词**："react testing" 比 "testing" 更好
2. **尝试同义词**："deploy" 不行就试 "deployment" 或 "ci-cd"
3. **关注热门来源**：`vercel-labs/agent-skills`、`ComposioHQ/awesome-claude-skills`

---

## 找不到 Skill 时

如果未找到相关 Skill：

1. 说明未找到现成 Skill
2. 表示可以直接用通用能力帮助
3. 建议用户可用 `npx skills init` 创建自己的 Skill

示例回复：

```
I searched for skills related to "xyz" but didn't find any matches.
I can still help you with this task directly! Would you like me to proceed?

If this is something you do often, you could create your own skill:
npx skills init my-xyz-skill
```
