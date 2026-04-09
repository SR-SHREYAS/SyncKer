"""Lightweight type contracts for scheduler helper inputs."""

from datetime import date, datetime, time
from typing import Protocol


class SkillTaggedTask(Protocol):
    """Minimal task shape needed by scoring and skill filtering."""

    skill_id: int | None


class ParticipantOwnedRecord(Protocol):
    """Minimal record shape scoped to one participant."""

    user_id: int | None


class ParticipantTimeBlock(ParticipantOwnedRecord, Protocol):
    """Minimal time-block shape used for availability/routine intersections."""

    is_recurring: bool
    day_of_week: int | None
    specific_date: date | None
    start_time: time
    end_time: time


class ParticipantPlannedTask(
    ParticipantOwnedRecord,
    SkillTaggedTask,
    Protocol,
):
    """Minimal task shape used for participant busy interval extraction."""

    planned_start_at: datetime | None
    planned_end_at: datetime | None
