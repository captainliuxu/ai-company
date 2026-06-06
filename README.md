# AI Companion Pro Demo

一个面向作品集与面试展示的 AI 陪伴聊天 Demo，核心围绕 `Persona + Emotion + Memory + RAG + Chat UI` 搭建。

## 项目亮点

- 多角色人格系统：内置 `小暖`、`小锐`、`小默` 三个预设角色
- 流式聊天体验：后端通过 `SSE` 推送回复，前端逐步渲染
- 情绪与关系状态：维护 `favorability`、`trust`、`mood`、`dependency` 时间线
- 长期记忆系统：提取用户事实、偏好、事件，并跨会话持久化
- 轻量 RAG：使用 `sentence-transformers` 做向量召回与混合排序
- 对话摘要：长会话自动压缩，降低上下文膨胀
- 产品化前端：角色选择、聊天页、洞察面板、语音输入/播放、会话恢复

## 技术栈

- Backend: `FastAPI` + `SQLAlchemy` + `SQLite`
- Frontend: `Next.js` + `React` + `Tailwind CSS`
- Embedding: `sentence-transformers` (`all-MiniLM-L6-v2`)
- Chat Model: `Gemini` via `api.xykjy.com` OpenAI-compatible proxy
- Voice: 独立语音 provider 配置，支持 `STT` / `TTS`

## 当前功能

- `Persona API`
  - `GET /api/v1/personas`
  - `GET /api/v1/personas/{persona_id}`
- `Chat API`
  - `POST /api/v1/chat/session`
  - `GET /api/v1/chat/session/{session_id}`
  - `POST /api/v1/chat/send`
- `Emotion API`
  - `GET /api/v1/emotion/{session_id}`
  - `GET /api/v1/emotion/{session_id}/history`
- `Memory API`
  - `GET /api/v1/memories/{session_id}`
- `Voice API`
  - `GET /api/v1/voice/health`
  - `POST /api/v1/voice/stt`
  - `POST /api/v1/voice/tts`

## 快速启动

### 1. 安装后端依赖

```powershell
pip install -r E:\ai-companion\requirements.txt
```

### 2. 启动后端

```powershell
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

启动后访问：

- Swagger: [http://localhost:8000/docs](http://localhost:8000/docs)

### 3. 安装前端依赖

```powershell
npm install --prefix E:\ai-companion\frontend
```

### 4. 启动前端

```powershell
npm run dev --prefix E:\ai-companion\frontend
```

启动后访问：

- App: [http://localhost:3000/personas](http://localhost:3000/personas)

## 环境变量

参考根目录的 `.env.example`。

项目主要依赖以下配置：

- `AI_API_KEY`
- `AI_BASE_URL`
- `AI_MODEL`
- `VOICE_ENABLED`
- `VOICE_API_KEY`
- `VOICE_BASE_URL`
- `VOICE_STT_MODEL`
- `VOICE_TTS_MODEL`
- `VOICE_TTS_VOICE`

## 目录说明

```text
backend/        FastAPI 后端
frontend/       Next.js 前端（真实项目入口）
next-app/       废弃脚手架目录，可忽略
docs/           任务、问题、验收与架构文档
data/           SQLite 数据与缓存
```

## 项目状态

按 `PROJECT_PLAN.md` 的 8 个开发阶段，核心能力已完成，当前仓库可作为演示版本使用：

- Persona System
- Chat API + Prompt Builder
- Emotion System
- Long-term Memory
- Lightweight RAG
- Conversation Summary
- Product Chat UI
- 集成调试与 Demo 打磨

## 文档入口

- [AGENTS.md](AGENTS.md)
- [PROJECT_PLAN.md](PROJECT_PLAN.md)
- [docs/TASK_BOARD.md](docs/TASK_BOARD.md)
- [docs/ISSUES_LOG.md](docs/ISSUES_LOG.md)

## 注意事项

- 真正的前端目录是 `frontend/`，不是 `next-app/`
- 本项目使用 `SSE`，不使用 `WebSocket`
- 数据库默认是本地单文件 `SQLite`
- 语音、聊天和向量召回都依赖外部模型服务与网络配置
