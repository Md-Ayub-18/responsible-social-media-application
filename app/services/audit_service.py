from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.moderation_log import ModerationLog
from app.models.user import User


class AuditService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def log(
        self,
        actor: User | None,
        action: str,
        target_type: str,
        target_id: str,
        reason: str | None = None,
        details: dict | None = None,
    ) -> ModerationLog:
        entry = ModerationLog(
            actor_id=actor.id if actor else None,
            actor_username=actor.username if actor else "system",
            action=action,
            target_type=target_type,
            target_id=target_id,
            reason=reason,
            details=details or {},
        )
        self.db.add(entry)
        await self.db.commit()
        await self.db.refresh(entry)
        return entry

    async def list_recent(
        self,
        action: str | None = None,
        actor_id: str | None = None,
        target_type: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ModerationLog]:
        stmt = select(ModerationLog)
        if action:
            stmt = stmt.where(ModerationLog.action == action)
        if actor_id:
            stmt = stmt.where(ModerationLog.actor_id == actor_id)
        if target_type:
            stmt = stmt.where(ModerationLog.target_type == target_type)
        stmt = stmt.order_by(ModerationLog.created_at.desc()).limit(limit).offset(offset)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
