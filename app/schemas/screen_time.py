from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class HeartbeatResponse(BaseModel):
    session_id: str
    duration_seconds: int
    today_total_seconds: int
    limit_seconds: int
    limit_reached: bool


class TodayScreenTime(BaseModel):
    today_total_seconds: int
    today_total_minutes: int
    limit_minutes: int
    limit_reached: bool
    break_reminders_enabled: bool
    is_child_account: bool


class UpdateLimitRequest(BaseModel):
    daily_screen_time_limit_minutes: int = Field(ge=5, le=480)   # 5 min to 8 hours
    break_reminders_enabled: bool = True


class ScreenSessionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    started_at: datetime
    ended_at: datetime | None
    duration_seconds: int
