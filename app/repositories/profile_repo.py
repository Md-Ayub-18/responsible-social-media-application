from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.post import Post
from app.models.reaction import Reaction
from app.models.user import User


class ProfileRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_by_username(self, username: str) -> User | None:
        result = await self.db.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()

    async def count_user_posts(self, user_id: str) -> int:
        result = await self.db.execute(
            select(func.count()).select_from(Post).where(Post.author_id == user_id)
        )
        return result.scalar_one()

    async def count_likes_received(self, user_id: str) -> int:
        """Total likes across all of this user's posts."""
        result = await self.db.execute(
            select(func.count())
            .select_from(Reaction)
            .join(Post, Post.id == Reaction.post_id)
            .where(Post.author_id == user_id)
        )
        return result.scalar_one()

    async def list_user_posts(
        self, user_id: str, limit: int = 30, offset: int = 0
    ) -> list[Post]:
        stmt = (
            select(Post)
            .where(Post.author_id == user_id)
            .where(Post.is_hidden.is_(False))
            .order_by(Post.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
