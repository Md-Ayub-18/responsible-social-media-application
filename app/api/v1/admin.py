from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.services.admin_service import AdminService
from app.services.audit_service import AuditService

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/dashboard")
async def dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Aggregated view of everything moderators need to act on."""
    return await AdminService(db).dashboard()


@router.get("/audit-log")
async def audit_log(
    action: str | None = Query(default=None),
    actor_id: str | None = Query(default=None),
    target_type: str | None = Query(default=None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Filterable, append-only log of every moderator and system action."""
    entries = await AuditService(db).list_recent(
        action=action, actor_id=actor_id,
        target_type=target_type, limit=limit, offset=offset,
    )
    return [
        {
            "id": e.id,
            "action": e.action,
            "actor_username": e.actor_username,
            "target_type": e.target_type,
            "target_id": e.target_id,
            "reason": e.reason,
            "details": e.details,
            "created_at": e.created_at.isoformat(),
        }
        for e in entries
    ]
