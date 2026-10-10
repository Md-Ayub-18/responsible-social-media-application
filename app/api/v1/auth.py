
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from app.core.age_utils import calculate_age, classify_account, tier_message
from app.core.rate_limit import limiter
from app.db.session import get_db
from app.dependencies import get_current_user, get_current_user_allow_inactive
from app.models.user import User
from app.schemas.user import (
    ChangeDateOfBirthRequest,
    SetDateOfBirthRequest,
    SetDateOfBirthResponse,
    TokenWithUser,
    UserCreate,
    UserLogin,
    UserRead,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


def _user_read_with_tier(user: User) -> UserRead:
    """Attach computed account_tier to UserRead."""
    data = UserRead.model_validate(user)
    if user.date_of_birth:
        data.account_tier = classify_account(user.date_of_birth)
    return data


# ---------- register ----------
@router.post(
    "/register",
    response_model=TokenWithUser,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("3/hour")
async def register(
    request: Request,
    response: Response,
    payload: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    user = await service.register(payload)
    token_data = service.issue_token(user)
    return {**token_data, "user": _user_read_with_tier(user)}


# ---------- set DOB (completes registration) ----------
@router.post("/set-date-of-birth", response_model=SetDateOfBirthResponse)
@limiter.limit("10/minute")
async def set_date_of_birth(
    request: Request,
    response: Response,
    payload: SetDateOfBirthRequest,
    current_user: User = Depends(get_current_user_allow_inactive),
    db: AsyncSession = Depends(get_db),
):
    """Complete registration by setting DOB. Activates the account."""
    tier = classify_account(payload.date_of_birth)
    age = calculate_age(payload.date_of_birth)
    if age < 0 or age > 120:
        raise HTTPException(400, "Please enter a valid date of birth")

    service = AuthService(db)
    user = await service.set_date_of_birth(current_user, payload.date_of_birth)

    return SetDateOfBirthResponse(
        user=_user_read_with_tier(user),
        tier=tier,
        message=tier_message(tier),
    )


# ---------- login ----------
@router.post("/login", response_model=TokenWithUser)
@limiter.limit("5/minute")
async def login(
    request: Request,
    response: Response,
    payload: UserLogin,
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    user = await service.authenticate(payload.email, payload.password)
    token_data = service.issue_token(user)
    return {**token_data, "user": _user_read_with_tier(user)}


# ---------- me ----------
@router.get("/me", response_model=UserRead)
async def me(current_user: User = Depends(get_current_user_allow_inactive)):
    return _user_read_with_tier(current_user)


# ---------- change DOB ----------
@router.patch("/me/date-of-birth", response_model=SetDateOfBirthResponse)
@limiter.limit("10/minute")
async def change_date_of_birth(
    request: Request,
    response: Response,
    payload: ChangeDateOfBirthRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Change DOB (30-day cooldown for existing users)."""
    from datetime import datetime, timedelta, timezone

    if current_user.last_dob_change_at:
        next_allowed = current_user.last_dob_change_at + timedelta(days=30)
        if datetime.now(timezone.utc) < next_allowed:
            days_left = (next_allowed - datetime.now(timezone.utc)).days + 1
            raise HTTPException(
                429,
                f"You can change your date of birth again in {days_left} day(s).",
            )

    tier = classify_account(payload.new_date_of_birth)
    age = calculate_age(payload.new_date_of_birth)
    if age < 0 or age > 120:
        raise HTTPException(400, "Please enter a valid date of birth")

    from app.core.age_utils import is_child_account
    from app.services.audit_service import AuditService

    old_dob = current_user.date_of_birth
    current_user.date_of_birth = payload.new_date_of_birth
    current_user.is_child_account = is_child_account(payload.new_date_of_birth)
    current_user.last_dob_change_at = datetime.now(timezone.utc)

    # Force Kids mode if now child; clear if no longer child
    from app.services.focus_mode_service import FocusModeService
    modes = await FocusModeService(db).list_modes(current_user.id)
    kids = next((m for m in modes if m.name == "Kids"), None)

    if current_user.is_child_account and kids:
        current_user.active_focus_mode_id = kids.id
    elif not current_user.is_child_account and current_user.active_focus_mode_id == (kids.id if kids else None):
        current_user.active_focus_mode_id = None

    await db.commit()
    await db.refresh(current_user)

    await AuditService(db).log(
        actor=current_user,
        action="dob_changed",
        target_type="user",
        target_id=current_user.id,
        reason=payload.reason or f"DOB changed to {payload.new_date_of_birth}",
        details={
            "old_dob": str(old_dob) if old_dob else None,
            "new_dob": str(payload.new_date_of_birth),
            "new_tier": tier,
        },
    )

    return SetDateOfBirthResponse(
        user=_user_read_with_tier(current_user),
        tier=tier,
        message=f"Date of birth updated. Your tier is now {tier}.",
    )
