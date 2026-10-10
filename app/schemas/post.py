from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PostAuthor(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    username: str
    display_name: str | None


class PostCreate(BaseModel):
    text: str = Field(min_length=1, max_length=5000)
    interest_slug: str = Field(min_length=1, max_length=50)
    media_urls: list[str] = Field(default_factory=list)
    community_id: str | None = None


class PostRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    author_id: str
    text: str
    interest_slug: str
    media_urls: list[str]
    community_id: str | None
    ai_generated: bool
    ai_label_shown: bool
    moderation_status: str
    moderation_reason: str | None
    media_moderation_status: str             
    media_moderation_reason: str | None 
    is_hidden: bool
    created_at: datetime
    updated_at: datetime


class PostReadWithAuthor(PostRead):
    author: PostAuthor | None = None
    reaction_count: int = 0
    is_liked_by_me: bool = False


class FeedResponse(BaseModel):
    posts: list[PostReadWithAuthor]
    count: int
    applied_interest_slugs: list[str]
    focus_mode_applied: bool
    focus_mode_name: str | None = None


class ReactionToggleResponse(BaseModel):
    post_id: str
    is_liked: bool
    reaction_count: int
