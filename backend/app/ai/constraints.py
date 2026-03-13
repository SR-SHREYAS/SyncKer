"""Scheduling hard and soft constraints."""

from datetime import datetime, timedelta


def resolve_window(
    window_start_at: datetime | None,
    window_end_at: datetime | None,
    minimum_duration_minutes: int,
) -> tuple[datetime, datetime]:
    """Pick a valid scheduling window for the rule engine."""
    start = window_start_at or datetime.utcnow()
    end = window_end_at or (start + timedelta(days=3))

    if end <= start:
        end = start + timedelta(minutes=minimum_duration_minutes)

    return start, end
