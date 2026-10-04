import uuid

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class StitchProject(Base, TimestampMixin):
    __tablename__ = "stitch_projects"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    moderator_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"),
        index=True, nullable=False,
    )

    title: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    interest_slug: Mapped[str] = mapped_column(
        String(50), index=True, nullable=False
    )

    # open | in_review | stitched | cancelled
    status: Mapped[str] = mapped_column(
        String(20), default="open", index=True, nullable=False
    )
    allow_contributions: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )

    stitched_video_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    stitch_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    contributions: Mapped[list["Contribution"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="Contribution.created_at.asc()",
    )

    def __repr__(self) -> str:
        return f"<StitchProject {self.title!r} status={self.status}>"


class Contribution(Base, TimestampMixin):
    __tablename__ = "contributions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("stitch_projects.id", ondelete="CASCADE"),
        index=True, nullable=False,
    )
    contributor_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"),
        index=True, nullable=False,
    )

    video_url: Mapped[str] = mapped_column(String(500), nullable=False)
    caption: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_seconds: Mapped[float | None] = mapped_column(nullable=True)

    # hard requirement: contributor must consent
    consent_given: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # pending | approved | rejected
    status: Mapped[str] = mapped_column(
        String(20), default="pending", index=True, nullable=False
    )
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # moderator-defined order for stitching
    order_index: Mapped[int | None] = mapped_column(Integer, nullable=True)

    project: Mapped["StitchProject"] = relationship(back_populates="contributions")

    def __repr__(self) -> str:
        return f"<Contribution {self.id[:8]} status={self.status}>"
