from sqlalchemy import delete, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.block import Block
from app.models.follow import Follow


class SocialRepository:
    """
    Repository for follow and block relationships.

    These are the two core primitives of the social graph:
      - Follow: one-way, enables feed discovery and private-post visibility
      - Block: two-way enforcement, hides content + prevents interaction
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    # ---------- follows ----------
    async def get_follow(self, follower_id: str, following_id: str) -> Follow | None:
        result = await self.db.execute(
            select(Follow).where(
                Follow.follower_id == follower_id,
                Follow.following_id == following_id,
            )
        )
        return result.scalar_one_or_none()

    async def add_follow(self, follower_id: str, following_id: str) -> Follow:
        f = Follow(follower_id=follower_id, following_id=following_id)
        self.db.add(f)
        await self.db.commit()
        await self.db.refresh(f)
        return f

    async def remove_follow(self, follower_id: str, following_id: str) -> bool:
        result = await self.db.execute(
            delete(Follow).where(
                Follow.follower_id == follower_id,
                Follow.following_id == following_id,
            )
        )
        await self.db.commit()
        return result.rowcount > 0

    async def is_following(self, follower_id: str, following_id: str) -> bool:
        f = await self.get_follow(follower_id, following_id)
        return f is not None

    async def following_ids(self, user_id: str) -> set[str]:
        """IDs of users this user follows."""
        result = await self.db.execute(
            select(Follow.following_id).where(Follow.follower_id == user_id)
        )
        return {row[0] for row in result.all()}

    async def follower_ids(self, user_id: str) -> set[str]:
        """IDs of users who follow this user."""
        result = await self.db.execute(
            select(Follow.follower_id).where(Follow.following_id == user_id)
        )
        return {row[0] for row in result.all()}

    async def count_followers(self, user_id: str) -> int:
        result = await self.db.execute(
            select(Follow).where(Follow.following_id == user_id)
        )
        return len(list(result.scalars().all()))

    async def count_following(self, user_id: str) -> int:
        result = await self.db.execute(
            select(Follow).where(Follow.follower_id == user_id)
        )
        return len(list(result.scalars().all()))

    # ---------- blocks ----------
    async def get_block(self, blocker_id: str, blocked_id: str) -> Block | None:
        result = await self.db.execute(
            select(Block).where(
                Block.blocker_id == blocker_id,
                Block.blocked_id == blocked_id,
            )
        )
        return result.scalar_one_or_none()

    async def add_block(self, blocker_id: str, blocked_id: str) -> Block:
        b = Block(blocker_id=blocker_id, blocked_id=blocked_id)
        self.db.add(b)
        await self.db.commit()
        await self.db.refresh(b)
        return b

    async def remove_block(self, blocker_id: str, blocked_id: str) -> bool:
        result = await self.db.execute(
            delete(Block).where(
                Block.blocker_id == blocker_id,
                Block.blocked_id == blocked_id,
            )
        )
        await self.db.commit()
        return result.rowcount > 0

    async def is_blocked(self, user_a: str, user_b: str) -> bool:
        """True if EITHER user has blocked the other (mutual invisibility)."""
        result = await self.db.execute(
            select(Block).where(
                or_(
                    (Block.blocker_id == user_a) & (Block.blocked_id == user_b),
                    (Block.blocker_id == user_b) & (Block.blocked_id == user_a),
                )
            )
        )
        return result.scalar_one_or_none() is not None

    async def blocked_ids(self, user_id: str) -> set[str]:
        """
        All user IDs this user has blocked OR who have blocked this user.
        Because blocks are mutual, both directions matter.
        """
        result = await self.db.execute(
            select(Block).where(
                or_(Block.blocker_id == user_id, Block.blocked_id == user_id)
            )
        )
        blocks = list(result.scalars().all())
        blocked = set()
        for b in blocks:
            other = b.blocked_id if b.blocker_id == user_id else b.blocker_id
            blocked.add(other)
        return blocked

    async def list_blocked_by_user(self, user_id: str) -> list[Block]:
        """Blocks this user has initiated (for the settings page)."""
        result = await self.db.execute(
            select(Block).where(Block.blocker_id == user_id)
        )
        return list(result.scalars().all())
