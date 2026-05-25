from datetime import datetime

from pydantic import BaseModel, field_serializer


class PersonaResponse(BaseModel):
    id: str
    name: str
    personality: str
    speaking_style: str
    background_story: str
    emotional_traits: dict
    avatar_url: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}

    @field_serializer('created_at')
    def serialize_created_at(self, dt: datetime) -> str:
        return dt.isoformat()


class PersonaListResponse(BaseModel):
    personas: list[PersonaResponse]


class SessionCreate(BaseModel):
    persona_id: str


class SessionResponse(BaseModel):
    session_id: str
    persona_id: str
    created_at: str


class ChatRequest(BaseModel):
    session_id: str
    persona_id: str
    message: str


class ChatMessage(BaseModel):
    role: str
    content: str
