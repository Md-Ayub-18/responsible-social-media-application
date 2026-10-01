from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PublicProfile(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    username: str
    display_name: str | None
    is_moderator: bool
    is_child_account: bool
    created_at: datetime

    # computed
    post_count: int = 0
    likes_received: int = 0


class UserProfileResponse(BaseModel):
    profile: PublicProfile
    posts: list[dict]  # PostReadWithAuthor shape