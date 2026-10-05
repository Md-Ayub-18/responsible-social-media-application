from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.social import (
    FollowResponse,
    FollowStatusResponse,
    PublicUserBrief,
)
from app.services.social_service import SocialService

router = APIRouter(prefix="/social", tags=["social"])


# ---------- follow ----------
@router.post("/follow/{username}", response_model=FollowResponse)
async def follow_user(
    username: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Follow a user."""
    service = SocialService(db)
    return await service.follow(current_user, username)


@router.delete("/follow/{username}", response_model=FollowResponse)
async def unfollow_user(
    username: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Unfollow a user."""
    service = SocialService(db)
    return await service.unfollow(current_user, username)


@router.get("/follow/{username}", response_model=FollowStatusResponse)
async def get_follow_status(
    username: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Check if you're following this user."""
    from fastapi import HTTPException
    from app.repositories.user_repo import UserRepository

    target = await UserRepository(db).get_by_username(username)
    if not target:
        raise HTTPException(404, "User not found")

    service = SocialService(db)
    status = await service.get_follow_status(current_user, target)
    return FollowStatusResponse(
        user_id=target.id,
        username=target.username,
        **status,
    )


# ---------- lists ----------
@router.get("/followers/{username}", response_model=list[PublicUserBrief])
async def list_followers(
    username: str,
    db: AsyncSession = Depends(get_db),
):
    """List users who follow this account."""
    service = SocialService(db)
    users = await service.list_followers(username)
    return [PublicUserBrief.model_validate(u) for u in users]


@router.get("/following/{username}", response_model=list[PublicUserBrief])
async def list_following(
    username: str,
    db: AsyncSession = Depends(get_db),
):
    """List users this account follows."""
    service = SocialService(db)
    users = await service.list_following(username)
    return [PublicUserBrief.model_validate(u) for u in users]
