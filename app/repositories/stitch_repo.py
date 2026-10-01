from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.stitch_project import Contribution, StitchProject


class StitchRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ---------- projects ----------
    async def create_project(self, project: StitchProject) -> StitchProject:
        self.db.add(project)
        await self.db.commit()
        await self.db.refresh(project)
        return project

    async def get_project(self, project_id: str, with_contributions: bool = False) -> StitchProject | None:
        stmt = select(StitchProject).where(StitchProject.id == project_id)
        if with_contributions:
            stmt = stmt.options(selectinload(StitchProject.contributions))
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_projects(
        self, status: str | None = None, interest_slug: str | None = None,
        limit: int = 50, offset: int = 0,
    ) -> list[StitchProject]:
        stmt = select(StitchProject)
        if status:
            stmt = stmt.where(StitchProject.status == status)
        if interest_slug:
            stmt = stmt.where(StitchProject.interest_slug == interest_slug)
        stmt = stmt.order_by(StitchProject.created_at.desc()).limit(limit).offset(offset)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def update_project(self, project: StitchProject, **changes) -> StitchProject:
        for key, value in changes.items():
            setattr(project, key, value)
        await self.db.commit()
        await self.db.refresh(project)
        return project

    # ---------- contributions ----------
    async def create_contribution(self, contribution: Contribution) -> Contribution:
        self.db.add(contribution)
        await self.db.commit()
        await self.db.refresh(contribution)
        return contribution

    async def get_contribution(self, contribution_id: str) -> Contribution | None:
        result = await self.db.execute(
            select(Contribution).where(Contribution.id == contribution_id)
        )
        return result.scalar_one_or_none()

    async def list_contributions(self, project_id: str) -> list[Contribution]:
        stmt = (
            select(Contribution)
            .where(Contribution.project_id == project_id)
            .order_by(Contribution.order_index.asc().nulls_last(), Contribution.created_at.asc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def list_approved_contributions(self, project_id: str) -> list[Contribution]:
        stmt = (
            select(Contribution)
            .where(Contribution.project_id == project_id)
            .where(Contribution.status == "approved")
            .order_by(Contribution.order_index.asc().nulls_last(), Contribution.created_at.asc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def update_contribution(self, contribution: Contribution, **changes) -> Contribution:
        for key, value in changes.items():
            setattr(contribution, key, value)
        await self.db.commit()
        await self.db.refresh(contribution)
        return contribution

    async def delete_contribution(self, contribution: Contribution) -> None:
        await self.db.delete(contribution)
        await self.db.commit()