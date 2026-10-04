from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.community import (
    CommunityCreate,
    CommunityListResponse,
    CommunityRead,
    CommunityUpdate,
    CommunityWithMembership,
    JoinLeaveResponse,
)
from app.services.community_service import CommunityService

router = APIRouter(prefix="/communities", tags=["communities"])


# ---------- create ----------
@router.post(
    "",
    response_model=CommunityWithMembership,
    status_code=status.HTTP_201_CREATED,
)
async def create_community(
    payload: CommunityCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new community. The creator becomes its moderator."""
    service = CommunityService(db)
    community = await service.create_community(
        creator=current_user,
        name=payload.name,
        description=payload.description,
        emoji=payload.emoji,
        interest_slug=payload.interest_slug,
        is_public=payload.is_public,
    )
    detail = await service.get_detail(community.slug, current_user)
    return detail


# ---------- list ----------
@router.get("", response_model=CommunityListResponse)
async def list_communities(
    limit: int = Query(100, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all public communities (most popular first)."""
    service = CommunityService(db)
    items = await service.list_communities(current_user, limit=limit, offset=offset)
    return CommunityListResponse(communities=items, count=len(items))


@router.get("/mine", response_model=CommunityListResponse)
async def list_my_communities(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List communities the current user has joined."""
    service = CommunityService(db)
    items = await service.list_my_communities(current_user)
    return CommunityListResponse(communities=items, count=len(items))


# ---------- detail ----------
@router.get("/by-id/{community_id}", response_model=CommunityWithMembership)
async def get_community_by_id(
    community_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Fetch a community by its ID (used when posting from a community context)."""
    service = CommunityService(db)
    c = await service.repo.get_by_id(community_id)
    if not c:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Community not found")
    # Reuse the detail logic via slug
    return await service.get_detail(c.slug, current_user)

@router.get("/{slug}", response_model=CommunityWithMembership)
async def get_community(
    slug: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a community by slug, including the user's membership status."""
    service = CommunityService(db)
    return await service.get_detail(slug, current_user)


@router.get("/{slug}/posts")
async def get_community_posts(
    slug: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get approved posts tagged with this community's interest."""
    service = CommunityService(db)
    return await service.get_community_posts(slug, current_user)


# ---------- membership ----------
@router.post("/{slug}/join", response_model=JoinLeaveResponse)
async def join_community(
    slug: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Join a community."""
    service = CommunityService(db)
    return await service.join(current_user, slug)


@router.delete("/{slug}/leave", response_model=JoinLeaveResponse)
async def leave_community(
    slug: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Leave a community. Community creators cannot leave."""
    service = CommunityService(db)
    return await service.leave(current_user, slug)


# ---------- update / delete ----------
@router.patch("/{slug}", response_model=CommunityRead)
async def update_community(
    slug: str,
    payload: CommunityUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a community (moderator only)."""
    service = CommunityService(db)
    return await service.update_community(
        current_user, slug, **payload.model_dump(exclude_unset=True)
    )


@router.delete("/{slug}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_community(
    slug: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a community (moderator only)."""
    service = CommunityService(db)
    await service.delete_community(current_user, slug)
    return None
