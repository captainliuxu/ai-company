# Memory Rules

## Storage Rules

- SQLite 单表 `memories`
- Embedding 存 BLOB（384维 float32）
- 每个 session 最多 200 条（超过则标记旧记忆 archived=true）
- 记忆类型严格使用 MemoryType enum

## Memory Extraction Rules

- 每轮对话后 LLM 判断是否提取新记忆
- 提取 Prompt：简洁，只返回 JSON
- 无新信息时跳过（不存空记忆）
- 一次最多提取 3 条

## RAG Recall Rules

- Top-K = 5（固定）
- Cosine similarity ≥ 0.3 才召回（低于阈值的不注入 Prompt）
- Embedding 缓存：同一文本不重复生成 embedding
- 搜索结果按 similarity 降序排列

## Constraints

- 不保存完整对话历史到 memory 表（对话历史另有 chat_history 表）
- 不 embedding 用户每条消息（只在提取出新记忆时才 embedding）
- embedding 生成用 `all-MiniLM-L6-v2`，384维

## [FUTURE]

- Memory decay（时间衰减）
- Importance auto-scoring（LLM 评分替代默认0.5）
- Hybrid retrieval（BM25 + Dense）
- 分层记忆（working/short/long/core）
- 向量数据库替换
