"""Routine request and response schemas."""

from datetime import date, datetime, time

from pydantic import BaseModel, ConfigDict, Field, model_validator


class RoutineBlockBase(BaseModel):
    title: str = Field(min_length=2, max_length=160)
    day_of_week: int | None = Field(default=None, ge=0, le=6)
    start_time: time
    end_time: time
    is_recurring: bool = True
    specific_date: date | None = None

    @model_validator(mode="after")
    def validate_block(self) -> "RoutineBlockBase":
        if self.start_time >= self.end_time:
            raise ValueError("start_time must be earlier than end_time")
        if self.is_recurring and self.day_of_week is None:
            raise ValueError("day_of_week is required for recurring blocks")
        if not self.is_recurring and self.specific_date is None:
            raise ValueError("specific_date is required for one-off blocks")
        return self


class RoutineBlockCreateRequest(RoutineBlockBase):
    pass


class RoutineBlockUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=160)
    day_of_week: int | None = Field(default=None, ge=0, le=6)
    start_time: time | None = None
    end_time: time | None = None
    is_recurring: bool | None = None
    specific_date: date | None = None


class RoutineBlockResponse(RoutineBlockBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
