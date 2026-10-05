from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=50)
    display_name: str | None = Field(default=None, max_length=100)


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)
    # date_of_birth is NOT here — set later via /set-date-of-birth


class SetDateOfBirthRequest(BaseModel):
    date_of_birth: date


class ChangeDateOfBirthRequest(BaseModel):
    new_date_of_birth: date
    reason: str | None = Field(default=None, max_length=500)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserRead(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    is_active: bool
    is_verified: bool
    is_child_account: bool
    is_moderator: bool
    is_private: bool
    date_of_birth: date | None
    account_tier: str | None = None
    created_at: datetime


class SetDateOfBirthResponse(BaseModel):
    user: UserRead
    tier: str
    message: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenWithUser(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserRead
