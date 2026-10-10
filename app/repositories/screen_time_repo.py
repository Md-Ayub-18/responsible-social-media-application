from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.screen_session import ScreenSession


# A session is considered "stale" (ended) after this many seconds without a heartbeat
STALE_AFTER_SECONDS = 600


class ScreenTimeRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_active_session(self, user_id: str) -> ScreenSession | None:
        """
        Return the user's current open session (last heartbeat within
        STALE_AFTER_SECONDS). Returns None if no session is active.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=STALE_AFTER_SECONDS)
        stmt = (
            select(ScreenSession)
            .where(
                ScreenSession.user_id == user_id,
                ScreenSession.ended_at.is_(None),
                ScreenSession.last_heartbeat_at >= cutoff,
            )
            .order_by(ScreenSession.started_at.desc())
            .limit(1)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_session(self, user_id: str) -> ScreenSession:
        now = datetime.now(timezone.utc)
        session = ScreenSession(
            user_id=user_id,
            started_at=now,
            last_heartbeat_at=now,
            duration_seconds=0,
        )
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def touch_session(self, session: ScreenSession) -> ScreenSession:
        """Update heartbeat + extend duration."""
        now = datetime.now(timezone.utc)
        elapsed = (now - session.last_heartbeat_at).total_seconds()
        session.last_heartbeat_at = now
        session.duration_seconds += int(max(elapsed, 0))
        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def close_session(self, session: ScreenSession) -> None:
        session.ended_at = datetime.now(timezone.utc)
        await self.db.commit()

    async def close_stale_sessions(self, user_id: str) -> None:
        """Close any open sessions with heartbeat older than STALE_AFTER_SECONDS."""
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=STALE_AFTER_SECONDS)
        stmt = select(ScreenSession).where(
            ScreenSession.user_id == user_id,
            ScreenSession.ended_at.is_(None),
            ScreenSession.last_heartbeat_at < cutoff,
        )
        result = await self.db.execute(stmt)
        sessions = list(result.scalars().all())
        now = datetime.now(timezone.utc)
        for s in sessions:
            s.ended_at = now
        if sessions:
            await self.db.commit()

    async def today_total_seconds(self, user_id: str) -> int:
        """Sum of duration_seconds for all sessions started today (UTC)."""
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        stmt = select(func.coalesce(func.sum(ScreenSession.duration_seconds), 0)).where(
            ScreenSession.user_id == user_id,
            ScreenSession.started_at >= today_start,
        )
        result = await self.db.execute(stmt)
        return int(result.scalar_one() or 0)
