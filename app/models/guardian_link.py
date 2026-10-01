import uuid

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class GuardianLink(Base, TimestampMixin):
    """Links a guardian (parent/legal guardian) to a child account."""

    __tablename__ = "guardian_links"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    guardian_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"),
        index=True, nullable=False,
    )
    child_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"),
        unique=True, index=True, nullable=False,   # one guardian per child
    )

    can_view_posts: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    can_restrict_dms: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    can_manage_focus: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    def __repr__(self) -> str:
        return f"<GuardianLink g={self.guardian_id[:8]} c={self.child_id[:8]}>"