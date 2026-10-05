from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.social import BlockedUser, BlockResponse
from app.services.social_service import SocialService

router = APIRouter(prefix="/blocks", tags=["blocks"])


@router.post("/{username}", response_model=BlockResponse)
async def block_user(
    username: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Block a user. Mutual invisibility + no interaction."""
    service = SocialService(db)
    return await service.block(current_user, username)


@router.delete("/{username}", response_model=BlockResponse)
async def unblock_user(
    username: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Unblock a user."""
    service = SocialService(db)
    return await service.unblock(current_user, username)


@router.get("", response_model=list[BlockedUser])
async def list_blocked(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List users you've blocked."""
    service = SocialService(db)
    return await service.list_blocked(current_user)
