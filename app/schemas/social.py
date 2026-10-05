from pydantic import BaseModel, ConfigDict


class PublicUserBrief(BaseModel):
    """Minimal user info for follower/following lists."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    username: str
    display_name: str | None
    is_private: bool = False


class FollowResponse(BaseModel):
    user_id: str
    username: str
    is_following: bool
    follower_count: int


class FollowStatusResponse(BaseModel):
    user_id: str
    username: str
    is_following: bool
    follower_count: int
    following_count: int


class BlockResponse(BaseModel):
    user_id: str
    username: str
    is_blocked: bool


class BlockedUser(BaseModel):
    user_id: str
    username: str
    display_name: str | None


class PrivacyUpdateRequest(BaseModel):
    is_private: bool
