# AI Companion Pro Demo

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
| AI SDK | OpenAI SDK (兼容 Gemini via api.xykjy.com) |
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

- Backend API: https://api.xykjy.com
- Backend admin: https://api.xykjy.com/admin
