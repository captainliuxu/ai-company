import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column
from backend.database import Base


class Emotion(Base):
    __tablename__ = "emotions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id: Mapped[str] = mapped_column(String(36), index=True)
    favorability: Mapped[int] = mapped_column(Integer)
    trust: Mapped[int] = mapped_column(Integer)
    mood: Mapped[str] = mapped_column(String(20))
    dependency: Mapped[int] = mapped_column(Integer)
    trigger_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
