import uuid

from sqlalchemy import JSON, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class ModerationLog(Base, TimestampMixin):
    """Append-only audit log. Never edited after creation."""

    __tablename__ = "moderation_logs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    actor_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"),
        index=True, nullable=True,
    )
    actor_username: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # what happened: post_override | report_resolved | bot_evaluated | stitch_completed
    action: Mapped[str] = mapped_column(String(40), index=True, nullable=False)

    # what was affected: post | report | user | stitch_project
    target_type: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    target_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)

    # human-readable reason
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # flexible payload for before/after state
    details: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    def __repr__(self) -> str:
        return f"<ModerationLog {self.action} on {self.target_type}:{self.target_id[:8]}>"
