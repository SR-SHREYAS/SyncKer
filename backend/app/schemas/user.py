"""User request and response schemas."""

from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    ValidationInfo,
    field_validator,
)

from app.utils.request_validation import normalize_optional_text


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    username: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserUpdateRequest(BaseModel):
    username: str | None = Field(default=None, min_length=3, max_length=50)

    @field_validator("username", mode="before")
    @classmethod
    def normalize_optional_username_not_blank(cls, value: object, info: ValidationInfo) -> object:
        return normalize_optional_text(value, field_name=info.field_name)
