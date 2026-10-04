from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CommunityCreate(BaseModel):
    name: str = Field(min_length=3, max_length=100)
    description: str | None = Field(default=None, max_length=1000)
    emoji: str | None = Field(default=None, max_length=10)
    interest_slug: str = Field(min_length=1, max_length=50)
    is_public: bool = True


class CommunityUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=3, max_length=100)
    description: str | None = Field(default=None, max_length=1000)
    emoji: str | None = Field(default=None, max_length=10)
    is_public: bool | None = None


class CommunityRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    slug: str
    name: str
    description: str | None
    emoji: str | None
    interest_slug: str
    creator_id: str
    is_public: bool
    member_count: int
    created_at: datetime
    updated_at: datetime


class CommunityWithMembership(CommunityRead):
    """Community details + the calling user's membership status."""

    is_member: bool = False
    is_moderator: bool = False


class MemberRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    community_id: str
    role: str
    created_at: datetime

    # optional user info (populated in service)
    username: str | None = None
    display_name: str | None = None


class CommunityListResponse(BaseModel):
    communities: list[CommunityWithMembership]
    count: int


class JoinLeaveResponse(BaseModel):
    community_id: str
    is_member: bool
    member_count: int
    message: str
