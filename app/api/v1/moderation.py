from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import get_current_user, require_moderator
from app.models.user import User
from app.schemas.post import PostRead
from app.services.moderation_service import ModerationService
from app.services.engagement_service import EngagementService
from app.schemas.trust import EngagementSignalRead, EngagementSignalWithPost

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




@router.get("/engagement/suspicious", response_model=list[EngagementSignalWithPost])
async def list_suspicious_engagement(
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(require_moderator),
    db: AsyncSession = Depends(get_db),
):
    """Moderator view: posts with suspicious or manipulated engagement."""
    rows = await EngagementService(db).list_suspicious(limit)
    out: list[EngagementSignalWithPost] = []
    for signal, post in rows:
        item = EngagementSignalWithPost.model_validate(signal)
        item.post_text = post.text[:200]
        item.post_author_id = post.author_id
        out.append(item)
    return out


@router.post("/engagement/scan/{post_id}", response_model=EngagementSignalRead)
async def scan_post_engagement(
    post_id: str,
    current_user: User = Depends(require_moderator),
    db: AsyncSession = Depends(get_db),
):
    """Force re-evaluation of a post's engagement pattern."""
    return await EngagementService(db).evaluate_and_store(post_id)


@router.post("/engagement/scan-recent")
async def scan_recent_engagement(
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(require_moderator),
    db: AsyncSession = Depends(get_db),
):
    """Batch-scan the N most recent posts with 5+ likes."""
    count = await EngagementService(db).scan_recent_posts(limit)
    return {"scanned": count}
