from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.interest import Interest
from app.repositories.interest_repo import InterestRepository

# Seed data — runs once on startup
SEED_INTERESTS = [
    {"slug": "learning",      "name": "Learning",        "emoji": "📚", "description": "Courses, tutorials, books, and skill-building."},
    {"slug": "sports",        "name": "Sports",          "emoji": "⚽", "description": "Matches, teams, fitness, and athletics."},
    {"slug": "art",           "name": "Art",             "emoji": "🎨", "description": "Painting, design, music, and creative work."},
    {"slug": "technology",    "name": "Technology",      "emoji": "💻", "description": "Programming, AI, gadgets, and engineering."},
    {"slug": "entertainment", "name": "Entertainment",   "emoji": "🎬", "description": "Movies, shows, games, and pop culture."},
    {"slug": "personal",      "name": "Personal Stories","emoji": "💬", "description": "Life updates, journeys, and reflections."},
    {"slug": "social_causes", "name": "Social Causes",   "emoji": "🌱", "description": "Climate, equality, community, and activism."},
]


class InterestService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = InterestRepository(db)

    # ---------- seeding ----------
    async def seed_if_empty(self) -> int:
        existing = await self.repo.list_all(active_only=False)
        if existing:
            return 0
        new_items = [Interest(**data) for data in SEED_INTERESTS]
        await self.repo.bulk_create(new_items)
        return len(new_items)

    # ---------- reads ----------
    async def list_interests(self) -> list[Interest]:
        return await self.repo.list_all()

    async def get_interest_or_404(self, interest_id: str) -> Interest:
        interest = await self.repo.get_by_id(interest_id)
        if not interest:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Interest not found",
            )
        return interest

    # ---------- user selections ----------
    async def list_user_interests(self, user_id: str) -> list[Interest]:
        return await self.repo.list_user_interests(user_id)

    async def add_user_interest(
        self, user_id: str, interest_id: str | None, slug: str | None
    ) -> Interest:
        if interest_id:
            interest = await self.repo.get_by_id(interest_id)
        elif slug:
            interest = await self.repo.get_by_slug(slug)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Provide either interest_id or slug",
            )
        if not interest:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Interest not found",
            )

        existing = await self.repo.get_user_link(user_id, interest.id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Interest already selected",
            )

        await self.repo.add_user_interest(user_id, interest.id)
        return interest

    async def remove_user_interest(self, user_id: str, interest_id: str) -> None:
        interest = await self.get_interest_or_404(interest_id)
        removed = await self.repo.remove_user_interest(user_id, interest.id)
        if not removed:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Interest was not selected by this user",
            )
