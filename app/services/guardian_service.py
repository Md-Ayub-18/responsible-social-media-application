from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.guardian_link import GuardianLink
from app.models.user import User


class GuardianService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_child(
        self,
        guardian: User,
        email: str,
        username: str,
        display_name: str | None,
        password: str,
    ) -> User:
        # emails/usernames must be unique
        dup = await self.db.execute(
            select(User).where((User.email == email) | (User.username == username))
        )
        if dup.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email or username already in use",
            )

        child = User(
            email=email,
            username=username,
            display_name=display_name or username,
            hashed_password=hash_password(password),
            is_child_account=True,
        )
        self.db.add(child)
        await self.db.flush()   # to get child.id

        # link guardian → child
        link = GuardianLink(guardian_id=guardian.id, child_id=child.id)
        self.db.add(link)

        # force the child into Kids focus mode
        from app.services.focus_mode_service import FocusModeService
        await FocusModeService(self.db).create_defaults_for_user(child.id)
        modes = await FocusModeService(self.db).list_modes(child.id)
        kids = next((m for m in modes if m.name == "Kids"), None)
        if kids:
            child.active_focus_mode_id = kids.id

        await self.db.commit()
        await self.db.refresh(child)
        return child

    async def list_children(self, guardian: User) -> list[User]:
        stmt = (
            select(User)
            .join(GuardianLink, GuardianLink.child_id == User.id)
            .where(GuardianLink.guardian_id == guardian.id)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_child_activity(self, guardian: User, child_id: str) -> dict:
        # verify link
        link_q = await self.db.execute(
            select(GuardianLink).where(
                GuardianLink.guardian_id == guardian.id,
                GuardianLink.child_id == child_id,
            )
        )
        if not link_q.scalar_one_or_none():
            raise HTTPException(403, "You are not the guardian of this account")

        from app.models.post import Post
        posts_q = await self.db.execute(
            select(Post).where(Post.author_id == child_id)
            .order_by(Post.created_at.desc()).limit(50)
        )
        posts = list(posts_q.scalars().all())

        return {
            "child_id": child_id,
            "post_count": len(posts),
            "recent_posts": [
                {
                    "id": p.id,
                    "text": p.text[:200],
                    "interest_slug": p.interest_slug,
                    "moderation_status": p.moderation_status,
                    "created_at": p.created_at.isoformat(),
                }
                for p in posts
            ],
        }