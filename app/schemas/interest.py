
from pydantic import BaseModel, ConfigDict


class InterestRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    slug: str
    name: str
    emoji: str | None
    description: str | None
    is_active: bool


class InterestSelect(BaseModel):
    """Payload for POST /users/me/interests — accepts either slug or id."""

    interest_id: str | None = None
    slug: str | None = None


class UserInterestsResponse(BaseModel):
    interests: list[InterestRead]
    count: int
