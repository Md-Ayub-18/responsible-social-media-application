from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.interest import InterestRead
from app.services.interest_service import InterestService

router = APIRouter(prefix="/interests", tags=["interests"])


@router.get("/", response_model=list[InterestRead])
async def list_interests(db: AsyncSession = Depends(get_db)):
    """Return all available interests users can choose from."""
    service = InterestService(db)
    return await service.list_interests()


@router.get("/{interest_id}", response_model=InterestRead)
async def get_interest(interest_id: str, db: AsyncSession = Depends(get_db)):
    """Return a specific interest by ID."""
    service = InterestService(db)
    return await service.get_interest_or_404(interest_id)
