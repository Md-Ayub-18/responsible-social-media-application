from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.trust import ReportCreate, ReportRead, ReportResolve
from app.services.report_service import ReportService

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("", response_model=ReportRead, status_code=status.HTTP_201_CREATED)
async def create_report(
    payload: ReportCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await ReportService(db).create_report(
        current_user, payload.target_type, payload.target_id,
        payload.category, payload.description,
    )


@router.get("/mine", response_model=list[ReportRead])
async def list_my_reports(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await ReportService(db).list_mine(current_user)


@router.get("/queue", response_model=list[ReportRead])
async def report_queue(
    status_filter: str = Query(default="open", alias="status"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Moderator view of all reports."""
    return await ReportService(db).list_queue(status_filter)


@router.patch("/{report_id}", response_model=ReportRead)
async def resolve_report(
    report_id: str,
    payload: ReportResolve,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await ReportService(db).resolve(
        current_user, report_id, payload.status, payload.note
    )
