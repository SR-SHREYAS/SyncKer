"""Availability intersection logic."""

from datetime import datetime, timedelta


def pick_first_common_slot(
    *,
    window_start_at: datetime,
    minimum_duration_minutes: int,
) -> tuple[datetime, datetime]:
    """Return the first candidate slot inside the current request window.

    This is a placeholder until real availability intersection is added.
    """
    suggested_start_at = window_start_at + timedelta(hours=1)
    suggested_end_at = suggested_start_at + timedelta(minutes=minimum_duration_minutes)
    return suggested_start_at, suggested_end_at
