"""Scheduling request and response schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import SuggestionStatus


class SuggestionGenerationRequest(BaseModel):
    participant_user_ids: list[int] = Field(min_length=2)
    collaboration_title: str = Field(min_length=2, max_length=180)
    skill_id: int | None = None
    window_start_at: datetime | None = None
    window_end_at: datetime | None = None
    minimum_duration_minutes: int = Field(default=30, ge=15, le=240)

    @field_validator("collaboration_title")
    @classmethod
    def validate_collaboration_title_not_blank(cls, value: str) -> str:
        normalized_value = value.strip()
        if not normalized_value:
            raise ValueError("collaboration_title must not be empty")
        return normalized_value


class SessionSuggestionResponse(BaseModel):
    id: int
    generated_for_user_id: int
    participant_user_ids: list[int]
    collaboration_title: str
    skill_id: int
    suggested_start_at: datetime
    suggested_end_at: datetime
    score: float
    status: SuggestionStatus
    explanation: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SuggestionStatusUpdateRequest(BaseModel):
    status: SuggestionStatus
