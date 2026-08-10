# Google Agents 白皮书 · 伴读笔记（第 2 讲）

> 📖 主题：Agents vs Models 能力边界 + 认知架构（厨师类比）+ ReAct 循环拆解
> 🗓️ 整理：2026-08-06 ｜ 来源：白皮书 p.8-11、p.35-37 + 伴读讨论凝练
> 🔗 原文：[full.md](../../99_Attachments_附件/AI_Agent/Google-Agents-Whitepaper-2024/full.md)

---

## 一、Agents vs Models：能力边界的官方划分

> 原文对比表（p.8）四行差异：

| | Models | Agents |
|---|---|---|
| **知识** | 止于训练数据 | 通过工具连接外部系统，知识被延伸 |
| **会话** | 单次推理，无 session history 管理 | 受管的多轮会话历史，由编排层维护 |
| **工具** | 无原生工具实现 | 工具是架构内生的 |
| **逻辑层** | 无原生逻辑层；用户**手工**用 CoT/ReAct 拼 prompt | 原生认知架构，框架内置于系统 |

### 核心拆解：模型是纯函数，Agent 是进程

四行差异收敛于一个事实：

- **模型** = `f(context) → tokens`：无状态、无副作用，每次调用宇宙重启一次
- **Agent** = 围绕纯函数搭的**有状态系统**：session history 是它的"内存"，工具是它的"外设"，编排层是它的"主循环"

🚗 车规类比：**MCU 芯片 vs 整块 ECU**。硅片（model）只是计算单元；ECU（agent）= 硅片 + 外设驱动 + 调度循环 + 线束。

### 两个值得记住的细节

1. **第 4 行藏了个微妙的承认**：裸模型也能跑 CoT/ReAct——只要用户手工拼 prompt。所以分界不在"能不能推理"，而在**循环归谁所有**：循环在代码里 = Agent，循环在人手里 = 人在用模型。
2. **"人肉 ReAct"判决**：手工写 ReAct prompt → 模型输出 `Action: Search["xxx"]` → 人手动搜索贴回去——按官方表这**不算 Agent**，因为编排层是人。此刻人就是那个 while 循环。**Agent 性不在模型里，在循环的归属权里。**

---

## 二、厨师类比：认知架构 = 闭环控制

### 1. 原文场景（p.8-9）

厨师的循环：收集信息（订单+储藏室食材）→ 内部推理（能做什么菜）→ 采取行动（切菜/调香料/煎肉）→ **每阶段按需调整**（食材耗尽、客户反馈→修正计划，用之前的结果决定下一步）。

原文落点：*"This cycle of information intake, planning, executing, and adjusting describes a unique cognitive architecture."*

### 2. 逐句映射

| 厨师 | Agent | 三件套归属 |
|------|-------|-----------|
| 客人订单 | user query / mission | — |
| 看储藏室有什么食材 | 工具查询，感知环境 | Tools（观察通道） |
| 琢磨能做什么菜 | 模型推理 | Model |
| 切菜、调香料、煎肉 | 工具调用，改变世界 | Tools（动作通道） |
| 食材没了 / 客人说太咸 | Observation：行动结果+环境反馈 | → 回流编排层 |
| 尝一口再决定加不加盐 | 中间验证，re-planning | Orchestration |

### 3. 第一性原理：这就是闭环控制 🚗

- **裸模型单次调用 = 开环**：输入 query → 一次性输出，对不对看运气（相当于启动工况开环喷油，按 map 走无反馈）
- **Agent = 闭环**：观察 → 推理 → 行动 → **观察行动结果** → 再推理……直到目标达成

| lambda 闭环燃油控制 | Agent 环 |
|---------------------|----------|
| 氧传感器采样 | observe（工具查询） |
| ECU 计算修正量 | model 推理 |
| 喷油器执行 | act（工具调用） |
| 排气氧含量变化 | 世界状态改变 |
| 下一拍再采样 | observation 回流 |

**关键洞察**：闭环控制的魅力在于**执行器有噪声也没关系**——只要反馈真实、环路纠偏，被控量就能收敛。同理：模型每拍可能想错，但 Observation 是真实世界数据，环路有机会下一拍把错误对冲掉。

> 🎯 **单次推理的可靠性靠模型，多轮任务的可靠性靠环路。**

⚠️ 反面也成立：**传感器漂移，闭环反而把系统带偏**——工具返回被污染（如网页埋 prompt injection），循环会忠实地把垃圾当反馈吃下去。（2025 版安全章伏笔）

### 4. 编排层四项职责

原文："responsible for maintaining **memory, state, reasoning and planning**"

| 职责 | 含义 | 物理载体 |
|------|------|----------|
| memory | 之前发生过什么（历史轨迹） | 往轮 Thought/Action/Observation |
| state | 现在进展到哪（当前快照） | 任务进度、中间产物 |
| reasoning | 这一拍怎么想 | 模型推理 |
| planning | 接下来怎么走 | 行动选择 |

四样的物理载体 = **每一轮塞进 prompt 的那坨上下文**。编排层每拍都在：打包 memory+state 进上下文 → 模型 reasoning → 产出下一步 plan。2025 版"Agent 是上下文窗口的策展人"在此已见雏形。

### 5. 为什么叫 "cognitive" 而不叫 "program"？

cron job / 批处理脚本也是循环，区别只有一个：**每一拍的内容从哪来**。

| | 步骤序列何时确定 |
|---|---|
| 脚本 | **设计时**：程序员写死每一步 |
| Agent | **运行时**：模型现场生成每一拍 |

循环里装着"内部推理"才配得上 cognitive——正是第 1 讲的"确定性骨架 + 概率性心跳"。另一隐含差别：**停止条件是目标，不是计数**。厨师把菜做完才停，不是切满 100 刀就停；脚本是 `for i in range(N)`，Agent 是 `while not goal_achieved()`。

---

## 三、ReAct 循环逐拍拆解

### 1. 推理框架三剑客定位

| 框架 | 一句话 | 形态 |
|------|--------|------|
| **CoT** | **只想不做**：中间步骤推理，无工具 | 一条思维链，开环内心戏 |
| **ReAct** | **边想边做**：Reason+Act 交替，工具在环 | 思维链+动作链交织，闭环 |
| **ToT** | **多想几条路**：泛化 CoT 为思维树 | 树搜索，适合探索/前瞻 |

CoT 子技术：self-consistency（多链投票）、active-prompt、multimodal CoT。

### 2. 六拍拆解：每拍的"产权归属"

序列：**Question → Thought → Action → Action Input → Observation →（循环 N 次）→ Final Answer**

| 拍 | 内容 | 谁产出 | 性质 |
|---|------|--------|------|
| Question | 用户原始问题 | 用户 | ✅ 确定 |
| Thought | "我下一步该干什么" | 模型 | 🎲 概率 |
| Action | 选哪个工具，如 `[Flights, Search, Code, None]` | 模型 | 🎲 概率（**选择集是确定枚举**） |
| Action Input | 给工具传什么参数 | 模型 | 🎲 概率（schema 可约束） |
| Observation | 工具执行结果 | **工具/世界** | ✅ **确定（真实数据）** |
| Final Answer | 最终回答 | 模型 | 🎲 概率 |

**洞察 1：概率拍与确定拍交替。** 模型连出三拍概率（Thought/Action/ActionInput），世界回一拍确定（Observation）——每轮循环模型想象三步，就被现实校准一次。**用世界的真实，锚定模型的想象。**

**洞察 2：Action 选择集 = 枚举约束**——第 1 讲工具箱第 1 层"收窄方差"的具体落地。**`None` 是合法选项**："决定不调工具"是元决策，其质量决定 Agent 是"瞎勤快"还是"够沉稳"。

**洞察 3：上下文逐轮累积。** 每轮 Thought/Action/Observation 全部回灌下一轮 prompt = memory 的物理实现；代价是上下文越滚越大——2025 版 "context engineering" 的病根在此埋下。

**洞察 4：ReAct 为什么 "improve human interoperability and trustworthiness"？** 推理轨迹天然留痕，可回放、可审计、可定位错在哪一拍。🚗 黑匣子/总线日志的价值——2025 版 OpenTelemetry traces 方法论的种子。

---

## 四、真实 trace 对照（LangChain 示例，p.35-37）

两跳问题：`create_react_agent(model, tools)` 一行起 ReAct Agent。

```txt
Human:  Texas Longhorns 上周和谁比赛？对方球队的体育场地址是什么？
AI:     [Action] search(query="Texas Longhorns football schedule")
Tool:   {...NCAA, Georgia, Date...}                        ← Observation 1
AI:     中间结论：对手是 Georgia Bulldogs
        [Action] places(query="Georgia Bulldogs stadium")  ← 参数来自上一拍观察！
Tool:   {...Sanford Stadium: 100 Sanford...}               ← Observation 2
AI:     Final Answer: 100 Sanford Dr, Athens, GA 30602, USA
```

- 六拍一一对上：Question=Human 消息；Action/Action Input=AI 的 Tool Calls；Observation=Tool Message；Final Answer=末条 AI 消息
- LangChain 实现里 Thought 不显式打印——**轨迹里想不想得见取决于框架，这是工程自由度**
- **精髓在第二跳**：`places` 的参数用第一跳 Observation 里的事实构造——开环单次调用做不到（提问时不知道对手是谁）。**多跳规划（multi-hop）是闭环循环的独占能力**，工具章 Extensions 选型还会用到这个判据

---

## 五、金句集 💎

1. **模型是纯函数，Agent 是进程** —— session history 是内存，工具是外设，编排是主循环
2. **单次推理的可靠性靠模型，多轮任务的可靠性靠环路**
3. **Agent 性不在模型里，在循环的归属权里** —— 人肉 ReAct 里，人就是那个 while 循环
4. **用世界的真实，锚定模型的想象** —— 概率拍与确定拍交替
5. **停止条件是目标，不是计数** —— `while not goal_achieved()` vs `for i in range(N)`

---

## 六、待讨论（第 2 讲思考题）

1.（①）Google 为什么把"受管 session history"抬到**架构级**差异，而不只是一个功能特性？
2.（①）"人肉 ReAct 不算 Agent"的判决，你认同吗？
3.（②）闭环视角下，Agent 环路里的"被控对象"到底是什么？
4.（②）厨师"尝一口汤"对应 Agent 的什么机制？如果让你设计 Agent 的"尝汤"环节，怎么实现？
5.（③）Observation 是确定拍——如果工具本身返回错误数据（不是模型错），循环会怎样演化？
6.（③）模型何时决定 `Action=None` / 给出 Final Answer？这个判断错了（过早/过晚停止）会怎样？

---

*下一讲：Tools 章——Extensions / Function Calling / Data Stores 三类工具 + 选择决策表（全书最实操一章，p.13-32）*
