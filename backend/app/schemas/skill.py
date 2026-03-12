"""Skill request and response schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ProficiencyLevel


class SkillCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    slug: str = Field(min_length=2, max_length=120)
    description: str | None = Field(default=None, max_length=2000)


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
