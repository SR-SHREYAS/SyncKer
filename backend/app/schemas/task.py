"""Task request and response schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import TaskPriority, TaskStatus


class TaskBase(BaseModel):
    title: str = Field(min_length=2, max_length=160)
    description: str | None = Field(default=None, max_length=2000)
    priority: TaskPriority
    status: TaskStatus = TaskStatus.PENDING
    estimated_minutes: int = Field(ge=15, le=1440)
    deadline_at: datetime | None = None
    skill_id: int | None = None


class TaskCreateRequest(TaskBase):
    pass


class TaskUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=160)
    description: str | None = Field(default=None, max_length=2000)
    priority: TaskPriority | None = None
    status: TaskStatus | None = None
    estimated_minutes: int | None = Field(default=None, ge=15, le=1440)
    deadline_at: datetime | None = None
    skill_id: int | None = None


class TaskResponse(TaskBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
