from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class FocusModeBase(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    emoji: str | None = Field(default=None, max_length=10)
    description: str | None = Field(default=None, max_length=300)
    interest_slugs: list[str] = Field(default_factory=list)


class FocusModeCreate(FocusModeBase):
    is_default: bool = False


class FocusModeUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=50)
    emoji: str | None = Field(default=None, max_length=10)
    description: str | None = Field(default=None, max_length=300)
    interest_slugs: list[str] | None = None


class FocusModeRead(FocusModeBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    is_default: bool
    is_child_safe: bool
    is_system: bool
    created_at: datetime
    updated_at: datetime


class FocusModeListResponse(BaseModel):
    modes: list[FocusModeRead]
    count: int


class ActiveFocusModeResponse(BaseModel):
    active_mode: FocusModeRead | None
    is_active: bool


class SwitchFocusModeRequest(BaseModel):
    focus_mode_id: str | None = Field(
        default=None,
        description="Focus mode UUID. Pass null to clear the active mode.",
    )

    @field_validator("focus_mode_id")
    @classmethod
    def strip_whitespace(cls, v):
        return v.strip() if isinstance(v, str) else v