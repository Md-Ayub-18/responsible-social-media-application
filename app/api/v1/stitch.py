from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.stitch import (
    ContributionModerate,
    ContributionRead,
    StitchProjectCreate,
    StitchProjectDetail,
    StitchProjectRead,
    StitchProjectUpdate,
    StitchResult,
)
from app.services.stitch_service import StitchService

router = APIRouter(prefix="/stitch", tags=["stitch"])


# ---------- projects ----------

@router.post(
    "/projects",
    response_model=StitchProjectRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_project(
    payload: StitchProjectCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = StitchService(db)
    project = await svc.create_project(
        current_user, payload.title, payload.description, payload.interest_slug
    )
    return StitchProjectRead.model_validate(project)


@router.get("/projects", response_model=list[StitchProjectRead])
async def list_projects(
    status_filter: str | None = Query(default=None, alias="status"),
    interest_slug: str | None = Query(default=None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    svc = StitchService(db)
    return await svc.list_projects(status_filter, interest_slug, limit, offset)


@router.get("/projects/{project_id}", response_model=StitchProjectDetail)
async def get_project(
    project_id: str,
    db: AsyncSession = Depends(get_db),
):
    svc = StitchService(db)
    project = await svc.get_project_or_404(project_id, with_contributions=True)
    return StitchProjectDetail.model_validate(project)


@router.patch("/projects/{project_id}", response_model=StitchProjectRead)
async def update_project(
    project_id: str,
    payload: StitchProjectUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = StitchService(db)
    project = await svc.update_project(
        current_user, project_id, **payload.model_dump(exclude_unset=True)
    )
    return StitchProjectRead.model_validate(project)


# ---------- contributions ----------

@router.post(
    "/projects/{project_id}/contributions",
    response_model=ContributionRead,
    status_code=status.HTTP_201_CREATED,
)
async def submit_contribution(
    project_id: str,
    file: UploadFile = File(...),
    caption: str | None = Form(default=None),
    consent_given: bool = Form(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = StitchService(db)
    contribution = await svc.submit_contribution(
        current_user, project_id, file, caption, consent_given
    )
    return ContributionRead.model_validate(contribution)


@router.get(
    "/projects/{project_id}/contributions",
    response_model=list[ContributionRead],
)
async def list_contributions(
    project_id: str,
    db: AsyncSession = Depends(get_db),
):
    svc = StitchService(db)
    return await svc.list_contributions(project_id)


@router.patch(
    "/contributions/{contribution_id}",
    response_model=ContributionRead,
)
async def moderate_contribution(
    contribution_id: str,
    payload: ContributionModerate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = StitchService(db)
    contribution = await svc.moderate_contribution(
        current_user, contribution_id,
        payload.status, payload.rejection_reason, payload.order_index,
    )
    return ContributionRead.model_validate(contribution)


@router.delete(
    "/contributions/{contribution_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def withdraw_contribution(
    contribution_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = StitchService(db)
    await svc.withdraw_contribution(current_user, contribution_id)
    return None


# ---------- stitch ----------

@router.post("/projects/{project_id}/stitch", response_model=StitchResult)
async def stitch_project(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = StitchService(db)
    project = await svc.stitch_project(current_user, project_id)

    approved_count = sum(1 for c in (project.contributions or []) if c.status == "approved")
    return StitchResult(
        project_id=project.id,
        status=project.status,
        stitched_video_url=project.stitched_video_url,
        contribution_count=approved_count,
        message="Stitching completed successfully",
    )