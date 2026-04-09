"""Scheduling hard and soft constraints."""

from datetime import date, datetime, time, timedelta

from app.ai.datetime_utils import normalize_datetime_to_utc


def to_datetime_range(
    target_date: date, start_time: time, end_time: time
) -> tuple[datetime, datetime]:
    """Convert a day and time block into concrete datetimes."""
    return (
        datetime.combine(target_date, start_time),
        datetime.combine(target_date, end_time),
    )


def resolve_window(
    window_start_at: datetime | None,
    window_end_at: datetime | None,
    minimum_duration_minutes: int,
) -> tuple[datetime, datetime]:
    """Pick a valid scheduling window for the rule engine."""
    start = normalize_datetime_to_utc(window_start_at or datetime.now())
    end = normalize_datetime_to_utc(window_end_at or (start + timedelta(days=3)))

    if end <= start:
        end = start + timedelta(minutes=minimum_duration_minutes)

    return start, end


def overlaps(
    left_start: datetime, left_end: datetime, right_start: datetime, right_end: datetime
) -> bool:
    """Return whether two datetime ranges overlap."""
    return left_start < right_end and right_start < left_end


def is_slot_blocked(
    *,
    slot_start: datetime,
    slot_end: datetime,
    blocked_ranges: list[tuple[datetime, datetime]]
) -> bool:
    """Return whether a candidate slot conflicts with any blocked range."""
    return any(
        overlaps(slot_start, slot_end, blocked_start, blocked_end)
        for blocked_start, blocked_end in blocked_ranges
    )
