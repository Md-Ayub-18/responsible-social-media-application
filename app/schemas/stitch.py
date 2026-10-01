from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


# ---------- Project ----------

class StitchProjectCreate(BaseModel):
    title: str = Field(min_length=3, max_length=150)
    description: str | None = Field(default=None, max_length=1000)
    interest_slug: str = Field(min_length=1, max_length=50)


class StitchProjectUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=150)
    description: str | None = Field(default=None, max_length=1000)
    allow_contributions: bool | None = None
    status: str | None = Field(default=None, pattern="^(open|in_review|stitched|cancelled)$")


class StitchProjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    moderator_id: str
    title: str
    description: str | None
    interest_slug: str
    status: str
    allow_contributions: bool
    stitched_video_url: str | None
    stitch_error: str | None
    created_at: datetime
    updated_at: datetime


class StitchProjectDetail(StitchProjectRead):
    contributions: list["ContributionRead"] = []


# ---------- Contribution ----------

class ContributionCreate(BaseModel):
    caption: str | None = Field(default=None, max_length=500)
    consent_given: bool


class ContributionModerate(BaseModel):
    """Moderator action on a contribution."""

    status: str = Field(pattern="^(approved|rejected)$")
    rejection_reason: str | None = Field(default=None, max_length=500)
    order_index: int | None = None


class ContributionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    contributor_id: str
    video_url: str
    caption: str | None
    duration_seconds: float | None
    consent_given: bool
    status: str
    rejection_reason: str | None
    order_index: int | None
    created_at: datetime
    updated_at: datetime


# ---------- Stitch result ----------

class StitchResult(BaseModel):
    project_id: str
    status: str
    stitched_video_url: str | None
    contribution_count: int
    message: str


# Resolve forward refs
StitchProjectDetail.model_rebuild()