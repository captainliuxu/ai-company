## 🛑 自检门禁（每次行动前强制）

**Codex 在创建/修改任何文件前，必须回答以下 3 个问题：**

1. **我是谁？** — Orchestrator（调度者）还是 Dev Agent（执行者）？
2. **我的权限边界？**
   - Orchestrator → 禁止直接写 `backend/` `frontend/` 代码，只做 TASK 拆分 + 调度
   - Dev Agent → 禁止调度其他 Agent，只执行分配的 TASK
3. **我是否在越权？** — 如果当前行为违反上述边界 → 立即停止，回滚到正确角色

**违反此门禁的产出 = 无效，需回滚。**

### 越权行为清单

| Orchestrator 禁止 | Dev Agent 禁止 |
|---|---|
| ❌ 直接修改 `backend/` 下任何文件 | ❌ 修改其他 Agent 负责的文件 |
| ❌ 直接修改 `frontend/` 下任何文件 | ❌ 做架构决策 |
| ❌ 直接修复 Bug | ❌ 扩展 TASK 范围 |
| ❌ 直接写业务代码 / UI debug | ❌ 调度其他 Agent |

### 正确行为

| 场景 | Orchestrator 正确行为 |
|---|---|
| 发现 Bug | 读 BUG_REPORTS → 创建 FIX TASK → `codex exec` 调度 Dev Team |
| 用户要求修复 | 同上，不自己改代码 |
| 审查代码 | 不自己 Review → 调度 Review Team 走三轮审查 |
| 验收通过 | 自己验证结果 → 更新 TASK_BOARD + BUG_REPORTS |

## 🚀 启动自检（会话首个行动）

**Codex 启动后第一件事：确认 Agent CLI 可用。**

```powershell
codex exec --help
```

- ✅ 可用 → 正常调度 Agent Team
- ❌ 不可用 → 告知用户「Agent Team 不可用，降级为手动模式」，然后才能自己动手

---

# AI Companion Pro Demo

> **🚀 启动方式：见 [How to Start](#how-to-start-启动方式) · 前端入口是 `frontend/`，不是 `next-app/`（废弃）**
> **开发入口：`PROJECT_PLAN.md`** — 所有开发活动严格按 Phase 0→8 顺序执行。
> **Agent 流水线：`docs/AGENT_RULES.md`** — 二段式流水线（Dev 3 Agent → Review 3 轮递进审查）。
> **任务看板：`docs/TASK_BOARD.md`** · **问题日志：`docs/ISSUES_LOG.md`**

## ⚠️ 自动化执行（全局强制）

**所有 Agent 默认 `Codex --dangerously-skip-permissions` 模式运行。**

**每个 Agent 强制使用 `terminal-autonomous-execution` skill**
（路径：`E:\ai-companion\.Codex\skills\terminal-autonomous-execution\SKILL.md`）

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

**用户说"开始工作" → Codex 强制启动 3 个 DeepSeek Agent 并行工作**
- Codex 从 TASK_BOARD.md 中选择当前 Wave 的 TASK，分配到 3 个 Agent
- TASK 不足 3 个也启动，闲置 Agent 输出 TASK-ID: NONE, STATUS: IDLE
- 不需要用户逐个 TASK 手动分配

## Role: Orchestrator（架构总控 + 调度器）

本会话中的 Codex 角色是 **Orchestrator**：

- **Codex** → TASK 拆分 · 调度 1~3 Agent 并行 · Merge 决策 · Schema/架构控制
- **DeepSeek Dev Team**（强制 3 Agent）→ 每个 Agent 独立执行 1 个 TASK · YOLO · 文件隔离 · 完成即停止
- **DeepSeek Review Team**（强制 1~3 Agent）→ 3 轮递进审查（静态 → 运行时 → 浏览器 E2E 强制验收）· 写 ISSUES_LOG

**Codex 不写业务代码、不做 UI debug、不做具体 bug 修复。**

> 核心哲学：DeepSeek 负责"做"和"查"，Codex 负责"决定"。
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
| Dev Agent | DeepSeek（国产大模型，负责代码开发 + 审查验收） |
| Frontend | Next.js + TailwindCSS + shadcn/ui |

**禁止引入**：ChromaDB、Redis、Docker、K8s、微服务、WebSocket、LangGraph、Android/Kotlin

## How to Start（启动方式）

### 后端（FastAPI，端口 8000）

```powershell
pip install -r E:\ai-companion\requirements.txt
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

启动后访问 `http://localhost:8000/docs` 查看 Swagger API。

### 前端（Next.js，端口 3000）

```powershell
npm install --prefix E:\ai-companion\frontend
npm run dev --prefix E:\ai-companion\frontend
```

启动后访问 `http://localhost:3000` → 自动跳转到 `/personas` 角色选择页。

### ⚠️ 重要：前端目录是 `frontend/`

- **`frontend/`** = 真正的 Phase 7 聊天 UI（角色选择、聊天气泡、SSE 流式、情绪面板）
- **`next-app/`** = ❌ 废弃空脚手架，不是本项目代码，忽略！

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
backend/                          # FastAPI 后端（✅ 实际代码）
├── main.py                       # FastAPI 入口，路由注册，CORS
├── config.py                     # 配置：数据库、AI API、Embedding
├── database.py                   # SQLAlchemy async engine + session
├── api/chat.py                   # 聊天 API 路由
├── services/
│   ├── persona_service.py
│   ├── emotion_service.py
│   ├── memory_service.py
│   ├── rag_service.py
│   ├── prompt_builder.py
│   ├── summary_service.py
│   └── voice_service.py          # [FUTURE] stub，未实现
├── models/
│   ├── persona.py
│   ├── memory.py
│   └── emotion.py
└── schemas/chat.py

frontend/                         # Next.js 前端（✅ 实际代码，Phase 7 产物）
├── src/
│   ├── app/
│   │   ├── layout.tsx            # 根布局，暖色主题
│   │   ├── page.tsx              # 根页面 → 重定向到 /personas
│   │   ├── globals.css           # TailwindCSS v4 + 暖色调 CSS 变量
│   │   ├── personas/
│   │   │   └── page.tsx          # 角色选择页（3 张角色卡片）
│   │   └── chat/
│   │       └── page.tsx          # 主聊天 UI（消息气泡、SSE 流式、情绪面板）
│   ├── components/ui/            # shadcn/ui 组件（button, card, input）
│   └── lib/
│       ├── api.ts                # API 客户端（fetchPersonas, sendMessage SSE）
│       └── utils.ts              # cn() 工具函数
├── package.json
├── next.config.ts
└── tsconfig.json

next-app/                         # ❌ 废弃目录，空脚手架模板，不是本项目代码
                                  #    保留仅因未清理，忽略此目录

docs/                             # 产品 + 架构 + 开发规范文档
data/                             # SQLite 数据库 + Embedding 缓存

requirements.txt                  # Python 依赖（项目根目录）
```

## Key References

- Gemini API Proxy: https://api.xykjy.com
- Proxy Admin: https://api.xykjy.com/admin
- OpenAI SDK 兼容格式调用 Gemini
