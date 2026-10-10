import uuid

from sqlalchemy import JSON, Boolean, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class Post(Base, TimestampMixin):
    __tablename__ = "posts"
    __table_args__ = (
        Index("ix_posts_interest_created", "interest_slug", "created_at"),
        Index("ix_posts_community_created", "community_id", "created_at"),
        Index("ix_posts_audience_created", "audience", "created_at"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    author_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"),
        index=True, nullable=False,
    )

    # If set, post belongs to a specific community; if null, it's a feed post.
    community_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("communities.id", ondelete="SET NULL"),
        index=True, nullable=True,
    )

    # Post visibility:
    #   "public"  → visible to anyone with matching interests
    #   "private" → visible only to the author and their followers
    audience: Mapped[str] = mapped_column(
        String(20), default="public", index=True, nullable=False
    )

    text: Mapped[str] = mapped_column(Text, nullable=False)
    interest_slug: Mapped[str] = mapped_column(
        String(50), index=True, nullable=False
    )
    media_urls: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)

    # --- text moderation ---
    # pending | approved | flagged | removed
    moderation_status: Mapped[str] = mapped_column(
        String(20), default="pending", index=True, nullable=False
    )
    moderation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # --- AI detection ---
    ai_generated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    ai_label_shown: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # --- media (image/video) moderation ---
    # pending | approved | flagged | removed
    media_moderation_status: Mapped[str] = mapped_column(
        String(20), default="pending", index=True, nullable=False
    )
    media_moderation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    is_hidden: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    def __repr__(self) -> str:
        return f"<Post {self.id[:8]} interest={self.interest_slug} audience={self.audience}>"
