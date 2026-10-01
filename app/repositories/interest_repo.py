from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.interest import Interest, UserInterest


class InterestRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_all(self, active_only: bool = True) -> list[Interest]:
        stmt = select(Interest).order_by(Interest.name)
        if active_only:
            stmt = stmt.where(Interest.is_active.is_(True))
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, interest_id: str) -> Interest | None:
        result = await self.db.execute(
            select(Interest).where(Interest.id == interest_id)
        )
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Interest | None:
        result = await self.db.execute(
            select(Interest).where(Interest.slug == slug)
        )
        return result.scalar_one_or_none()

    async def bulk_create(self, interests: list[Interest]) -> None:
        self.db.add_all(interests)
        await self.db.commit()

    # --- user interest links ---

    async def list_user_interests(self, user_id: str) -> list[Interest]:
        stmt = (
            select(Interest)
            .join(UserInterest, UserInterest.interest_id == Interest.id)
            .where(UserInterest.user_id == user_id)
            .order_by(Interest.name)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_user_link(
        self, user_id: str, interest_id: str
    ) -> UserInterest | None:
        result = await self.db.execute(
            select(UserInterest).where(
                UserInterest.user_id == user_id,
                UserInterest.interest_id == interest_id,
            )
        )
        return result.scalar_one_or_none()

    async def add_user_interest(self, user_id: str, interest_id: str) -> UserInterest:
        link = UserInterest(user_id=user_id, interest_id=interest_id)
        self.db.add(link)
        await self.db.commit()
        await self.db.refresh(link)
        return link

    async def remove_user_interest(self, user_id: str, interest_id: str) -> bool:
        result = await self.db.execute(
            delete(UserInterest).where(
                UserInterest.user_id == user_id,
                UserInterest.interest_id == interest_id,
            )
        )
        await self.db.commit()
        return result.rowcount > 0