import json
import logging

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import AI_API_KEY, AI_BASE_URL, AI_MODEL
from backend.models.emotion import Emotion

logger = logging.getLogger(__name__)


class EmotionService:
    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def analyze_emotion(
        self, session_id: str, user_message: str, ai_reply: str
    ) -> Emotion:
        prompt = (
            f"用户消息：{user_message}\n"
            f"AI回复：{ai_reply}\n\n"
            "分析上述对话中用户的情绪状态，只输出JSON，不要输出其他内容。"
            "JSON格式：{\"favorability\":0-100,\"trust\":0-100,\"mood\":\"情绪标签\",\"dependency\":0-100}\n"
            "字段说明：favorability=好感度, trust=信任度, mood=情绪标签(如开心/难过/平静/焦虑/愤怒/期待/失望), dependency=依赖度"
        )

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
                        "max_tokens": 256,
                        "messages": [
                            {
                                "role": "system",
                                "content": "你是情绪分析助手。分析对话中用户的情绪状态，只输出JSON，不要输出任何解释或额外文字。",
                            },
                            {"role": "user", "content": prompt},
                        ],
                        "stream": False,
                    },
                )

            if response.status_code != 200:
                logger.warning(
                    "Emotion analysis AI call failed with status %s: %s",
                    response.status_code,
                    response.text,
                )
                return await self._create_fallback_emotion(session_id)

            data = response.json()
            choices = data.get("choices", [])
            if not choices:
                logger.warning("Emotion analysis returned no choices")
                return await self._create_fallback_emotion(session_id)

            raw_content = choices[0].get("message", {}).get("content", "")
            parsed = self._parse_emotion_json(raw_content)

            emotion = Emotion(
                session_id=session_id,
                favorability=parsed["favorability"],
                trust=parsed["trust"],
                mood=parsed["mood"],
                dependency=parsed["dependency"],
                trigger_message=user_message[:500],
            )
            self.db.add(emotion)
            await self.db.commit()
            await self.db.refresh(emotion)
            return emotion

        except Exception as exc:
            logger.warning("Emotion analysis failed with exception: %s", exc)
            return await self._create_fallback_emotion(session_id)

    async def get_current_state(self, session_id: str) -> Emotion | None:
        result = await self.db.execute(
            select(Emotion)
            .where(Emotion.session_id == session_id)
            .order_by(Emotion.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_history(self, session_id: str) -> list[Emotion]:
        result = await self.db.execute(
            select(Emotion)
            .where(Emotion.session_id == session_id)
            .order_by(Emotion.created_at.asc())
        )
        return list(result.scalars().all())

    def _parse_emotion_json(self, raw: str) -> dict:
        raw = raw.strip()

        # Try extracting JSON block if wrapped in markdown fences
        if raw.startswith("```"):
            lines = raw.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            raw = "\n".join(lines).strip()

        # Find the outermost { ... }
        start = raw.find("{")
        end = raw.rfind("}")
        if start != -1 and end != -1 and end > start:
            raw = raw[start : end + 1]

        parsed = json.loads(raw)

        favorability = max(0, min(100, int(parsed.get("favorability", 50))))
        trust = max(0, min(100, int(parsed.get("trust", 50))))
        mood = str(parsed.get("mood", "平静"))[:20]
        dependency = max(0, min(100, int(parsed.get("dependency", 50))))

        return {
            "favorability": favorability,
            "trust": trust,
            "mood": mood,
            "dependency": dependency,
        }

    async def _create_fallback_emotion(self, session_id: str) -> Emotion:
        emotion = Emotion(
            session_id=session_id,
            favorability=50,
            trust=50,
            mood="平静",
            dependency=50,
        )
        self.db.add(emotion)
        await self.db.commit()
        await self.db.refresh(emotion)
        return emotion
