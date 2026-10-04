import uuid

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class Reaction(Base, TimestampMixin):
    __tablename__ = "reactions"
    __table_args__ = (
        UniqueConstraint("user_id", "post_id", "kind", name="uq_user_post_reaction"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"),
        index=True, nullable=False,
    )
    post_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("posts.id", ondelete="CASCADE"),
        index=True, nullable=False,
    )
    kind: Mapped[str] = mapped_column(
        String(20), default="like", nullable=False
    )

    def __repr__(self) -> str:
        return f"<Reaction {self.kind} user={self.user_id[:8]} post={self.post_id[:8]}>"
