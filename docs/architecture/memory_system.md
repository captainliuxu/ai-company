# Memory System Design

## Overview

轻量级长期记忆系统。用户消息经过 embedding → 存储 → 召回 → 拼入 Prompt。

不是企业级 RAG 平台。

## Memory Model

```python
class Memory:
    id: UUID
    session_id: str        # 会话ID
    user_id: str           # 用户标识
    type: MemoryType       # user_info | preference | event | emotion
    content: str           # 记忆文本
    embedding: bytes       # 384维向量 (BLOB)
    importance: float      # 重要性 0-1 [FUTURE: 自动化评分]
    created_at: datetime
    updated_at: datetime
```

## Memory Types

| Type | Example | Source |
|------|---------|--------|
| user_info | "我叫小王" | 用户直接陈述 |
| user_preference | "喜欢下雨天" | 对话中提取 |
| relationship_event | "今天是第3次聊天" | 系统生成 |
| emotional_event | "今天升职了很开心" | Emotion Service 标记 |

## Memory Pipeline

```
After each user-AI turn:
  1. LLM checks: "Is there new info worth remembering?"
  2. If yes → extract content + type
  3. Generate embedding via sentence-transformers
  4. Store (content + embedding) to SQLite
  5. No action if nothing new
```

## RAG Recall

```
On each user message:
  1. Embed user message → query_vector (384d)
  2. Load all memory embeddings for this session
  3. Cosine similarity: query_vector vs all memory vectors
  4. Top-K (K=5) most similar memories
  5. Inject into Prompt Builder → Memory Block
```

## Similarity Search (numpy)

```python
def search_similar(query_embedding, memory_embeddings, top_k=5):
    similarities = cosine_similarity(query_embedding, memory_embeddings)
    top_indices = np.argsort(similarities)[-top_k:][::-1]
    return [(memory, score) for memory, score in ...]
```

## Storage

SQLite 单表，embedding 存为 BLOB：

```sql
CREATE TABLE memories (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    user_id TEXT NOT NULL DEFAULT 'default',
    type TEXT NOT NULL,
    content TEXT NOT NULL,
    embedding BLOB,
    importance REAL DEFAULT 0.5,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Constraints

- 每个 session 最多保留 200 条记忆（超过则归档旧记忆）
- RAG 每次最多召回 5 条
- embedding 缓存避免重复计算

## [FUTURE] Advanced Memory

### 向量数据库替换
- ChromaDB / Qdrant / pgvector
- 替换 rag_service 的存储层

### 混合检索
- BM25 关键词 + Dense Embedding
- 融合排序

### 记忆衰减
- 时间衰减因子 (exponential decay)
- 近期记忆权重 > 远期记忆

### 记忆重要性
- LLM 自动评分替代默认0.5
- 重要事件永不衰减

### 分层记忆
- Working Memory (当前对话)
- Short-term Memory (最近7天)
- Long-term Memory (7天以上)
- Core Memory (永远保留的关键信息)
