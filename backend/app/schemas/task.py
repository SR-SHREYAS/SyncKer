"""Task request and response schemas."""

from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    ValidationInfo,
    field_validator,
    model_validator,
)

from app.models.enums import TaskPriority, TaskStatus
from app.utils.request_validation import (
    normalize_optional_text,
    normalize_required_text,
)


class TaskBase(BaseModel):
    title: str = Field(min_length=2, max_length=160)
    description: str | None = Field(default=None, max_length=2000)
    priority: TaskPriority
    status: TaskStatus = TaskStatus.PENDING
    estimated_minutes: int = Field(ge=15, le=1440)
    deadline_at: datetime | None = None
    planned_start_at: datetime | None = None
    planned_end_at: datetime | None = None
    skill_id: int | None = None

    @field_validator("title", mode="before")
    @classmethod
    def normalize_title_not_blank(cls, value: object, info: ValidationInfo) -> object:
        return normalize_required_text(value, field_name=info.field_name)

    @model_validator(mode="after")
    def validate_planned_task_time_range(self) -> "TaskBase":
        if (
            self.planned_start_at is not None
            and self.planned_end_at is not None
            and self.planned_end_at <= self.planned_start_at
        ):
            raise ValueError("planned_end_at must be after planned_start_at")
        return self


class TaskCreateRequest(TaskBase):
    pass


class TaskUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=160)
    description: str | None = Field(default=None, max_length=2000)
    priority: TaskPriority | None = None
    status: TaskStatus | None = None
    estimated_minutes: int | None = Field(default=None, ge=15, le=1440)
    deadline_at: datetime | None = None
    planned_start_at: datetime | None = None
    planned_end_at: datetime | None = None
    skill_id: int | None = None

    @field_validator("title", mode="before")
    @classmethod
    def normalize_optional_title_not_blank(
        cls, value: object, info: ValidationInfo
    ) -> object:
        return normalize_optional_text(value, field_name=info.field_name)

    @model_validator(mode="after")
    def validate_planned_task_time_range(self) -> "TaskUpdateRequest":
        if (
            self.planned_start_at is not None
            and self.planned_end_at is not None
            and self.planned_end_at <= self.planned_start_at
        ):
            raise ValueError("planned_end_at must be after planned_start_at")
        return self


class TaskResponse(TaskBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TeamTimetableParticipantResponse(BaseModel):
    user_id: int
    username: str
    email: EmailStr
    tasks: list[TaskResponse]


class TeamTimetableResponse(BaseModel):
    team_id: int
    participants: list[TeamTimetableParticipantResponse]
