import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Integer, DateTime, LargeBinary
from sqlalchemy.orm import Mapped, mapped_column
from backend.database import Base


class Memory(Base):
    __tablename__ = "memories"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id: Mapped[str] = mapped_column(String(36), index=True)
    user_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    type: Mapped[str] = mapped_column(String(20))
    content: Mapped[str] = mapped_column(String(1000))
    importance: Mapped[int] = mapped_column(Integer, default=3)
    embedding: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
