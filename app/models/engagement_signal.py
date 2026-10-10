import uuid

from sqlalchemy import Float, ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class EngagementSignal(Base, TimestampMixin):
    """
    Stores the result of engagement manipulation analysis for a single post.

    Updated periodically (or on-demand by a moderator). One row per post.
    """

    __tablename__ = "engagement_signals"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    post_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("posts.id", ondelete="CASCADE"),
        unique=True, index=True, nullable=False,
    )

    # 0.0 (clean) → 1.0 (definitely manipulated)
    score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False, index=True)

    # clean | suspicious | manipulated
    verdict: Mapped[str] = mapped_column(
        String(20), default="clean", nullable=False, index=True
    )

    # Human-readable reasons: ["20 likes in 45 seconds", "80% new accounts"]
    reasons: Mapped[list] = mapped_column(JSON, default=list, nullable=False)

    # Raw metrics for debugging: {"total_likes": 20, "unique_likers": 20, ...}
    details: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    def __repr__(self) -> str:
        return f"<EngagementSignal post={self.post_id[:8]} score={self.score} verdict={self.verdict}>"