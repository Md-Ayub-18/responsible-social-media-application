from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.community import Community, CommunityMember


class CommunityRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ---------- reads ----------
    async def list_all(self, limit: int = 100, offset: int = 0) -> list[Community]:
        stmt = (
            select(Community)
            .where(Community.is_public.is_(True))
            .order_by(Community.member_count.desc(), Community.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, community_id: str) -> Community | None:
        result = await self.db.execute(
            select(Community).where(Community.id == community_id)
        )
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Community | None:
        result = await self.db.execute(
            select(Community).where(Community.slug == slug)
        )
        return result.scalar_one_or_none()

    async def list_user_communities(self, user_id: str) -> list[Community]:
        stmt = (
            select(Community)
            .join(CommunityMember, CommunityMember.community_id == Community.id)
            .where(CommunityMember.user_id == user_id)
            .order_by(Community.name)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    # ---------- writes ----------
    async def create(self, community: Community) -> Community:
        self.db.add(community)
        await self.db.commit()
        await self.db.refresh(community)
        return community

    async def update(self, community: Community, **changes) -> Community:
        for key, value in changes.items():
            setattr(community, key, value)
        await self.db.commit()
        await self.db.refresh(community)
        return community

    async def delete(self, community: Community) -> None:
        await self.db.delete(community)
        await self.db.commit()

    # ---------- membership ----------
    async def get_membership(
        self, user_id: str, community_id: str
    ) -> CommunityMember | None:
        result = await self.db.execute(
            select(CommunityMember).where(
                CommunityMember.user_id == user_id,
                CommunityMember.community_id == community_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_members(self, community_id: str) -> list[CommunityMember]:
        stmt = (
            select(CommunityMember)
            .where(CommunityMember.community_id == community_id)
            .order_by(CommunityMember.created_at.asc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def add_member(
        self, user_id: str, community_id: str, role: str = "member"
    ) -> CommunityMember:
        m = CommunityMember(user_id=user_id, community_id=community_id, role=role)
        self.db.add(m)
        await self.db.commit()
        await self.db.refresh(m)
        return m

    async def remove_member(self, user_id: str, community_id: str) -> bool:
        m = await self.get_membership(user_id, community_id)
        if not m:
            return False
        await self.db.delete(m)
        await self.db.commit()
        return True

    async def recount_members(self, community_id: str) -> int:
        stmt = (
            select(func.count())
            .select_from(CommunityMember)
            .where(CommunityMember.community_id == community_id)
        )
        count = (await self.db.execute(stmt)).scalar_one()

        community = await self.get_by_id(community_id)
        if community:
            community.member_count = count
            await self.db.commit()
        return count

    # ---------- posts (scoped) ----------
    async def list_community_posts(
        self, community_id: str, limit: int = 30, offset: int = 0
    ):
        from app.models.post import Post

        community = await self.get_by_id(community_id)
        if not community:
            return []

        stmt = (
            select(Post)
            .where(Post.community_id == community_id)
            .where(Post.is_hidden.is_(False))
            .where(Post.moderation_status == "approved")
            .order_by(Post.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
