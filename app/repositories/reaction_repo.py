from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.reaction import Reaction


class ReactionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def count_for_post(self, post_id: str) -> int:
        stmt = select(func.count()).select_from(Reaction).where(
            Reaction.post_id == post_id
        )
        return (await self.db.execute(stmt)).scalar_one()

    async def count_for_posts(self, post_ids: list[str]) -> dict[str, int]:
        if not post_ids:
            return {}
        stmt = (
            select(Reaction.post_id, func.count())
            .where(Reaction.post_id.in_(post_ids))
            .group_by(Reaction.post_id)
        )
        rows = (await self.db.execute(stmt)).all()
        return {pid: cnt for pid, cnt in rows}

    async def liked_post_ids(self, user_id: str, post_ids: list[str]) -> set[str]:
        if not post_ids:
            return set()
        stmt = select(Reaction.post_id).where(
            Reaction.user_id == user_id,
            Reaction.post_id.in_(post_ids),
            Reaction.kind == "like",
        )
        rows = (await self.db.execute(stmt)).all()
        return {r[0] for r in rows}

    async def get(self, user_id: str, post_id: str, kind: str = "like") -> Reaction | None:
        stmt = select(Reaction).where(
            Reaction.user_id == user_id,
            Reaction.post_id == post_id,
            Reaction.kind == kind,
        )
        return (await self.db.execute(stmt)).scalar_one_or_none()

    async def add(self, user_id: str, post_id: str, kind: str = "like") -> Reaction:
        r = Reaction(user_id=user_id, post_id=post_id, kind=kind)
        self.db.add(r)
        await self.db.commit()
        await self.db.refresh(r)
        return r

    async def remove(self, user_id: str, post_id: str, kind: str = "like") -> bool:
        result = await self.db.execute(
            delete(Reaction).where(
                Reaction.user_id == user_id,
                Reaction.post_id == post_id,
                Reaction.kind == kind,
            )
        )
        await self.db.commit()
        return result.rowcount > 0
