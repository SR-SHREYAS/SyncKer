"""Auth request and response schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, ValidationInfo, field_validator

from app.utils.request_validation import normalize_required_text


class RegisterRequest(BaseModel):
    """Input schema for account creation.

    Schemas define the shape of incoming and outgoing API data.
    """

    email: EmailStr
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("username", "password", mode="before")
    @classmethod
    def normalize_non_empty_text_fields(cls, value: object, info: ValidationInfo) -> object:
        return normalize_required_text(value, field_name=info.field_name)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    @field_validator("password", mode="before")
    @classmethod
    def normalize_password_non_empty(cls, value: object, info: ValidationInfo) -> object:
        return normalize_required_text(value, field_name=info.field_name)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime


class AuthUserResponse(BaseModel):
    id: int
    email: EmailStr
    username: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class AuthResponse(BaseModel):
    user: AuthUserResponse
    token: TokenResponse
