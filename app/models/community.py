import uuid

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class Community(Base, TimestampMixin):
    """A named interest-based space where users gather and post."""

    __tablename__ = "communities"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    slug: Mapped[str] = mapped_column(
        String(60), unique=True, index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    emoji: Mapped[str | None] = mapped_column(String(10), nullable=True)

    # The interest this community is about (learning, sports, etc.)
    interest_slug: Mapped[str] = mapped_column(
        String(50), index=True, nullable=False
    )

    # The user who created the community — becomes its moderator
    creator_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"),
        index=True, nullable=False,
    )

    is_public: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    member_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    members: Mapped[list["CommunityMember"]] = relationship(
        back_populates="community",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Community {self.slug} ({self.member_count} members)>"


class CommunityMember(Base, TimestampMixin):
    """Join table — which users belong to which communities."""

    __tablename__ = "community_members"
    __table_args__ = (
        UniqueConstraint("user_id", "community_id", name="uq_user_community"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"),
        index=True, nullable=False,
    )
    community_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("communities.id", ondelete="CASCADE"),
        index=True, nullable=False,
    )

    # "member" | "moderator" (the creator starts as moderator)
    role: Mapped[str] = mapped_column(
        String(20), default="member", nullable=False
    )

    community: Mapped["Community"] = relationship(back_populates="members")

    def __repr__(self) -> str:
        return f"<CommunityMember user={self.user_id[:8]} community={self.community_id[:8]} role={self.role}>"
