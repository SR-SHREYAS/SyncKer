"""Availability intersection logic."""

from datetime import datetime, timedelta

from app.ai.constraints import is_slot_blocked


def build_blocked_ranges(
    *,
    routine_blocks: list[object],
    window_start_at: datetime,
    window_end_at: datetime,
) -> list[tuple[datetime, datetime]]:
    """Build concrete blocked ranges from routine blocks inside the current window."""
    blocked_ranges: list[tuple[datetime, datetime]] = []
    current_date = window_start_at.date()

    while current_date <= window_end_at.date():
        for block in routine_blocks:
            if block.is_recurring:
                if block.day_of_week != current_date.weekday():
                    continue
            elif block.specific_date != current_date:
                continue

            blocked_ranges.append(
                (
                    datetime.combine(current_date, block.start_time),
                    datetime.combine(current_date, block.end_time),
                )
            )
        current_date += timedelta(days=1)

    return blocked_ranges


def pick_first_common_slot(
    *,
    window_start_at: datetime,
    window_end_at: datetime,
    minimum_duration_minutes: int,
    availability_blocks: list[object],
    routine_blocks: list[object],
) -> tuple[datetime, datetime]:
    """Return the first candidate slot that respects availability and routines.

    This MVP version uses recurring and one-off availability blocks plus routine blocks.
    """
    blocked_ranges = build_blocked_ranges(
        routine_blocks=routine_blocks,
        window_start_at=window_start_at,
        window_end_at=window_end_at,
    )
    current_date = window_start_at.date()

    while current_date <= window_end_at.date():
        for block in availability_blocks:
            if block.is_recurring:
                if block.day_of_week != current_date.weekday():
                    continue
            elif block.specific_date != current_date:
                continue

            slot_start = datetime.combine(current_date, block.start_time)
            slot_end = slot_start + timedelta(minutes=minimum_duration_minutes)
            block_end = datetime.combine(current_date, block.end_time)

            if slot_start < window_start_at:
                slot_start = window_start_at
                slot_end = slot_start + timedelta(minutes=minimum_duration_minutes)

            if slot_end > block_end or slot_end > window_end_at:
                continue

            if is_slot_blocked(slot_start=slot_start, slot_end=slot_end, blocked_ranges=blocked_ranges):
                continue

            return slot_start, slot_end

        current_date += timedelta(days=1)

    fallback_start = window_start_at
    fallback_end = window_start_at + timedelta(minutes=minimum_duration_minutes)
    return fallback_start, fallback_end
