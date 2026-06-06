"""Memory service — long-term memory extraction and storage."""

import json
import logging
import math
from datetime import datetime, timezone

import httpx
import numpy as np
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import (
    AI_API_KEY,
    AI_BASE_URL,
    AI_MODEL,
    MEMORY_MAX_EMOTION_RESULTS,
    MEMORY_MAX_SUMMARY_RESULTS,
    MEMORY_RECENCY_HALFLIFE_DAYS,
    MEMORY_SEARCH_TOP_K,
    MEMORY_SEMANTIC_THRESHOLD,
    MEMORY_TYPE_WEIGHT_EMOTION,
    MEMORY_TYPE_WEIGHT_EVENT,
    MEMORY_TYPE_WEIGHT_PREFERENCE,
    MEMORY_TYPE_WEIGHT_SUMMARY,
    MEMORY_TYPE_WEIGHT_USER_INFO,
    MEMORY_WEIGHT_IMPORTANCE,
    MEMORY_WEIGHT_RECENCY,
    MEMORY_WEIGHT_SEMANTIC,
    MEMORY_WEIGHT_TYPE,
)
from backend.models.memory import Memory
from backend.services.rag_service import RAGService

logger = logging.getLogger(__name__)

MEMORY_EXTRACTION_SYSTEM_PROMPT = """你是信息提取助手。从对话中提取值得长期记住的用户信息。只输出JSON数组。

提取规则：
- type 只能是: user_info, preference, event, emotion
- user_info: 用户的基本信息（姓名、年龄、职业、地点等）
- preference: 用户的偏好、喜好、习惯
- event: 用户提到的重要事件、经历
- emotion: 用户表达的情绪状态、感受
- importance: 1-5，1=一般信息，5=非常重要
- 每条 content 要简洁但完整，能独立理解
- 如果没有值得记住的信息，输出空数组 []"""


class MemoryService:
    """Manages long-term memory storage and AI-driven extraction."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._rag_service = None

    def _get_rag_service(self):
        """Lazily create a RAGService instance.

        RAGService loads a ~90 MB embedding model. Deferring creation until the
        first embed / search call prevents MemoryService construction from
        failing the entire /chat/send endpoint when the model is unavailable.
        """
        if self._rag_service is None:
            self._rag_service = RAGService()
        return self._rag_service

    def _get_search_weights(self) -> dict[str, float]:
        """Return hybrid search weights from application config."""
        return {
            "semantic": float(MEMORY_WEIGHT_SEMANTIC),
            "importance": float(MEMORY_WEIGHT_IMPORTANCE),
            "recency": float(MEMORY_WEIGHT_RECENCY),
            "type_weight": float(MEMORY_WEIGHT_TYPE),
        }

    def _get_type_weights(self) -> dict[str, float]:
        """Return per-memory-type ranking weights from application config."""
        return {
            "user_info": float(MEMORY_TYPE_WEIGHT_USER_INFO),
            "preference": float(MEMORY_TYPE_WEIGHT_PREFERENCE),
            "event": float(MEMORY_TYPE_WEIGHT_EVENT),
            "emotion": float(MEMORY_TYPE_WEIGHT_EMOTION),
            "summary": float(MEMORY_TYPE_WEIGHT_SUMMARY),
        }

    def _get_type_result_caps(self) -> dict[str, int]:
        """Return per-memory-type result caps from application config."""
        return {
            "summary": int(MEMORY_MAX_SUMMARY_RESULTS),
            "emotion": int(MEMORY_MAX_EMOTION_RESULTS),
        }

    async def extract_from_conversation(
        self, user_message: str, ai_reply: str
    ) -> list[dict]:
        """Call AI to extract memory-worthy information from a conversation turn.

        Returns a list of dicts with keys: type, content, importance.
        Does NOT save to database — caller must call add_memory() for each.
        """
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
                response = await client.post(
                    f"{AI_BASE_URL}/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {AI_API_KEY}",
                        "content-type": "application/json",
                    },
                    json={
                        "model": AI_MODEL,
                        "max_tokens": 512,
                        "messages": [
                            {"role": "system", "content": MEMORY_EXTRACTION_SYSTEM_PROMPT},
                            {
                                "role": "user",
                                "content": (
                                    f"用户消息：{user_message}\n"
                                    f"AI回复：{ai_reply}\n\n"
                                    "提取值得长期记住的信息。输出JSON数组："
                                    '[{"type":"user_info|preference|event|emotion","content":"...","importance":1-5}]。'
                                    "如果没有值得记住的，输出空数组[]。"
                                ),
                            },
                        ],
                        "stream": False,
                    },
                )
                response.raise_for_status()
        except httpx.HTTPError as exc:
            logger.error("AI memory extraction HTTP error: %s", exc)
            return []
        except Exception as exc:
            logger.error("AI memory extraction unexpected error: %s", exc)
            return []

        try:
            data = response.json()
            raw_text = data["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError, TypeError) as exc:
            logger.error("Failed to parse AI response structure: %s", exc)
            return []

        return _parse_memory_json(raw_text)

    async def add_memory(
        self, session_id: str, type: str, content: str, importance: int = 3
    ) -> Memory:
        """Create and persist a single Memory record."""
        if importance < 1:
            importance = 1
        elif importance > 5:
            importance = 5

        memory = Memory(
            session_id=session_id,
            type=type,
            content=content,
            importance=importance,
        )

        # Generate embedding for semantic search (lazy RAGService init)
        try:
            rag = self._get_rag_service()
            embedding_list = rag.encode(content)
            memory.embedding = np.array(embedding_list, dtype=np.float32).tobytes()
        except Exception as exc:
            logger.warning("Failed to generate embedding for memory: %s", exc)

        self.db.add(memory)
        await self.db.commit()
        await self.db.refresh(memory)
        return memory

    async def get_by_session(self, session_id: str) -> list[Memory]:
        """Return all memories for a session, newest first."""
        result = await self.db.execute(
            select(Memory)
            .where(Memory.session_id == session_id)
            .order_by(Memory.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_type(self, session_id: str, memory_type: str) -> list[Memory]:
        """Return memories for a session filtered by type, newest first."""
        result = await self.db.execute(
            select(Memory)
            .where(Memory.session_id == session_id, Memory.type == memory_type)
            .order_by(Memory.created_at.desc())
        )
        return list(result.scalars().all())

    async def search_memories(
        self,
        session_id: str,
        query: str,
        top_k: int = MEMORY_SEARCH_TOP_K,
        return_debug_scores: bool = False,
    ) -> list[Memory] | list[dict]:
        """Hybrid search over memories for a session using semantic + heuristics.

        Falls back to keyword-based filtering if RAGService is unavailable or
        no embeddings exist. When ``return_debug_scores`` is True, returns
        scored payloads instead of bare Memory objects for internal debugging.
        """
        all_memories = await self.get_by_session(session_id)
        memories_with_embeddings = [m for m in all_memories if m.embedding is not None]

        if not memories_with_embeddings:
            logger.debug(
                "No embedded memories found for session %s; returning empty result.",
                session_id,
            )
            return []

        try:
            rag = self._get_rag_service()
            query_vec = np.array(rag.encode(query), dtype=np.float32)
            if not np.any(query_vec):
                logger.debug(
                    "Query embedding is zero-vector for session %s; returning empty result.",
                    session_id,
                )
                return []

            scored = []
            search_weights = self._get_search_weights()
            type_weights = self._get_type_weights()
            for memory in memories_with_embeddings:
                hybrid_score = self._score_memory_candidate(
                    memory=memory,
                    query_vec=query_vec,
                    search_weights=search_weights,
                    type_weights=type_weights,
                    return_debug_scores=return_debug_scores,
                )
                if hybrid_score is None:
                    continue
                scored.append(hybrid_score)

            ranked_memories = self._select_ranked_memories(scored, top_k=top_k)
            if return_debug_scores:
                return ranked_memories
            return [item["memory"] for item in ranked_memories]
        except Exception as exc:
            logger.warning(
                "RAG search failed for session %s (degrading to keyword match): %s",
                session_id,
                exc,
            )
            # Degrade to simple keyword-based filtering
            query_lower = query.lower()
            matched = []
            for mem in memories_with_embeddings:
                if query_lower in mem.content.lower():
                    matched.append(mem)
            return matched[:top_k]

    def _score_memory_candidate(
        self,
        memory: Memory,
        query_vec: np.ndarray,
        search_weights: dict[str, float],
        type_weights: dict[str, float],
        return_debug_scores: bool = False,
    ) -> dict | None:
        """Return hybrid score payload for a memory, or None if it is filtered out."""
        try:
            mem_vec = np.frombuffer(memory.embedding, dtype=np.float32)
        except (ValueError, TypeError) as exc:
            logger.warning(
                "Failed to deserialize embedding for memory %s: %s",
                getattr(memory, "id", "?"),
                exc,
            )
            return None

        if mem_vec.shape != query_vec.shape:
            logger.warning(
                "Memory %s has embedding dim %d, expected %d; skipping.",
                getattr(memory, "id", "?"),
                mem_vec.shape[0],
                query_vec.shape[0],
            )
            return None

        semantic_score = self._cosine_similarity(query_vec, mem_vec)
        semantic_threshold = float(MEMORY_SEMANTIC_THRESHOLD)
        if semantic_score < semantic_threshold:
            return None

        importance_score = max(0.0, min(float(memory.importance) / 5.0, 1.0))
        recency_score = self._calculate_recency_score(memory.created_at)
        type_score = type_weights.get(memory.type, 0.75)

        hybrid_score = (
            semantic_score * search_weights["semantic"]
            + importance_score * search_weights["importance"]
            + recency_score * search_weights["recency"]
            + type_score * search_weights["type_weight"]
        )

        payload = {
            "memory": memory,
            "hybrid_score": hybrid_score,
            "semantic_score": semantic_score,
            "importance_score": importance_score,
            "recency_score": recency_score,
            "type_score": type_score,
        }

        if return_debug_scores:
            payload["weights"] = search_weights.copy()
            payload["thresholds"] = {
                "semantic": semantic_threshold,
                "recency_halflife_days": float(MEMORY_RECENCY_HALFLIFE_DAYS),
            }
            payload["type_weights"] = type_weights.copy()
            payload["type_caps"] = self._get_type_result_caps()

        return payload

    def _select_ranked_memories(
        self, scored_memories: list[dict], top_k: int
    ) -> list[dict]:
        """Apply final sorting and per-type caps to scored memories."""
        ranked = sorted(
            scored_memories,
            key=lambda item: (
                item["hybrid_score"],
                item["semantic_score"],
                item["importance_score"],
                item["recency_score"],
            ),
            reverse=True,
        )

        selected = []
        type_counts: dict[str, int] = {}
        type_caps = self._get_type_result_caps()

        for item in ranked:
            memory_type = item["memory"].type
            max_allowed = type_caps.get(memory_type)
            current_count = type_counts.get(memory_type, 0)

            if max_allowed is not None and current_count >= max_allowed:
                continue

            selected.append(item)
            type_counts[memory_type] = current_count + 1

            if len(selected) >= top_k:
                break

        return selected

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Compute cosine similarity between two numpy arrays."""
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))

    def _calculate_recency_score(self, created_at: datetime | None) -> float:
        """Convert age to a 0-1 score using the configured half-life."""
        if created_at is None:
            return 0.0

        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)

        now = datetime.now(timezone.utc)
        age_seconds = max((now - created_at).total_seconds(), 0.0)
        age_days = age_seconds / 86400.0
        return math.pow(0.5, age_days / float(MEMORY_RECENCY_HALFLIFE_DAYS))


def _parse_memory_json(raw_text: str) -> list[dict]:
    """Parse AI response text into a list of memory dicts.

    Handles markdown code fences, trailing commas, and other common LLM quirks.
    Returns an empty list on any parse failure.
    """
    text = raw_text.strip()

    # Strip markdown code fences if present
    if text.startswith("```"):
        # Remove opening fence line
        newline_idx = text.find("\n")
        if newline_idx != -1:
            text = text[newline_idx + 1:]
        # Remove closing fence
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

    # Try direct JSON parse
    try:
        parsed = json.loads(text)
        if isinstance(parsed, list):
            return _validate_memories(parsed)
        return []
    except json.JSONDecodeError:
        pass

    # Try to extract JSON array from text (fallback for extra text around JSON)
    try:
        start = text.find("[")
        end = text.rfind("]")
        if start != -1 and end != -1 and end > start:
            parsed = json.loads(text[start:end + 1])
            if isinstance(parsed, list):
                return _validate_memories(parsed)
    except json.JSONDecodeError:
        pass

    logger.warning("Could not parse memory JSON from AI response: %s", raw_text[:200])
    return []


def _validate_memories(raw_items: list) -> list[dict]:
    """Filter and validate raw memory dicts from AI output."""
    valid_types = {"user_info", "preference", "event", "emotion"}
    cleaned = []

    for item in raw_items:
        if not isinstance(item, dict):
            continue
        mem_type = str(item.get("type", "")).strip().lower()
        content = str(item.get("content", "")).strip()
        if mem_type not in valid_types or not content:
            continue
        importance = int(item.get("importance", 3))
        importance = max(1, min(5, importance))
        cleaned.append({
            "type": mem_type,
            "content": content,
            "importance": importance,
        })

    return cleaned
