import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class BotSignal(Base, TimestampMixin):
    __tablename__ = "bot_signals"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"),
        unique=True, index=True, nullable=False,
    )

    score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False, index=True)
    details: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    # list[str] of human-readable reasons
    reasons: Mapped[list] = mapped_column(JSON, default=list, nullable=False)

    # clean | suspicious | confirmed_bot | cleared
    verdict: Mapped[str] = mapped_column(
        String(20), default="clean", index=True, nullable=False
    )
    last_evaluated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    def __repr__(self) -> str:
        return f"<BotSignal user={self.user_id[:8]} score={self.score}>"