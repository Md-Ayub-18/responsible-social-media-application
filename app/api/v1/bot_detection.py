from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.trust import BotSignalRead, BotSignalWithUser
from app.services.bot_service import BotService

router = APIRouter(prefix="/moderation/bots", tags=["bot-detection"])


@router.get("/suspicious", response_model=list[BotSignalWithUser])
async def list_suspicious(
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Moderator view: accounts flagged as suspicious or confirmed bots."""
    rows = await BotService(db).list_suspicious(limit)
    out: list[BotSignalWithUser] = []
    for signal, user in rows:
        item = BotSignalWithUser.model_validate(signal)
        item.username = user.username
        item.display_name = user.display_name
        out.append(item)
    return out


@router.post("/evaluate/{user_id}", response_model=BotSignalRead)
async def evaluate_user_now(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Force a re-evaluation of a user (moderator only)."""
    return await BotService(db).evaluate_and_store(user_id)