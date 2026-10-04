from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.interest import InterestRead, InterestSelect, UserInterestsResponse
from app.services.interest_service import InterestService

router = APIRouter(prefix="/users/me", tags=["users"])


@router.get("/interests", response_model=UserInterestsResponse)
async def my_interests(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = InterestService(db)
    items = await service.list_user_interests(current_user.id)
    return UserInterestsResponse(
        interests=[InterestRead.model_validate(i) for i in items],
        count=len(items),
    )


@router.post(
    "/interests",
    response_model=InterestRead,
    status_code=status.HTTP_201_CREATED,
)
async def select_interest(
    payload: InterestSelect,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = InterestService(db)
    interest = await service.add_user_interest(
        current_user.id, payload.interest_id, payload.slug
    )
    return InterestRead.model_validate(interest)


@router.delete(
    "/interests/{interest_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def deselect_interest(
    interest_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = InterestService(db)
    await service.remove_user_interest(current_user.id, interest_id)
