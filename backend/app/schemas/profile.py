"""Profile request and response schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator

from app.models.enums import ProfileRole
from app.utils.request_validation import normalize_optional_text, normalize_required_text


class ProfileBase(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    bio: str | None = Field(default=None, max_length=2000)
    role: ProfileRole
    timezone: str = Field(min_length=2, max_length=64)

    @field_validator("full_name", "timezone", mode="before")
    @classmethod
    def normalize_required_text_fields(cls, value: object, info: ValidationInfo) -> object:
        return normalize_required_text(value, field_name=info.field_name)


class ProfileCreateRequest(ProfileBase):
    pass


class ProfileUpdateRequest(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=120)
    bio: str | None = Field(default=None, max_length=2000)
    role: ProfileRole | None = None
    timezone: str | None = Field(default=None, min_length=2, max_length=64)

    @field_validator("full_name", "timezone", mode="before")
    @classmethod
    def normalize_optional_text_fields(cls, value: object, info: ValidationInfo) -> object:
        return normalize_optional_text(value, field_name=info.field_name)


class ProfileResponse(ProfileBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
