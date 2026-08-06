# Google Agents 白皮书精读笔记

> 📚 学习对象：
> 1. **《Agents》**（2024-09，Wiesinger / Marlow / Vuskovic，42 页）— [full.md](../../99_Attachments_附件/AI_Agent/Google-Agents-Whitepaper-2024/full.md)
> 2. **《Introduction to Agents》**（2025-11，Blount / Gulli / Saboo / Zimmermann / Vuskovic，54 页，五部曲首篇）— [full.md](../../99_Attachments_附件/AI_Agent/Google-Introduction-to-Agents-2025/full.md)
>
> 笔记整理：2026-07-19

---

## 一、两篇的关系与演进

| | 2024 原版 | 2025 续作 |
|---|---|---|
| 定位 | **概念奠基**：什么是 Agent | **生产落地**：怎么把 Agent 做成企业级产品 |
| 核心框架 | Model + Tools + Orchestration 三件套 | 三件套 + Deployment 四要素（"身体与腿"） |
| 关键词 | ReAct、Extensions/Functions/Data Stores | L0-L4 分级、Agent Ops、A2A/MCP/AP2、安全治理 |
| 读法 | 建立心智模型 | 建立工程方法论 |

一句话：**2024 版回答"Agent 是什么"，2025 版回答"怎么把 Agent 养好、管好、用起来"**。

---

## 二、2024《Agents》核心要点

### 1. Agent 的定义
> "一个通过观察世界并使用工具采取行动来达成目标的生成式 AI 应用。"

关键特征：**自主性**（无需人类逐步指导）、**主动性**（没有明确指令也能推理下一步）。

### 2. 认知架构三件套（全书骨架）

| 组件 | 角色 | 要点 |
|------|------|------|
| **Model** | 大脑 🧠 | 一个或多个 LM，支持 ReAct/CoT/ToT 推理框架；通常不针对 Agent 配置专门训练 |
| **Tools** | 双手 🙌 | 弥合模型与外部世界的鸿沟，形态类似 Web API（GET/POST/PATCH/DELETE） |
| **Orchestration** | 神经系统 🎛️ | 循环过程：摄入信息 → 内部推理 → 决定下一步行动，直到达成目标 |

### 3. Agents vs Models（经典对比）
- 模型知识止于训练数据；Agent 通过工具连接外部系统
- 模型单次推理无会话管理；Agent 有受管的会话历史（multi-turn）
- 模型无原生工具/逻辑层；Agent 有原生认知架构

### 4. 推理框架三剑客
- **ReAct**：Reason + Act 交替（Thought → Action → Action Input → Observation 循环 N 次 → Final Answer），可带或不带 in-context 示例
- **CoT**：通过中间步骤推理（子技术：self-consistency、active-prompt、multimodal CoT）
- **ToT**：适合探索/战略前瞻任务，泛化 CoT 为思维树

### 5. 三类工具（Google 体系）⭐ 全书最实操的一章

| | Extensions | Function Calling | Data Stores |
|---|---|---|---|
| **执行位置** | Agent 侧 | **客户端侧** | Agent 侧 |
| **本质** | 用示例教会 Agent 调 API（1对多动态选择） | 模型只输出函数名+参数（JSON），**不发真实 API 调用** | 向量库 + RAG，给模型动态知识 |
| **典型场景** | 多跳规划（下一步依赖上一步结果）；用预建扩展（Code Interpreter、Vertex Search） | 安全/认证限制；批量/人工审批；API 不在公网；要额外数据变换 | RAG 应用：网站内容、结构化/非结构化文档 |

**易混点**：Function Calling 里模型只是"填空"生成参数，真正的 API 调用由客户端应用执行 —— 开发者获得数据流的细粒度控制权。

### 6. 定向学习增强模型（厨师类比 👨‍🍳）
- **In-context learning**：给菜谱+食材+示例菜，现场发挥（如 ReAct）
- **Retrieval-based in-context learning**：有个储备丰富的储藏室（外部数据），动态取材（如 Vertex Example Store）
- **Fine-tuning**：送回学校系统学习新菜系

### 7. 落地路径
- **LangChain/LangGraph 快速原型**：`create_react_agent(model, tools)` 几行代码起一个 ReAct Agent
- **Vertex AI 生产级**：Agent Builder + Extensions + Function Calling + Example Store，平台管基础设施，开发者专注 Agent 本身

### 8. 未来方向
- **Agent chaining**（链式组合）→ "mixture of agent experts"（专家混合），各自擅长单一领域的专业 Agent 组合

---

## 三、2025《Introduction to Agents》核心要点

### 1. 新定义（更完整）
> "Model + Tools + Orchestration + **Runtime services**，用 LM 循环达成目标。"

新增第四要素 **Deployment（身体与腿）**：托管、监控、日志、A2A 接口 —— 原型到生产的分水岭。

### 2. 五步问题解决循环 🔄
1. **Get the Mission**（接任务：用户或触发器）
2. **Scan the Scene**（感知环境：记忆、工具可用资源）
3. **Think It Through**（推理规划：思维链分解）
4. **Take Action**（执行：选工具、调用）
5. **Observe and Iterate**（观察结果入记忆，回到 3）

> 精彩论断：**"Agent 本质上是上下文窗口的策展人（curator）"** —— 不断组装上下文 → 提示模型 → 观察结果 → 重组上下文。

### 3. Agent 能力分级（L0-L4）⭐ 2025 版最有传播度的框架

| 级别 | 名称 | 能力 |
|---|---|---|
| **L0** | 核心推理系统 | 裸 LM，无工具无记忆，对训练数据之后的世界"失明" |
| **L1** | 连接的问题解决者 | 接工具（搜索/RAG/股票 API），能查实时信息 |
| **L2** | 战略的问题解决者 | 多步规划 + **上下文工程**（主动筛选/打包/管理每步最相关信息） |
| **L3** | 协作多智能体系统 | "专家团队"模式：PM Agent 把 Mission 分派给专业 Agent（Agent 把其他 Agent 当工具） |
| **L4** | 自进化系统 | 发现能力缺口 → **自主创建新工具/新 Agent**（如 AgentCreator 工具现场造一个舆情监控 Agent） |

### 4. 开发者角色转变
- 传统开发者 = **砌砖工**（精确定义每一步逻辑）
- Agent 开发者 = **导演**（布景=指令、选角=工具、给 context，引导自主"演员"演出）
- 金句：**"prompt engineering" 已进化为 "context engineering"**

### 5. Agent Ops ⭐ 对测试验证工程师最有价值的一章

传统 `assert output == expected` 对概率性系统失效！Agent Ops 方法论：

| 实践 | 要点 |
|------|------|
| **像 A/B 实验一样定义成功** | KPI 不止技术正确性：目标完成率、用户满意度、延迟、单次成本、业务收入 |
| **LM as Judge** | 用强模型按 rubric 评质量（答案对吗？ grounded 吗？遵循指令吗？），跑 golden dataset |
| **Metrics-Driven Development** | 新版本跑全量评估集 vs 生产版本比分，作为部署 Go/No-Go |
| **OpenTelemetry Traces 调试** | 高保真记录完整轨迹：prompt、内部推理、工具选择、参数、返回 —— 回答"为什么" |
| **珍视人类反馈** | bug 报告/点踩 = 新的边缘用例 → 转化为评估集永久测试用例（"给系统打疫苗"） |

> 📌 **与车规测试的对照**：LM Judge ≈ 自动化评审；golden dataset ≈ 回归测试集；trace ≈ 总线日志；反馈闭环 ≈ 问题单转测试用例。理念完全同构，只是被测对象从确定性硬件变成了概率性模型。

### 6. 多 Agent 设计模式
- **Coordinator**：经理 Agent 分派子任务给专家 Agent 并汇总（动态/非线性任务）
- **Sequential**：数字流水线，一个输出接下一个输入（线性任务）
- **Iterative Refinement**：生成者 + 批评者循环改进质量
- **HITL**：高风险动作前人工确认

### 7. 互操作协议生态 🔌
| 协议 | 解决的问题 |
|------|-----------|
| **MCP** | Agent ↔ 工具/数据 的连接标准（事务性请求） |
| **A2A** | Agent ↔ Agent：Agent Card（JSON 名片，能力+端点+凭证）+ 异步任务式通信 |
| **AP2** | Agent 支付：加密签名的"授权令"（mandates），不可抵赖审计链 |
| **x402** | HTTP 402 状态码的机器间微支付 |

### 8. 安全体系 🛡️
- **核心矛盾**：效用 vs 安全的权衡 —— "皮带要长到能干活，短到不会冲进车流"
- **纵深防御**：确定性护栏（硬编码策略引擎，如"超过 $100 阻止"）+ 推理型防御（guard model 审查计划）
- **Agent Identity**：继人（OAuth/SSO）、服务（IAM）之后的**第三类主体**，用 SPIFFE 发"数字护照"，最小权限、控制爆炸半径
- **ADK 实践**：`before_tool_callback` 参数校验、插件化"Gemini as Judge"实时筛查注入、Model Armor 托管服务
- **企业级**：中央网关控制平面（所有 Agent 流量的强制入口）+ 中央注册表（企业应用商店），解决 "agent sprawl"

### 9. 自进化与 Agent Gym 🏋️
- 学习来源：运行时经验（日志/trace/记忆 + HITL 纠正）+ 外部信号（新政策、新文档）
- 两类适应：**增强上下文工程**（优化 prompt/示例/检索）+ **工具优化与创造**
- 合规学习示例：Querying → Reporting → Critiquing → **Learning Agent** 把人类专家的纠正泛化成可复用规则
- **Agent Gym**：离线仿真平台（不在执行路径上），合成数据生成器 + 红队 + 批评 Agent 家族，压力测试并优化多 Agent 系统

### 10. 两个标杆案例
- **Google Co-Scientist**：科研协作 Agent 生态，Supervisor 分派任务，生成-评估假设循环，跑几小时甚至几天（已产出真实科研突破）
- **AlphaEvolve**：进化式算法发现 Agent（Gemini 生成代码 + 自动评估器打分 + 优胜劣汰），成果：更快的矩阵乘法、数据中心优化。**适合"验证比求解容易"的问题**

---

## 四、贯通思考：两篇合起来告诉我们什么

1. **架构稳定性**：三件套（Model/Tools/Orchestration）从 2024 到 2025 没变，说明这是经过检验的范式 —— 值得作为分析任何 Agent 系统的默认拆解框架
2. **工程重心迁移**：2024 年大家在玩原型（LangChain quick start），2025 年主题已变成评估、安全、治理、成本 —— **行业从"能跑"进入"敢用"阶段**
3. **测试验证是 Agent 时代的核心岗位**：2025 版近半篇幅（Agent Ops / LM Judge / 评估集 / trace / 红队）本质都是"如何验证一个概率性系统" —— 这正是验证工程师的主场 💪
4. **协议化 = 分层解耦**：MCP（工具层）/A2A（协作层）/AP2（交易层）的分层，和 AUTOSAR 的分层哲学（MCAL/ECU抽象/服务层各管各的接口）异曲同工
5. **L4 自进化是最值得跟踪的前沿**：能自主造工具/造 Agent 的系统，将彻底改变"验证"的含义 —— 如何验证一个会自己变化的系统？（Agent Gym 是 Google 给的答案雏形）

---

## 五、值得回读的章节指引

| 想深入了解 | 去读 |
|---|---|
| Function Calling 代码细节 | 2024 版 p.18-26（Snippet 5-7，ski trip 示例） |
| ReAct 完整循环示例 | 2024 版 p.10-11 + p.35-37（LangChain 示例） |
| 三类工具选择决策 | 2024 版 p.32（对比表） |
| L0-L4 分级原文 | 2025 版 p.14-18 |
| Agent Ops 完整方法论 | 2025 版 p.27-31 |
| 安全体系（ADK/SPIFFE/Model Armor） | 2025 版 p.34-38 |
| 自进化 + Agent Gym | 2025 版 p.42-46 |
