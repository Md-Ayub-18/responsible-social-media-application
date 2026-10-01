from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.user import (
    TokenWithUser,
    UserCreate,
    UserLogin,
    UserRead,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=TokenWithUser,
    status_code=status.HTTP_201_CREATED,
)
async def register(payload: UserCreate, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    user = await service.register(payload)
    token_data = service.issue_token(user)
    return {**token_data, "user": UserRead.model_validate(user)}


@router.post("/login", response_model=TokenWithUser)
async def login(payload: UserLogin, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    user = await service.authenticate(payload.email, payload.password)
    token_data = service.issue_token(user)
    return {**token_data, "user": UserRead.model_validate(user)}


@router.get("/me", response_model=UserRead)
async def me(current_user: User = Depends(get_current_user)):
    return UserRead.model_validate(current_user)