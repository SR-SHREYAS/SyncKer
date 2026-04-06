"""Team request and response schemas."""

from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    ValidationInfo,
    field_validator,
)

from app.utils.request_validation import (
    normalize_optional_text_to_none,
    normalize_required_text,
)


class TeamCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    description: str | None = Field(default=None, max_length=500)

    @field_validator("name", mode="before")
    @classmethod
    def normalize_name_not_blank(cls, value: object, info: ValidationInfo) -> object:
        return normalize_required_text(value, field_name=info.field_name)

    @field_validator("description", mode="before")
    @classmethod
    def normalize_description_blank_to_none(cls, value: object) -> object:
        return normalize_optional_text_to_none(value)


class TeamAddParticipantRequest(BaseModel):
    participant_user_id: int


class TeamResponse(BaseModel):
    id: int
    name: str
    description: str | None
    owner_user_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TeamMemberResponse(BaseModel):
    team_member_id: int
    team_id: int
    user_id: int
    username: str
    email: EmailStr
    joined_at: datetime
