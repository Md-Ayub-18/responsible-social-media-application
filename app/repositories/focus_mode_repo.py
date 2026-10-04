from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.focus_mode import FocusMode


class FocusModeRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_for_user(self, user_id: str) -> list[FocusMode]:
        stmt = (
            select(FocusMode)
            .where(FocusMode.user_id == user_id)
            .order_by(FocusMode.is_default.desc(), FocusMode.created_at.asc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get(self, mode_id: str) -> FocusMode | None:
        result = await self.db.execute(
            select(FocusMode).where(FocusMode.id == mode_id)
        )
        return result.scalar_one_or_none()

    async def get_default(self, user_id: str) -> FocusMode | None:
        result = await self.db.execute(
            select(FocusMode).where(
                FocusMode.user_id == user_id, FocusMode.is_default.is_(True)
            )
        )
        return result.scalar_one_or_none()

    async def create(self, mode: FocusMode) -> FocusMode:
        self.db.add(mode)
        await self.db.commit()
        await self.db.refresh(mode)
        return mode

    async def bulk_create(self, modes: list[FocusMode]) -> None:
        self.db.add_all(modes)
        await self.db.commit()

    async def update(self, mode: FocusMode, **changes) -> FocusMode:
        for key, value in changes.items():
            setattr(mode, key, value)
        await self.db.commit()
        await self.db.refresh(mode)
        return mode

    async def delete(self, mode: FocusMode) -> None:
        await self.db.delete(mode)
        await self.db.commit()

    async def clear_default_flag(self, user_id: str) -> None:
        await self.db.execute(
            update(FocusMode)
            .where(FocusMode.user_id == user_id)
            .values(is_default=False)
        )
        await self.db.commit()