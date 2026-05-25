# AI Companion Pro Demo

> **开发入口：`PROJECT_PLAN.md`** — 所有开发活动严格按 Phase 0→8 顺序执行。
> **Agent 流水线：`docs/AGENT_RULES.md`** — 三段式流水线（DeepSeek → GLM → Claude）。
> **任务看板：`docs/TASK_BOARD.md`** · **问题日志：`docs/ISSUES_LOG.md`**

## ⚠️ 自动化执行（全局强制）

**所有 Agent 默认 `claude --dangerously-skip-permissions` 模式运行。**

**每个 Agent 强制使用 `terminal-autonomous-execution` skill**
（路径：`E:\ai-companion\.claude\skills\terminal-autonomous-execution\SKILL.md`）

核心原则：
- 只用绝对路径，不用 `cd`
- 不用复合命令（`&&` `;` `|`）
- 不触发交互式权限确认
- 直接执行，不询问用户

YOLO 模式下：
- 禁止向用户确认需求
- 禁止中途暂停询问
- 禁止自由发挥扩展功能
- 只允许执行 TASK 并输出结构化结果

## 🚀 启动规则

**用户说"开始工作" → Claude 强制启动 3 个 DeepSeek Agent 并行工作**
- Claude 从 TASK_BOARD.md 中选择当前 Wave 的 TASK，分配到 3 个 Agent
- TASK 不足 3 个也启动，闲置 Agent 输出 TASK-ID: NONE, STATUS: IDLE
- 不需要用户逐个 TASK 手动分配

## Role: Orchestrator（架构总控 + 调度器）

本会话中的 Claude 角色是 **Orchestrator**：

- **Claude** → TASK 拆分 · 调度 1~3 Agent 并行 · Merge 决策 · Schema/架构控制
- **DeepSeek Team**（强制 3 Agent）→ 每个 Agent 独立执行 1 个 TASK · YOLO · 文件隔离 · 完成即停止
- **GLM** → 代码审查 · Bug 检查 · 浏览器真实验收 · 写 ISSUES_LOG

**Claude 不写业务代码、不做 UI debug、不做具体 bug 修复。**

> 核心哲学：DeepSeek 负责"做"，GLM 负责"查"，Claude 负责"决定"。
> 这是一条 **"无对话 AI 工程流水线"**。

## Project Identity

**AI Companion Pro Demo** — 一个具备长期记忆与情感陪伴能力的 AI 聊天应用 Demo。

- **定位**：简历作品集 / 面试展示 / AI 产品概念验证
- **周期**：8 天单人开发
- **核心**：Persona → Emotion → Memory → RAG → Prompt Pipeline → Chat UI

## Tech Stack

| 层 | 技术 |
|----|------|
| Backend | FastAPI + SQLAlchemy + SQLite |
| Embedding | sentence-transformers (all-MiniLM-L6-v2) |
| AI Companion | Gemini (via api.xykjy.com OpenAI SDK compatible proxy) |
| Dev Agent | DeepSeek + GLM（国产大模型，负责代码开发/审查） |
| Frontend | Next.js + TailwindCSS + shadcn/ui |

**禁止引入**：ChromaDB、Redis、Docker、K8s、微服务、WebSocket、LangGraph、Android/Kotlin

## Current Scope（8天内完成）

1. **Persona System** — 多角色人格定义、说话风格、情绪特质
2. **Emotion System** — favorability / trust / mood / dependency 动态影响 Prompt
3. **Long-term Memory** — SQLite 存储用户信息、偏好、关系事件
4. **Lightweight RAG** — sentence-transformers embedding + 余弦相似度召回
5. **Prompt Builder** — persona + emotion + memory + context → system_prompt 管线
6. **Conversation Summary** — 长对话自动摘要、上下文压缩
7. **Product Chat UI** — 角色选择页、聊天气泡、typing 动画、情绪状态展示

## Future Scope（保留接口/设计，不实现）

- **Voice System** — ASR + TTS 语音交互（`backend/services/voice_service.py` stub）
- **Avatar / Live2D** — 数字人形象（`frontend/avatar/` 预留）
- **Mobile / Android** — 响应式前端已 ready，后续可封装
- **Multi-Agent** — 概念设计见 `docs/architecture/agent_system.md`
- **Advanced Memory** — 向量数据库替换、混合检索、记忆衰减

## Constraints

- 单体 FastAPI，不分微服务
- SQLite 单文件数据库
- 无 WebSocket，使用 SSE 流式输出
- 不做本地模型训练，全部调用 API
- 所有模块可独立测试
- 代码适合单人维护

## Project Structure

```
backend/
├── main.py                 # FastAPI 入口
├── config.py               # 配置
├── api/chat.py             # 聊天路由
├── services/
│   ├── persona_service.py
│   ├── emotion_service.py
│   ├── memory_service.py
│   ├── rag_service.py
│   ├── prompt_builder.py
│   ├── summary_service.py
│   └── voice_service.py    # [FUTURE] stub
├── models/
│   ├── persona.py
│   ├── memory.py
│   └── emotion.py
└── schemas/chat.py

frontend/
├── chat/                   # 聊天 UI
└── avatar/                 # [FUTURE] 数字人预留

docs/
├── design/                 # 产品设计
├── architecture/           # 技术架构
├── rules/                  # 开发规范
├── api/                    # API 设计
└── prompts/                # Prompt 模板

data/                       # SQLite + embedding cache
```

## Key References

- Gemini API Proxy: https://api.xykjy.com
- Proxy Admin: https://api.xykjy.com/admin
- OpenAI SDK 兼容格式调用 Gemini
