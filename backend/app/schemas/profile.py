"""Profile request and response schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ProfileRole


class ProfileBase(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    bio: str | None = Field(default=None, max_length=2000)
    role: ProfileRole
    timezone: str = Field(min_length=2, max_length=64)


class ProfileCreateRequest(ProfileBase):
    pass


class ProfileUpdateRequest(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=120)
    bio: str | None = Field(default=None, max_length=2000)
    role: ProfileRole | None = None
    timezone: str | None = Field(default=None, min_length=2, max_length=64)


class ProfileResponse(ProfileBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
