import uuid

from sqlalchemy import JSON, Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class FocusMode(Base, TimestampMixin):
    __tablename__ = "focus_modes"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"),
        index=True, nullable=False,
    )
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    emoji: Mapped[str | None] = mapped_column(String(10), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # List of interest slugs, e.g. ["learning", "technology"]
    interest_slugs: Mapped[list[str]] = mapped_column(
        JSON, default=list, nullable=False
    )

    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_child_safe: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    def __repr__(self) -> str:
        return f"<FocusMode {self.name} user={self.user_id}>"
