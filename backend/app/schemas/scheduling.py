"""Scheduling request and response schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import SuggestionStatus


class SuggestionGenerationRequest(BaseModel):
    learner_user_id: int
    mentor_user_id: int
    skill_id: int
    window_start_at: datetime | None = None
    window_end_at: datetime | None = None
    minimum_duration_minutes: int = Field(default=30, ge=15, le=240)


class SessionSuggestionResponse(BaseModel):
    id: int
    generated_for_user_id: int
    mentor_user_id: int
    learner_user_id: int
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
