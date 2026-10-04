from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.repositories.user_repo import UserRepository
from app.schemas.user import UserCreate


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = UserRepository(db)

    async def register(self, payload: UserCreate) -> User:
        """Create an INACTIVE account without DOB. DOB is set later."""
        # Duplicate checks
        if await self.repo.get_by_email(payload.email):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email is already registered",
            )
        if await self.repo.get_by_username(payload.username):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username is already taken",
            )

        # Create account as inactive, no DOB yet
        user = User(
            email=payload.email,
            username=payload.username,
            display_name=payload.display_name or payload.username,
            hashed_password=hash_password(payload.password),
            date_of_birth=None,
            is_child_account=False,
            is_active=False,
        )
        user = await self.repo.create(user)

        # Seed default focus modes
        from app.services.focus_mode_service import FocusModeService
        await FocusModeService(self.db).create_defaults_for_user(user.id)

        return user

    async def set_date_of_birth(self, user: User, dob) -> User:
        """Set DOB for the first time and activate the account."""
        from datetime import datetime, timezone

        from app.core.age_utils import is_child_account

        if user.date_of_birth is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Date of birth already set. Use the change endpoint to modify.",
            )

        child = is_child_account(dob)
        user.date_of_birth = dob
        user.is_child_account = child
        user.is_active = True
        user.last_dob_change_at = datetime.now(timezone.utc)

        # Force Kids mode if child
        if child:
            from app.services.focus_mode_service import FocusModeService
            modes = await FocusModeService(self.db).list_modes(user.id)
            kids = next((m for m in modes if m.name == "Kids"), None)
            if kids:
                user.active_focus_mode_id = kids.id

        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def authenticate(self, email: str, password: str) -> User:
        """Authenticate a user by email + password. Returns the User."""
        user = await self.repo.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is inactive. Please complete your registration.",
            )
        return user

    def issue_token(self, user: User) -> dict:
        token = create_access_token(subject=user.id)
        return {
            "access_token": token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        }
