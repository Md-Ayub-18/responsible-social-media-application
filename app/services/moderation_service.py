from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.post import Post
from app.models.user import User


class ModerationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_queue(
        self,
        status_filter: str | None = "flagged",
        limit: int = 50,
        offset: int = 0,
    ) -> list[Post]:
        """Return posts awaiting moderator review."""
        stmt = select(Post)
        if status_filter:
            stmt = stmt.where(Post.moderation_status == status_filter)
        stmt = stmt.order_by(Post.created_at.desc()).limit(limit).offset(offset)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def override_decision(
        self,
        moderator: User,
        post_id: str,
        new_status: str,
        reason: str | None,
    ) -> Post:
        """Human moderator overrides the automated decision."""
        result = await self.db.execute(select(Post).where(Post.id == post_id))
        post = result.scalar_one_or_none()
        if not post:
            from fastapi import HTTPException
            raise HTTPException(404, "Post not found")

        old_status = post.moderation_status

        post.moderation_status = new_status
        prefix = f"[moderator:{moderator.username}]"
        post.moderation_reason = (
            f"{prefix} {reason}" if reason else f"{prefix} override to {new_status}"
        )
        await self.db.commit()
        await self.db.refresh(post)

        # audit log
        from app.services.audit_service import AuditService
        await AuditService(self.db).log(
            actor=moderator,
            action="post_override",
            target_type="post",
            target_id=post.id,
            reason=reason or f"override to {new_status}",
            details={"before": old_status, "after": new_status},
        )
        return post