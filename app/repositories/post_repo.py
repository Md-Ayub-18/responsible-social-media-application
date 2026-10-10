from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.post import Post


class PostRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, post: Post) -> Post:
        self.db.add(post)
        await self.db.commit()
        await self.db.refresh(post)
        return post

    async def get(self, post_id: str) -> Post | None:
        result = await self.db.execute(
            select(Post).where(Post.id == post_id)
        )
        return result.scalar_one_or_none()

    async def get_with_author(self, post_id: str) -> Post | None:
        result = await self.db.execute(
            select(Post)
            .options(selectinload(Post.author) if hasattr(Post, "author") else None)
            .where(Post.id == post_id)
        )
        return result.scalar_one_or_none()

    async def list_by_interest_slugs(
        self,
        interest_slugs: list[str],
        limit: int = 50,
        offset: int = 0,
        include_flagged: bool = False,
        for_user_id: str | None = None,
        viewer_id: str | None = None,
        allowed_private_author_ids: set[str] | None = None,
        blocked_ids: set[str] | None = None,
    ) -> list[Post]:
        if not interest_slugs:
            return []

        stmt = (
            select(Post)
            .where(Post.interest_slug.in_(interest_slugs))
            .where(Post.is_hidden.is_(False))
            .where(Post.community_id.is_(None))
        )

                # Visibility filter:
        if for_user_id:
            stmt = stmt.where(
                or_(
                    Post.moderation_status == "approved",
                    Post.author_id == for_user_id,
                )
            )
            # Media visibility: flagged media visible only to author
            stmt = stmt.where(
                or_(
                    Post.media_moderation_status.in_(("approved", "pending")),
                    Post.author_id == for_user_id,
                )
            )
        elif not include_flagged:
            stmt = stmt.where(Post.moderation_status == "approved")
            # Hide flagged/removed media from anonymous viewers
            stmt = stmt.where(Post.media_moderation_status == "approved")

        # Audience filter:
        #   - public posts: visible to all
        #   - private posts: visible only to the author + their followers
        #     (we pass in allowed_private_author_ids = IDs the viewer may see)
        if for_user_id is not None:
            allowed = allowed_private_author_ids or set()
            allowed_with_self = allowed | {for_user_id}
            stmt = stmt.where(
                or_(
                    Post.audience == "public",
                    Post.author_id.in_(allowed_with_self),
                )
            )
        else:
            # Anonymous viewer (rare) → only public
            stmt = stmt.where(Post.audience == "public")

        # Block filter: exclude anything authored by a blocked/blocking user
        if blocked_ids:
            stmt = stmt.where(~Post.author_id.in_(blocked_ids))

        stmt = stmt.order_by(Post.created_at.desc()).limit(limit).offset(offset)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def list_by_author(
        self, author_id: str, limit: int = 50, offset: int = 0
    ) -> list[Post]:
        stmt = (
            select(Post)
            .where(Post.author_id == author_id)
            .order_by(Post.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def delete(self, post: Post) -> None:
        await self.db.delete(post)
        await self.db.commit()



    async def count_recent_posts_by_author(self, author_id: str, minutes: int = 60) -> int:
        """Count posts by this author in the last N minutes."""
        from datetime import datetime, timedelta, timezone
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=minutes)
        stmt = (
            select(func.count())
            .select_from(Post)
            .where(Post.author_id == author_id)
            .where(Post.created_at >= cutoff)
        )
        return (await self.db.execute(stmt)).scalar_one()

    async def count_all_posts_by_author(self, author_id: str) -> int:
        """Total posts by this author."""
        stmt = (
            select(func.count())
            .select_from(Post)
            .where(Post.author_id == author_id)
        )
        return (await self.db.execute(stmt)).scalar_one()
