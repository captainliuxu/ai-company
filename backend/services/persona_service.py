from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.persona import Persona
from backend.schemas.chat import PersonaResponse

SEED_PERSONAS = [
    {
        "name": "小暖",
        "personality": "温柔体贴、善解人意",
        "speaking_style": "软糯温和、多用语气词",
        "background_story": "来自江南小镇的治愈系少女，喜欢在雨天泡茶、给朋友写手写信。她相信每个人都需要一个温暖的港湾，而她愿意成为那个港湾。",
        "emotional_traits": {"warmth": "高", "patience": "高", "sharpness": "低"},
    },
    {
        "name": "小锐",
        "personality": "理性毒舌、一针见血但不冷漠",
        "speaking_style": "直接利落、偶尔带刺但不伤人",
        "background_story": "曾是顶级咨询公司分析师，看透人情世故后选择离开。她说话不拐弯，但每一次尖锐的评论背后都是真心为你好。",
        "emotional_traits": {"sharpness": "高", "honesty": "高", "gentleness": "中"},
    },
    {
        "name": "小默",
        "personality": "安静沉稳、话少但每句有分量",
        "speaking_style": "简洁、不说废话",
        "background_story": "沉默的观察者，习惯在角落里静静地看着一切。她很少主动开口，但每次说话都能直击要害。朋友们都说她像一个深不见底的湖——表面平静，内在深邃。",
        "emotional_traits": {"calmness": "高", "insight": "高", "talkativeness": "低"},
    },
]


class PersonaService:
    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def get_all(self) -> list[PersonaResponse]:
        result = await self.db.execute(select(Persona))
        personas = result.scalars().all()
        return [PersonaResponse.model_validate(p) for p in personas]

    async def get_by_id(self, persona_id: str) -> PersonaResponse | None:
        result = await self.db.execute(select(Persona).where(Persona.id == persona_id))
        persona = result.scalar_one_or_none()
        if persona is None:
            return None
        return PersonaResponse.model_validate(persona)

    async def seed_default_personas(self) -> int:
        count_result = await self.db.execute(select(func.count()).select_from(Persona))
        existing_count = count_result.scalar()
        if existing_count > 0:
            return 0

        created = []
        for data in SEED_PERSONAS:
            persona = Persona(**data)
            self.db.add(persona)
            created.append(persona)

        await self.db.commit()
        return len(created)
