from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.social_repo import SocialRepository
from app.repositories.user_repo import UserRepository


class SocialService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = SocialRepository(db)
        self.users = UserRepository(db)

    # ---------- follows ----------
    async def follow(self, follower: User, target_username: str) -> dict:
        target = await self.users.get_by_username(target_username)
        if not target:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")

        if target.id == follower.id:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST, "You cannot follow yourself"
            )

        # Blocked users cannot follow each other
        if await self.repo.is_blocked(follower.id, target.id):
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                "You cannot follow this user",
            )

        existing = await self.repo.get_follow(follower.id, target.id)
        if existing:
            raise HTTPException(
                status.HTTP_409_CONFLICT, "You already follow this user"
            )

        await self.repo.add_follow(follower.id, target.id)
        followers = await self.repo.count_followers(target.id)

        return {
            "user_id": target.id,
            "username": target.username,
            "is_following": True,
            "follower_count": followers,
        }

    async def unfollow(self, follower: User, target_username: str) -> dict:
        target = await self.users.get_by_username(target_username)
        if not target:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")

        removed = await self.repo.remove_follow(follower.id, target.id)
        if not removed:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND, "You are not following this user"
            )

        followers = await self.repo.count_followers(target.id)
        return {
            "user_id": target.id,
            "username": target.username,
            "is_following": False,
            "follower_count": followers,
        }

    async def get_follow_status(self, viewer: User, target: User) -> dict:
        """Whether the viewer follows the target, and counts for the target."""
        is_following = await self.repo.is_following(viewer.id, target.id)
        followers = await self.repo.count_followers(target.id)
        following = await self.repo.count_following(target.id)
        return {
            "is_following": is_following,
            "follower_count": followers,
            "following_count": following,
        }

    async def list_followers(self, username: str) -> list[User]:
        target = await self.users.get_by_username(username)
        if not target:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
        ids = await self.repo.follower_ids(target.id)
        if not ids:
            return []
        users = []
        for uid in ids:
            u = await self.users.get_by_id(uid)
            if u:
                users.append(u)
        return users

    async def list_following(self, username: str) -> list[User]:
        target = await self.users.get_by_username(username)
        if not target:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
        ids = await self.repo.following_ids(target.id)
        if not ids:
            return []
        users = []
        for uid in ids:
            u = await self.users.get_by_id(uid)
            if u:
                users.append(u)
        return users

    # ---------- blocks ----------
    async def block(self, blocker: User, target_username: str) -> dict:
        target = await self.users.get_by_username(target_username)
        if not target:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")

        if target.id == blocker.id:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST, "You cannot block yourself"
            )

        existing = await self.repo.get_block(blocker.id, target.id)
        if existing:
            raise HTTPException(
                status.HTTP_409_CONFLICT, "You already blocked this user"
            )

        await self.repo.add_block(blocker.id, target.id)

        # A block also removes any follow relationships in both directions
        await self.repo.remove_follow(blocker.id, target.id)
        await self.repo.remove_follow(target.id, blocker.id)

        return {
            "user_id": target.id,
            "username": target.username,
            "is_blocked": True,
        }

    async def unblock(self, blocker: User, target_username: str) -> dict:
        target = await self.users.get_by_username(target_username)
        if not target:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")

        removed = await self.repo.remove_block(blocker.id, target.id)
        if not removed:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND, "You have not blocked this user"
            )

        return {
            "user_id": target.id,
            "username": target.username,
            "is_blocked": False,
        }

    async def list_blocked(self, user: User) -> list[dict]:
        blocks = await self.repo.list_blocked_by_user(user.id)
        out = []
        for b in blocks:
            target = await self.users.get_by_id(b.blocked_id)
            if target:
                out.append({
                    "user_id": target.id,
                    "username": target.username,
                    "display_name": target.display_name,
                })
        return out

    # ---------- privacy settings ----------
    async def set_private(self, user: User, is_private: bool) -> User:
        user.is_private = is_private
        await self.db.commit()
        await self.db.refresh(user)
        return user
