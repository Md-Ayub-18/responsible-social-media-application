import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class ScreenSession(Base, TimestampMixin):
    """
    One row per continuous browsing session for a user.

    A "session" starts on first heartbeat and ends when the user
    closes the tab (or after N minutes of no heartbeat).

    Sessions are grouped by day on the frontend to compute daily totals.
    """

    __tablename__ = "screen_sessions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"),
        index=True, nullable=False,
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    last_heartbeat_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Total seconds logged in this session (updated by heartbeat)
    duration_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    def __repr__(self) -> str:
        return f"<ScreenSession user={self.user_id[:8]} dur={self.duration_seconds}s>"
