from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.post import Post
from app.models.user import User
from sqlalchemy import or_, select


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
    ) -> list[Post]:
        if not interest_slugs:
            return []

        stmt = (
            select(Post)
            .where(Post.interest_slug.in_(interest_slugs))
            .where(Post.is_hidden.is_(False))
        )

        # Approved posts are visible to everyone. Flagged posts are visible
        # to their author only, so the user can see what happened to their
        # own content.
        if for_user_id:
            stmt = stmt.where(
                or_(
                    Post.moderation_status == "approved",
                    Post.author_id == for_user_id,
                )
            )
        elif not include_flagged:
            stmt = stmt.where(Post.moderation_status == "approved")

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