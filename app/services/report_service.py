from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.report import Report
from app.models.user import User


class ReportService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_report(
        self,
        reporter: User,
        target_type: str,
        target_id: str,
        category: str,
        description: str | None,
    ) -> Report:
        # prevent self-report spam
        if target_type == "user" and target_id == reporter.id:
            raise HTTPException(400, "You cannot report yourself")

        # dedupe: one open report per (reporter, target)
        existing = await self.db.execute(
            select(Report).where(
                Report.reporter_id == reporter.id,
                Report.target_type == target_type,
                Report.target_id == target_id,
                Report.status.in_(("open", "reviewing")),
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You already have an open report for this content",
            )

        report = Report(
            reporter_id=reporter.id,
            target_type=target_type,
            target_id=target_id,
            category=category,
            description=description,
        )
        self.db.add(report)
        await self.db.commit()
        await self.db.refresh(report)
        return report

    async def list_mine(self, user: User) -> list[Report]:
        result = await self.db.execute(
            select(Report).where(Report.reporter_id == user.id)
            .order_by(Report.created_at.desc())
        )
        return list(result.scalars().all())

    async def list_queue(self, status_filter: str = "open") -> list[Report]:
        stmt = select(Report)
        if status_filter:
            stmt = stmt.where(Report.status == status_filter)
        stmt = stmt.order_by(Report.created_at.desc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def resolve(
        self, moderator: User, report_id: str, new_status: str, note: str | None
    ) -> Report:
        result = await self.db.execute(select(Report).where(Report.id == report_id))
        report = result.scalar_one_or_none()
        if not report:
            raise HTTPException(404, "Report not found")

        old_status = report.status
        report.status = new_status
        report.resolution_note = f"[moderator:{moderator.username}] {note or new_status}"
        report.resolved_by_id = moderator.id
        await self.db.commit()
        await self.db.refresh(report)

        from app.services.audit_service import AuditService
        await AuditService(self.db).log(
            actor=moderator,
            action="report_resolved",
            target_type="report",
            target_id=report.id,
            reason=note or new_status,
            details={"before": old_status, "after": new_status,
                     "target_type": report.target_type,
                     "target_id": report.target_id},
        )
        return report