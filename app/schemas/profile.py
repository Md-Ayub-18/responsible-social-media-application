from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class PublicProfile(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    username: str
    display_name: str | None
    is_moderator: bool
    is_child_account: bool
    is_private: bool = False
    date_of_birth: date | None = None
    account_tier: str | None = None
    created_at: datetime

    # computed
    post_count: int = 0
    likes_received: int = 0
    follower_count: int = 0
    following_count: int = 0
    is_following: bool = False

class UserProfileResponse(BaseModel):
    profile: PublicProfile
    posts: list[dict]  # PostReadWithAuthor shape
