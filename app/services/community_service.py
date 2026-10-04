import re

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.community import Community
from app.models.user import User
from app.repositories.community_repo import CommunityRepository
from app.repositories.interest_repo import InterestRepository


def slugify(name: str) -> str:
    """Turn a name into a URL-safe slug."""
    slug = name.lower().strip()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = slug.strip("-")
    return slug[:60] or "community"


class CommunityService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = CommunityRepository(db)
        self.interests = InterestRepository(db)

    # ---------- create ----------
    async def create_community(
        self,
        creator: User,
        name: str,
        description: str | None,
        emoji: str | None,
        interest_slug: str,
        is_public: bool,
    ) -> Community:
        # Validate interest exists
        interest = await self.interests.get_by_slug(interest_slug)
        if not interest or not interest.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown interest: {interest_slug}",
            )

        # Unique slug
        base_slug = slugify(name)
        slug = base_slug
        counter = 1
        while await self.repo.get_by_slug(slug):
            counter += 1
            slug = f"{base_slug}-{counter}"

        community = Community(
            slug=slug,
            name=name,
            description=description,
            emoji=emoji or "🌐",
            interest_slug=interest_slug,
            creator_id=creator.id,
            is_public=is_public,
            member_count=1,
        )
        community = await self.repo.create(community)

        # Creator auto-joins as moderator
        await self.repo.add_member(creator.id, community.id, role="moderator")
        await self.repo.recount_members(community.id)

        return community

    # ---------- reads ----------
    async def list_communities(
        self, user: User, limit: int = 100, offset: int = 0
    ) -> list[dict]:
        communities = await self.repo.list_all(limit=limit, offset=offset)
        return await self._decorate_with_membership(communities, user)

    async def list_my_communities(self, user: User) -> list[dict]:
        communities = await self.repo.list_user_communities(user.id)
        return await self._decorate_with_membership(communities, user)

    async def _decorate_with_membership(
        self, communities: list[Community], user: User
    ) -> list[dict]:
        out = []
        for c in communities:
            membership = await self.repo.get_membership(user.id, c.id)
            item = {
                "id": c.id,
                "slug": c.slug,
                "name": c.name,
                "description": c.description,
                "emoji": c.emoji,
                "interest_slug": c.interest_slug,
                "creator_id": c.creator_id,
                "is_public": c.is_public,
                "member_count": c.member_count,
                "created_at": c.created_at,
                "updated_at": c.updated_at,
                "is_member": membership is not None,
                "is_moderator": bool(membership and membership.role == "moderator"),
            }
            out.append(item)
        return out

    async def get_community_or_404(self, slug: str) -> Community:
        c = await self.repo.get_by_slug(slug)
        if not c:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Community not found",
            )
        return c

    async def get_detail(self, slug: str, user: User) -> dict:
        c = await self.get_community_or_404(slug)
        if not c.is_public:
            # non-public communities require membership
            membership = await self.repo.get_membership(user.id, c.id)
            if not membership:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="This community is private",
                )
        return (await self._decorate_with_membership([c], user))[0]

    async def get_community_posts(self, slug: str, user: User):
        c = await self.get_community_or_404(slug)
        if not c.is_public:
            membership = await self.repo.get_membership(user.id, c.id)
            if not membership:
                raise HTTPException(403, "This community is private")

        from app.services.post_service import PostService

        posts = await self.repo.list_community_posts(c.id)
        enriched = await PostService(self.db).enrich_posts_with_reactions(posts, user)
        return enriched

    # ---------- membership ----------
    async def join(self, user: User, slug: str) -> dict:
        c = await self.get_community_or_404(slug)

        existing = await self.repo.get_membership(user.id, c.id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You are already a member",
            )

        await self.repo.add_member(user.id, c.id, role="member")
        count = await self.repo.recount_members(c.id)

        return {
            "community_id": c.id,
            "is_member": True,
            "member_count": count,
            "message": f"Joined {c.name}",
        }

    async def leave(self, user: User, slug: str) -> dict:
        c = await self.get_community_or_404(slug)

        if c.creator_id == user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Community creators cannot leave their own community",
            )

        removed = await self.repo.remove_member(user.id, c.id)
        if not removed:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="You are not a member of this community",
            )

        count = await self.repo.recount_members(c.id)

        return {
            "community_id": c.id,
            "is_member": False,
            "member_count": count,
            "message": f"Left {c.name}",
        }

    # ---------- update / delete ----------
    async def update_community(
        self, user: User, slug: str, **changes
    ) -> Community:
        c = await self.get_community_or_404(slug)
        if c.creator_id != user.id:
            raise HTTPException(403, "Only the community moderator can edit this")
        changes = {k: v for k, v in changes.items() if v is not None}
        if not changes:
            return c
        return await self.repo.update(c, **changes)

    async def delete_community(self, user: User, slug: str) -> None:
        c = await self.get_community_or_404(slug)
        if c.creator_id != user.id:
            raise HTTPException(403, "Only the community moderator can delete this")
        await self.repo.delete(c)
