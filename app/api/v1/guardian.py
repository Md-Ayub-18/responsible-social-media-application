from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.trust import ChildCreate, ChildRead
from app.services.guardian_service import GuardianService

router = APIRouter(prefix="/guardian", tags=["guardian"])


@router.post("/children", response_model=ChildRead, status_code=status.HTTP_201_CREATED)
async def create_child(
    payload: ChildCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    child = await GuardianService(db).create_child(
        current_user, payload.email, payload.username,
        payload.display_name, payload.password,
    )
    return ChildRead.model_validate(child)


@router.get("/children", response_model=list[ChildRead])
async def list_children(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await GuardianService(db).list_children(current_user)


@router.get("/children/{child_id}/activity")
async def child_activity(
    child_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await GuardianService(db).get_child_activity(current_user, child_id)