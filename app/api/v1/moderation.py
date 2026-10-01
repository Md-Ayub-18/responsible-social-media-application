from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.post import PostRead
from app.services.moderation_service import ModerationService

router = APIRouter(prefix="/moderation", tags=["moderation"])


class OverrideRequest(BaseModel):
    status: str = Field(pattern="^(approved|flagged|removed)$")
    reason: str | None = Field(default=None, max_length=500)


@router.get("/queue", response_model=list[PostRead])
async def get_queue(
    status_filter: str | None = Query(default="flagged", alias="status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """View posts awaiting moderation. Default shows 'flagged' posts."""
    return await ModerationService(db).list_queue(status_filter, limit, offset)


@router.patch("/posts/{post_id}", response_model=PostRead)
async def override_post_status(
    post_id: str,
    payload: OverrideRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Moderator override: approve, flag, or remove a post."""
    return await ModerationService(db).override_decision(
        current_user, post_id, payload.status, payload.reason
    )