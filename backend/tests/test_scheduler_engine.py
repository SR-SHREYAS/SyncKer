from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

from app.ai.scheduler_engine import SchedulerEngine


def test_scheduler_engine_returns_slot_inside_window() -> None:
    engine = SchedulerEngine()
    now = datetime.now(UTC).replace(hour=9, minute=0, second=0, microsecond=0)

    availability = [
        SimpleNamespace(
            user_id=1,
            day_of_week=now.weekday(),
            start_time=(now + timedelta(hours=1)).time(),
            end_time=(now + timedelta(hours=3)).time(),
            is_recurring=True,
            specific_date=None,
        ),
        SimpleNamespace(
            user_id=2,
            day_of_week=now.weekday(),
            start_time=(now + timedelta(hours=1)).time(),
            end_time=(now + timedelta(hours=3)).time(),
            is_recurring=True,
            specific_date=None,
        ),
    ]

    result = engine.generate(
        participant_user_ids=[1, 2],
        skill_id=10,
        minimum_duration_minutes=60,
        window_start_at=now,
        window_end_at=now + timedelta(days=1),
        tasks=[],
        availability_blocks=availability,
        routine_blocks=[],
    )

    assert result["suggested_start_at"] >= now
    assert result["suggested_end_at"] > result["suggested_start_at"]
    assert result["slot_reason"] == "found"
    assert result["score"] >= 10


def test_scheduler_engine_scores_related_tasks_higher() -> None:
    engine = SchedulerEngine()
    now = datetime.now(UTC).replace(hour=9, minute=0, second=0, microsecond=0)
    availability = [
        SimpleNamespace(
            user_id=1,
            day_of_week=now.weekday(),
            start_time=(now + timedelta(hours=1)).time(),
            end_time=(now + timedelta(hours=4)).time(),
            is_recurring=True,
            specific_date=None,
        ),
        SimpleNamespace(
            user_id=2,
            day_of_week=now.weekday(),
            start_time=(now + timedelta(hours=1)).time(),
            end_time=(now + timedelta(hours=4)).time(),
            is_recurring=True,
            specific_date=None,
        ),
    ]
    related_task = SimpleNamespace(
        user_id=1,
        skill_id=10,
        planned_start_at=None,
        planned_end_at=None,
    )

    without_tasks = engine.generate(
        participant_user_ids=[1, 2],
        skill_id=10,
        minimum_duration_minutes=60,
        window_start_at=now,
        window_end_at=now + timedelta(days=1),
        tasks=[],
        availability_blocks=availability,
        routine_blocks=[],
    )
    with_tasks = engine.generate(
        participant_user_ids=[1, 2],
        skill_id=10,
        minimum_duration_minutes=60,
        window_start_at=now,
        window_end_at=now + timedelta(days=1),
        tasks=[related_task],
        availability_blocks=availability,
        routine_blocks=[],
    )

    assert with_tasks["score"] > without_tasks["score"]


def test_scheduler_engine_finds_true_common_slot_for_three_participants() -> None:
    engine = SchedulerEngine()
    now = datetime.now(UTC).replace(hour=9, minute=0, second=0, microsecond=0)
    availability = [
        SimpleNamespace(
            user_id=1,
            day_of_week=now.weekday(),
            start_time=(now + timedelta(hours=0)).time(),
            end_time=(now + timedelta(hours=3)).time(),
            is_recurring=True,
            specific_date=None,
        ),
        SimpleNamespace(
            user_id=2,
            day_of_week=now.weekday(),
            start_time=(now + timedelta(hours=1)).time(),
            end_time=(now + timedelta(hours=4)).time(),
            is_recurring=True,
            specific_date=None,
        ),
        SimpleNamespace(
            user_id=3,
            day_of_week=now.weekday(),
            start_time=(now + timedelta(hours=1, minutes=30)).time(),
            end_time=(now + timedelta(hours=2, minutes=30)).time(),
            is_recurring=True,
            specific_date=None,
        ),
    ]

    result = engine.generate(
        participant_user_ids=[1, 2, 3],
        skill_id=10,
        minimum_duration_minutes=30,
        window_start_at=now,
        window_end_at=now + timedelta(days=1),
        tasks=[],
        availability_blocks=availability,
        routine_blocks=[],
    )

    expected_start = now + timedelta(hours=1, minutes=30)
    assert result["suggested_start_at"] == expected_start
    assert result["suggested_end_at"] == expected_start + timedelta(minutes=30)
    assert result["slot_reason"] == "found"


def test_scheduler_engine_applies_participant_routine_blocks_in_intersection() -> None:
    engine = SchedulerEngine()
    now = datetime.now(UTC).replace(hour=9, minute=0, second=0, microsecond=0)
    availability = [
        SimpleNamespace(
            user_id=1,
            day_of_week=now.weekday(),
            start_time=(now + timedelta(hours=0)).time(),
            end_time=(now + timedelta(hours=3)).time(),
            is_recurring=True,
            specific_date=None,
        ),
        SimpleNamespace(
            user_id=2,
            day_of_week=now.weekday(),
            start_time=(now + timedelta(hours=0)).time(),
            end_time=(now + timedelta(hours=3)).time(),
            is_recurring=True,
            specific_date=None,
        ),
        SimpleNamespace(
            user_id=3,
            day_of_week=now.weekday(),
            start_time=(now + timedelta(hours=0)).time(),
            end_time=(now + timedelta(hours=3)).time(),
            is_recurring=True,
            specific_date=None,
        ),
    ]
    routine_blocks = [
        SimpleNamespace(
            user_id=2,
            day_of_week=now.weekday(),
            start_time=(now + timedelta(hours=0)).time(),
            end_time=(now + timedelta(hours=1)).time(),
            is_recurring=True,
            specific_date=None,
        )
    ]

    result = engine.generate(
        participant_user_ids=[1, 2, 3],
        skill_id=10,
        minimum_duration_minutes=60,
        window_start_at=now,
        window_end_at=now + timedelta(days=1),
        tasks=[],
        availability_blocks=availability,
        routine_blocks=routine_blocks,
    )

    expected_start = now + timedelta(hours=1)
    assert result["suggested_start_at"] == expected_start
    assert result["suggested_end_at"] == expected_start + timedelta(hours=1)
    assert result["slot_reason"] == "found"


def test_scheduler_engine_treats_missing_availability_as_full_window() -> None:
    engine = SchedulerEngine()
    now = datetime.now(UTC).replace(hour=9, minute=0, second=0, microsecond=0)

    availability = [
        SimpleNamespace(
            user_id=1,
            day_of_week=now.weekday(),
            start_time=(now + timedelta(hours=1)).time(),
            end_time=(now + timedelta(hours=3)).time(),
            is_recurring=True,
            specific_date=None,
        )
    ]

    result = engine.generate(
        participant_user_ids=[1, 2],
        skill_id=10,
        minimum_duration_minutes=60,
        window_start_at=now,
        window_end_at=now + timedelta(hours=8),
        tasks=[],
        availability_blocks=availability,
        routine_blocks=[],
    )

    expected_start = now + timedelta(hours=1)
    assert result["suggested_start_at"] == expected_start
    assert result["suggested_end_at"] == expected_start + timedelta(hours=1)
    assert result["slot_reason"] == "found"


def test_scheduler_engine_falls_back_when_no_common_slot_exists() -> None:
    engine = SchedulerEngine()
    now = datetime.now(UTC).replace(hour=9, minute=0, second=0, microsecond=0)
    availability = [
        SimpleNamespace(
            user_id=1,
            day_of_week=now.weekday(),
            start_time=(now + timedelta(hours=0)).time(),
            end_time=(now + timedelta(hours=1)).time(),
            is_recurring=True,
            specific_date=None,
        ),
        SimpleNamespace(
            user_id=2,
            day_of_week=now.weekday(),
            start_time=(now + timedelta(hours=2)).time(),
            end_time=(now + timedelta(hours=3)).time(),
            is_recurring=True,
            specific_date=None,
        ),
    ]

    result = engine.generate(
        participant_user_ids=[1, 2],
        skill_id=10,
        minimum_duration_minutes=30,
        window_start_at=now,
        window_end_at=now + timedelta(days=1),
        tasks=[],
        availability_blocks=availability,
        routine_blocks=[],
    )

    assert result["suggested_start_at"] == now
    assert result["suggested_end_at"] == now + timedelta(minutes=30)
    assert result["slot_reason"] == "no_overlap"
    assert result["score"] == 50.0
    assert "fallback" in result["explanation"].lower()


def test_scheduler_engine_clamps_no_overlap_fallback_to_window_end() -> None:
    engine = SchedulerEngine()
    now = datetime.now(UTC).replace(hour=9, minute=0, second=0, microsecond=0)
    window_end_at = now + timedelta(minutes=10)

    result = engine.generate(
        participant_user_ids=[1, 2],
        skill_id=10,
        minimum_duration_minutes=30,
        window_start_at=now,
        window_end_at=window_end_at,
        tasks=[],
        availability_blocks=[],
        routine_blocks=[],
    )

    assert result["suggested_start_at"] == now
    assert result["suggested_end_at"] == window_end_at
    assert result["slot_reason"] == "no_overlap"


def test_scheduler_engine_respects_planned_tasks_for_common_slot() -> None:
    engine = SchedulerEngine()
    now = datetime.now(UTC).replace(hour=9, minute=0, second=0, microsecond=0)
    availability = [
        SimpleNamespace(
            user_id=1,
            day_of_week=now.weekday(),
            start_time=(now + timedelta(hours=0)).time(),
            end_time=(now + timedelta(hours=2)).time(),
            is_recurring=True,
            specific_date=None,
        ),
        SimpleNamespace(
            user_id=2,
            day_of_week=now.weekday(),
            start_time=(now + timedelta(hours=0)).time(),
            end_time=(now + timedelta(hours=2)).time(),
            is_recurring=True,
            specific_date=None,
        ),
    ]
    tasks = [
        SimpleNamespace(
            user_id=1,
            skill_id=10,
            planned_start_at=now + timedelta(minutes=30),
            planned_end_at=now + timedelta(minutes=90),
        ),
        SimpleNamespace(
            user_id=2,
            skill_id=10,
            planned_start_at=now + timedelta(minutes=0),
            planned_end_at=now + timedelta(minutes=30),
        ),
    ]

    result = engine.generate(
        participant_user_ids=[1, 2],
        skill_id=10,
        minimum_duration_minutes=30,
        window_start_at=now,
        window_end_at=now + timedelta(days=1),
        tasks=tasks,
        availability_blocks=availability,
        routine_blocks=[],
    )

    expected_start = now + timedelta(minutes=90)
    assert result["suggested_start_at"] == expected_start
    assert result["suggested_end_at"] == expected_start + timedelta(minutes=30)
    assert result["slot_reason"] == "found"


def test_scheduler_engine_marks_empty_participants_as_distinct_fallback() -> None:
    engine = SchedulerEngine()
    now = datetime.now(UTC).replace(hour=9, minute=0, second=0, microsecond=0)

    result = engine.generate(
        participant_user_ids=[],
        skill_id=10,
        minimum_duration_minutes=30,
        window_start_at=now,
        window_end_at=now + timedelta(days=1),
        tasks=[],
        availability_blocks=[],
        routine_blocks=[],
    )

    assert result["suggested_start_at"] == now
    assert result["suggested_end_at"] == now + timedelta(minutes=30)
    assert result["slot_reason"] == "no_participants"
    assert result["score"] == 40.0
    assert "no participants" in result["explanation"].lower()


def test_scheduler_engine_clamps_no_participants_fallback_to_window_end() -> None:
    engine = SchedulerEngine()
    now = datetime.now(UTC).replace(hour=9, minute=0, second=0, microsecond=0)
    window_end_at = now + timedelta(minutes=10)

    result = engine.generate(
        participant_user_ids=[],
        skill_id=10,
        minimum_duration_minutes=30,
        window_start_at=now,
        window_end_at=window_end_at,
        tasks=[],
        availability_blocks=[],
        routine_blocks=[],
    )

    assert result["suggested_start_at"] == now
    assert result["suggested_end_at"] == window_end_at
    assert result["slot_reason"] == "no_participants"
