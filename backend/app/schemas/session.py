"""Session request and response schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator

from app.models.enums import ParticipantResponseStatus, ParticipantRole, SessionStatus
from app.utils.request_validation import normalize_optional_text


class SessionCreateFromSuggestionRequest(BaseModel):
    suggestion_id: int
    title: str | None = Field(default=None, min_length=2, max_length=180)

    @field_validator("title", mode="before")
    @classmethod
    def normalize_optional_title_not_blank(
        cls, value: object, info: ValidationInfo
    ) -> object:
        return normalize_optional_text(value, field_name=info.field_name)


class SessionParticipantResponse(BaseModel):
    id: int
    session_id: int
    user_id: int
    participant_role: ParticipantRole
    collaboration_role: str
    response_status: ParticipantResponseStatus
    joined_at: datetime | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SessionResponse(BaseModel):
    id: int
    session_suggestion_id: int | None
    skill_id: int
    title: str
    scheduled_start_at: datetime
    scheduled_end_at: datetime
    status: SessionStatus
    created_by_user_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SessionDetailResponse(SessionResponse):
    participants: list[SessionParticipantResponse]
