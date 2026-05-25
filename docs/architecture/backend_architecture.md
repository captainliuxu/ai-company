# Backend Architecture

## Overview

单体 FastAPI 应用。所有服务共享一个 SQLite 数据库。

```
                  ┌──────────┐
                  │  Next.js │
                  │  Frontend│
                  └────┬─────┘
                       │ SSE (streaming) + REST
                  ┌────▼─────┐
                  │  FastAPI │
                  │  Server  │
                  └────┬─────┘
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
    ┌──────────┐ ┌──────────┐ ┌──────────┐
    │ Persona  │ │ Emotion  │ │ Memory   │
    │ Service  │ │ Service  │ │ Service  │
    └──────────┘ └──────────┘ └────┬─────┘
                                   │
                          ┌────────▼────────┐
                          │  RAG Service    │
                          │  (embedding +   │
                          │   similarity)   │
                          └────────┬────────┘
                                   │
                          ┌────────▼────────┐
                          │ Prompt Builder  │
                          │ (Pipeline)      │
                          └────────┬────────┘
                                   │
                          ┌────────▼────────┐
                          │  OpenAI SDK     │
                          │  (LLM call)     │
                          └────────┬────────┘
                                   │
                          ┌────────▼────────┐
                          │ Summary Service │
                          │ (compression)   │
                          └─────────────────┘
```

## Data Flow

```
1. User Message → FastAPI /api/v1/chat/send
2. Emotion Service 分析情绪 → 更新 emotion_state
3. RAG Service embed message → 检索相似记忆
4. Prompt Builder 组装 system_prompt
5. LLM 生成回复 → SSE stream 返回前端
6. Memory Service 提取新记忆 → 存储
7. Summary Service 检查是否需要压缩 → 生成摘要
```

## Directory Structure

```
backend/
├── main.py              # FastAPI app 启动 + lifespan
├── config.py            # Settings (DB path, API key, model)
├── database.py          # SQLAlchemy engine + session
├── api/
│   └── chat.py          # Chat routes
├── services/
│   ├── persona_service.py
│   ├── emotion_service.py
│   ├── memory_service.py
│   ├── rag_service.py
│   ├── prompt_builder.py
│   ├── summary_service.py
│   └── voice_service.py # [FUTURE] stub
├── models/
│   ├── persona.py
│   ├── memory.py
│   └── emotion.py
└── schemas/
    └── chat.py
```

## Key Decisions

| 决策 | 选择 | 原因 |
|------|------|------|
| 数据库 | SQLite | 零配置、单文件、足够 Demo 使用 |
| 向量存储 | SQLite BLOB | 避免引入 ChromaDB 等外部依赖 |
| 流式输出 | SSE | 比 WebSocket 简单，够用 |
| AI SDK | OpenAI SDK | 兼容 Gemini proxy (api.xykjy.com) |
| Embedding | all-MiniLM-L6-v2 | 384维轻量，本地运行，不需要 GPU |

## [FUTURE] Extensibility

- SQLite → PostgreSQL (只需改 connection string)
- SQLite BLOB → ChromaDB/Qdrant (替换 rag_service 实现)
- SSE → WebSocket (替换 chat route handler)
- 单体 → 拆分服务 (但 Demo 阶段不需要)
