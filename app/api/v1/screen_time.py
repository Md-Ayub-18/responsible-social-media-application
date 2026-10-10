from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.screen_time import (
    HeartbeatResponse,
    TodayScreenTime,
    UpdateLimitRequest,
)
from app.schemas.user import UserRead
from app.services.screen_time_service import ScreenTimeService

router = APIRouter(prefix="/screen-time", tags=["screen-time"])


@router.post("/heartbeat", response_model=HeartbeatResponse)
async def heartbeat(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Called by the frontend every ~60s to log active time."""
    return await ScreenTimeService(db).heartbeat(current_user)


@router.get("/today", response_model=TodayScreenTime)
async def today(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get today's screen time summary for the current user."""
    return await ScreenTimeService(db).get_today(current_user)


@router.patch("/limit", response_model=UserRead)
async def update_limit(
    payload: UpdateLimitRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Set daily screen time limit + break reminder preference."""
    user = await ScreenTimeService(db).update_limit(
        current_user,
        payload.daily_screen_time_limit_minutes,
        payload.break_reminders_enabled,
    )
    return UserRead.model_validate(user)
