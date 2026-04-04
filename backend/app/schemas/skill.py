"""Skill request and response schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import ProficiencyLevel
from app.utils.request_validation import normalize_optional_text_to_none


class SkillCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    slug: str = Field(min_length=2, max_length=120)
    description: str | None = Field(default=None, max_length=2000)

    @field_validator("name", "slug")
    @classmethod
    def validate_non_empty_text_fields(cls, value: str) -> str:
        normalized_value = value.strip()
        if not normalized_value:
            raise ValueError("must not be empty")
        return normalized_value

    @field_validator("description")
    @classmethod
    def normalize_description(cls, value: str | None) -> str | None:
        return normalize_optional_text_to_none(value)


class SkillResponse(SkillCreateRequest):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserSkillCreateRequest(BaseModel):
    skill_id: int
    proficiency_level: ProficiencyLevel
    is_teaching: bool = False
    is_learning: bool = True


class UserSkillResponse(BaseModel):
    id: int
    user_id: int
    skill_id: int
    proficiency_level: ProficiencyLevel
    is_teaching: bool
    is_learning: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
