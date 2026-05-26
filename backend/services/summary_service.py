"""Conversation summary service — compress long conversations."""

import logging

import httpx

from backend.config import AI_API_KEY, AI_BASE_URL, AI_MODEL, SUMMARY_TRIGGER_ROUNDS

logger = logging.getLogger(__name__)

SUMMARY_SYSTEM_PROMPT = """你是对话摘要助手。用中文总结以下对话的关键信息。
总结要点：
1. 用户近况（最近在做什么、状态如何）
2. 情绪变化（情绪轨迹，从什么变为什么）
3. 关系变化（好感度、信任度、依赖度的变化）
4. 重要事件或信息（用户提到的关键信息）

保持简洁。"""


class SummaryService:
    """Compress long conversations by generating AI-powered summaries."""

    def __init__(self, db_session=None):
        self.db = db_session

    async def should_summarize(self, messages: list) -> bool:
        """Check whether the conversation exceeds the summary trigger threshold.

        Counts user/assistant turn pairs. Returns True when the count meets
        or exceeds SUMMARY_TRIGGER_ROUNDS.
        """
        if not messages:
            return False

        user_messages = [m for m in messages if m.get("role") == "user"]
        return len(user_messages) >= SUMMARY_TRIGGER_ROUNDS

    async def generate_summary(self, messages: list) -> str:
        """Generate a concise Chinese summary of the conversation.

        Sends the last 40 messages to the AI API and returns a summary
        string covering user status, emotion changes, relationship
        dynamics, and key events. Returns an empty string on any failure.
        """
        if not messages:
            return ""

        recent = messages[-40:]
        conversation_text = self._format_conversation(recent)

        if not conversation_text.strip():
            return ""

        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
                response = await client.post(
                    f"{AI_BASE_URL}/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {AI_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": AI_MODEL,
                        "max_tokens": 1024,
                        "messages": [
                            {"role": "system", "content": SUMMARY_SYSTEM_PROMPT},
                            {"role": "user", "content": f"请总结以下对话：\n\n{conversation_text}"},
                        ],
                        "stream": False,
                    },
                )

            if response.status_code != 200:
                logger.warning(
                    "Summary generation AI call failed with status %s: %s",
                    response.status_code,
                    response.text[:200],
                )
                return ""

            data = response.json()
            choices = data.get("choices", [])
            if not choices:
                logger.warning("Summary generation returned no choices")
                return ""

            content = choices[0].get("message", {}).get("content", "")
            return content.strip() if content else ""

        except Exception as exc:
            logger.warning("Summary generation failed with exception: %s", exc)
            return ""

    def apply_summary(self, messages: list, summary: str) -> list:
        """Replace old messages with a summary context plus the most recent messages.

        Creates a system-level summary message and keeps only the last 5
        messages after it. Returns the new compressed message list.
        """
        if not summary:
            return messages

        summary_msg = {
            "role": "system",
            "content": f"[对话摘要] {summary}",
        }

        last_messages = messages[-5:] if len(messages) > 5 else messages
        return [summary_msg] + last_messages

    def _format_conversation(self, messages: list) -> str:
        """Convert message list into a readable conversation text block."""
        lines = []
        for m in messages:
            role = m.get("role", "")
            content = m.get("content", "")
            if role == "user":
                lines.append(f"用户：{content}")
            elif role == "assistant":
                lines.append(f"AI：{content}")
            elif role == "system":
                lines.append(f"[系统]：{content}")
        return "\n".join(lines)
