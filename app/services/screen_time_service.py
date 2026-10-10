from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.screen_time_repo import ScreenTimeRepository


class ScreenTimeService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = ScreenTimeRepository(db)

    async def heartbeat(self, user: User) -> dict:
        """
        Called by the frontend every ~60s.
        Creates a new session if none active, or extends the current one.
        """
        # Close any stale sessions first
        await self.repo.close_stale_sessions(user.id)

        session = await self.repo.get_active_session(user.id)
        if session:
            session = await self.repo.touch_session(session)
        else:
            session = await self.repo.create_session(user.id)

        today_seconds = await self.repo.today_total_seconds(user.id)
        limit_seconds = user.daily_screen_time_limit_minutes * 60

        return {
            "session_id": session.id,
            "duration_seconds": session.duration_seconds,
            "today_total_seconds": today_seconds,
            "limit_seconds": limit_seconds,
            "limit_reached": today_seconds >= limit_seconds,
        }

    async def get_today(self, user: User) -> dict:
        today_seconds = await self.repo.today_total_seconds(user.id)
        limit_seconds = user.daily_screen_time_limit_minutes * 60
        return {
            "today_total_seconds": today_seconds,
            "today_total_minutes": today_seconds // 60,
            "limit_minutes": user.daily_screen_time_limit_minutes,
            "limit_reached": today_seconds >= limit_seconds,
            "break_reminders_enabled": user.break_reminders_enabled,
            "is_child_account": user.is_child_account,
        }

    async def update_limit(self, user: User, minutes: int, enabled: bool) -> User:
        # Children can't disable reminders
        if user.is_child_account and not enabled:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Child accounts cannot disable break reminders",
            )
        user.daily_screen_time_limit_minutes = minutes
        user.break_reminders_enabled = enabled
        await self.db.commit()
        await self.db.refresh(user)
        return user
