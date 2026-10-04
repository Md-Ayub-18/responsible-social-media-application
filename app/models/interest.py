import uuid

from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class Interest(Base, TimestampMixin):
    __tablename__ = "interests"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    slug: Mapped[str] = mapped_column(
        String(50), unique=True, index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    emoji: Mapped[str | None] = mapped_column(String(10), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    user_links: Mapped[list["UserInterest"]] = relationship(
        back_populates="interest", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Interest {self.slug}>"


class UserInterest(Base):
    """Join table: which interests a user has selected."""

    __tablename__ = "user_interests"
    __table_args__ = (
        UniqueConstraint("user_id", "interest_id", name="uq_user_interest"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    interest_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("interests.id", ondelete="CASCADE"), index=True, nullable=False
    )

    interest: Mapped["Interest"] = relationship(back_populates="user_links")
