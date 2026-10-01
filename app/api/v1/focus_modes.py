from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.focus_mode import (
    ActiveFocusModeResponse,
    FocusModeCreate,
    FocusModeListResponse,
    FocusModeRead,
    FocusModeUpdate,
    SwitchFocusModeRequest,
)
from app.services.focus_mode_service import FocusModeService

router = APIRouter(prefix="/users/me/focus-modes", tags=["focus-modes"])


@router.get("", response_model=FocusModeListResponse)
async def list_focus_modes(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    modes = await FocusModeService(db).list_modes(current_user.id)
    return FocusModeListResponse(
        modes=[FocusModeRead.model_validate(m) for m in modes],
        count=len(modes),
    )


@router.post("", response_model=FocusModeRead, status_code=status.HTTP_201_CREATED)
async def create_focus_mode(
    payload: FocusModeCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = FocusModeService(db)
    mode = await service.create_mode(
        user_id=current_user.id,
        name=payload.name,
        emoji=payload.emoji,
        description=payload.description,
        interest_slugs=payload.interest_slugs,
        is_default=payload.is_default,
    )
    return FocusModeRead.model_validate(mode)


@router.get("/active", response_model=ActiveFocusModeResponse)
async def get_active_focus_mode(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    mode = await FocusModeService(db).get_active_mode(current_user)
    return ActiveFocusModeResponse(
        active_mode=FocusModeRead.model_validate(mode) if mode else None,
        is_active=mode is not None,
    )


@router.patch("/active", response_model=ActiveFocusModeResponse)
async def switch_active_focus_mode(
    payload: SwitchFocusModeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    mode = await FocusModeService(db).switch_active_mode(
        current_user, payload.focus_mode_id
    )
    return ActiveFocusModeResponse(
        active_mode=FocusModeRead.model_validate(mode) if mode else None,
        is_active=mode is not None,
    )


@router.patch("/{mode_id}", response_model=FocusModeRead)
async def update_focus_mode(
    mode_id: str,
    payload: FocusModeUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = FocusModeService(db)
    mode = await service.update_mode(
        current_user.id, mode_id, **payload.model_dump(exclude_unset=True)
    )
    return FocusModeRead.model_validate(mode)


@router.delete("/{mode_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_focus_mode(
    mode_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = FocusModeService(db)
    await service.delete_mode(current_user.id, mode_id)
    return None

