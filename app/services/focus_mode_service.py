from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.focus_mode import FocusMode
from app.models.user import User
from app.repositories.focus_mode_repo import FocusModeRepository

# Default modes auto-created when a user registers
DEFAULT_MODES = [
    {
        "name": "Study",
        "emoji": "📖",
        "description": "Deep focus — learning and technology only.",
        "interest_slugs": ["learning", "technology"],
        "is_default": True,
        "is_child_safe": False,
        "is_system": True,
    },
    {
        "name": "Casual",
        "emoji": "☕",
        "description": "Relaxed browsing — entertainment, sports, art.",
        "interest_slugs": ["entertainment", "sports", "art"],
        "is_default": False,
        "is_child_safe": False,
        "is_system": True,
    },
    {
        "name": "Kids",
        "emoji": "🧸",
        "description": "Child-safe mode with approved interests only.",
        "interest_slugs": ["learning", "art"],
        "is_default": False,
        "is_child_safe": True,
        "is_system": True,
    },
]


class FocusModeService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = FocusModeRepository(db)

    # ---------- seeding ----------
    async def create_defaults_for_user(self, user_id: str) -> list[FocusMode]:
        existing = await self.repo.list_for_user(user_id)
        if existing:
            return existing
        modes = [FocusMode(user_id=user_id, **data) for data in DEFAULT_MODES]
        await self.repo.bulk_create(modes)
        return modes

    # ---------- reads ----------
    async def list_modes(self, user_id: str) -> list[FocusMode]:
        return await self.repo.list_for_user(user_id)

    async def get_mode_or_404(self, mode_id: str, user_id: str) -> FocusMode:
        mode = await self.repo.get(mode_id)
        if not mode or mode.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Focus mode not found",
            )
        return mode

    # ---------- writes ----------
    async def create_mode(
        self, user_id: str, name: str, emoji, description, interest_slugs, is_default
    ) -> FocusMode:
        if is_default:
            await self.repo.clear_default_flag(user_id)

        mode = FocusMode(
            user_id=user_id,
            name=name,
            emoji=emoji,
            description=description,
            interest_slugs=interest_slugs or [],
            is_default=is_default,
            is_child_safe=False,
            is_system=False,
        )
        return await self.repo.create(mode)

    async def update_mode(
        self, user_id: str, mode_id: str, **changes
    ) -> FocusMode:
        mode = await self.get_mode_or_404(mode_id, user_id)
        # Filter out None values so partial updates work
        changes = {k: v for k, v in changes.items() if v is not None}
        if not changes:
            return mode
        return await self.repo.update(mode, **changes)

    async def delete_mode(self, user_id: str, mode_id: str) -> None:
        mode = await self.get_mode_or_404(mode_id, user_id)
        if mode.is_default:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete the default mode. Set another mode as default first.",
            )
        await self.repo.delete(mode)

    # ---------- switching ----------
    async def switch_active_mode(
        self, user: User, mode_id: str | None
    ) -> FocusMode | None:
        print(f"\n[SWITCH] called with mode_id={mode_id!r}")
        print(f"[SWITCH] user.id={user.id!r}")
        print(f"[SWITCH] user.active_focus_mode_id before={user.active_focus_mode_id!r}")

        if mode_id is None:
            user.active_focus_mode_id = None
            await self.db.commit()
            print("[SWITCH] cleared active mode")
            return None

        mode = await self.repo.get(mode_id)
        print(f"[SWITCH] repo.get returned: {mode!r}")

        if not mode:
            print("[SWITCH] FAIL: mode not found by ID")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Focus mode not found",
            )

        if mode.user_id != user.id:
            print(f"[SWITCH] FAIL: user mismatch stored={mode.user_id!r} req={user.id!r}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Focus mode not found",
            )

        user.active_focus_mode_id = mode.id
        await self.db.commit()
        print(f"[SWITCH] SUCCESS: set active_focus_mode_id={mode.id!r}")
        return mode

    async def get_active_mode(self, user: User) -> FocusMode | None:
        if not user.active_focus_mode_id:
            return None
        mode = await self.repo.get(user.active_focus_mode_id)
        if mode and mode.user_id == user.id:
            return mode
        return None
