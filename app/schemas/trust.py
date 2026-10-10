from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

# ---------- Reports ----------

class ReportCreate(BaseModel):
    target_type: str = Field(pattern="^(post|comment|user|contribution)$")
    target_id: str
    category: str = Field(pattern="^(spam|harassment|misinformation|hate|ai_undisclosed|other)$")
    description: str | None = Field(default=None, max_length=1000)


class ReportRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    reporter_id: str
    target_type: str
    target_id: str
    category: str
    description: str | None
    status: str
    resolution_note: str | None
    created_at: datetime


class ReportResolve(BaseModel):
    status: str = Field(pattern="^(resolved|dismissed)$")
    note: str | None = Field(default=None, max_length=500)


# ---------- Guardian ----------

class ChildCreate(BaseModel):
    """Guardian creates a child account."""
    email: str
    username: str = Field(min_length=3, max_length=50)
    display_name: str | None = None
    password: str = Field(min_length=8, max_length=128)


class ChildRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    username: str
    display_name: str | None
    is_child_account: bool
    is_active: bool
    created_at: datetime


class GuardianLinkRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    guardian_id: str
    child_id: str
    can_view_posts: bool
    can_restrict_dms: bool
    can_manage_focus: bool
    created_at: datetime


# ---------- Bot ----------

class BotSignalRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    score: float
    verdict: str
    reasons: list[str]
    details: dict
    last_evaluated_at: datetime | None


class BotSignalWithUser(BotSignalRead):
    username: str | None = None
    display_name: str | None = None


class EngagementSignalRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    post_id: str
    score: float
    verdict: str
    reasons: list[str]
    details: dict
    created_at: datetime


class EngagementSignalWithPost(EngagementSignalRead):
    post_text: str | None = None
    post_author_id: str | None = None
