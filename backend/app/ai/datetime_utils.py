"""Shared datetime helpers for scheduler modules."""

from datetime import UTC, datetime


def normalize_datetime_to_utc(value: datetime) -> datetime:
    """Normalize datetimes to UTC-aware for scheduler comparisons.

    Naive datetimes are treated as UTC by contract in this scheduler layer.
    """
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)
