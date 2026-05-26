"""Memory service — long-term memory extraction and storage."""

import json
import logging

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import AI_API_KEY, AI_BASE_URL, AI_MODEL
from backend.models.memory import Memory

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
