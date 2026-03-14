from datetime import datetime, timedelta
from types import SimpleNamespace

from app.ai.scheduler_engine import SchedulerEngine


def test_scheduler_engine_returns_slot_inside_window() -> None:
    engine = SchedulerEngine()
    now = datetime.utcnow().replace(hour=9, minute=0, second=0, microsecond=0)

    availability = [
        SimpleNamespace(
            day_of_week=now.weekday(),
            start_time=(now + timedelta(hours=1)).time(),
            end_time=(now + timedelta(hours=3)).time(),
            is_recurring=True,
            specific_date=None,
        )
    ]

    result = engine.generate(
        learner_user_id=1,
        mentor_user_id=2,
        skill_id=10,
        minimum_duration_minutes=60,
        window_start_at=now,
        window_end_at=now + timedelta(days=1),
        learner_tasks=[],
        mentor_tasks=[],
        learner_availability_blocks=availability,
        mentor_availability_blocks=[],
        learner_routine_blocks=[],
        mentor_routine_blocks=[],
    )

    assert result["suggested_start_at"] >= now
    assert result["suggested_end_at"] > result["suggested_start_at"]
    assert result["score"] >= 10


def test_scheduler_engine_scores_related_tasks_higher() -> None:
    engine = SchedulerEngine()
    now = datetime.utcnow().replace(hour=9, minute=0, second=0, microsecond=0)
    availability = [
        SimpleNamespace(
            day_of_week=now.weekday(),
            start_time=(now + timedelta(hours=1)).time(),
            end_time=(now + timedelta(hours=4)).time(),
            is_recurring=True,
            specific_date=None,
        )
    ]
    related_task = SimpleNamespace(skill_id=10)

    without_tasks = engine.generate(
        learner_user_id=1,
        mentor_user_id=2,
        skill_id=10,
        minimum_duration_minutes=60,
        window_start_at=now,
        window_end_at=now + timedelta(days=1),
        learner_tasks=[],
        mentor_tasks=[],
        learner_availability_blocks=availability,
        mentor_availability_blocks=[],
        learner_routine_blocks=[],
        mentor_routine_blocks=[],
    )
    with_tasks = engine.generate(
        learner_user_id=1,
        mentor_user_id=2,
        skill_id=10,
        minimum_duration_minutes=60,
        window_start_at=now,
        window_end_at=now + timedelta(days=1),
        learner_tasks=[related_task],
        mentor_tasks=[],
        learner_availability_blocks=availability,
        mentor_availability_blocks=[],
        learner_routine_blocks=[],
        mentor_routine_blocks=[],
    )

    assert with_tasks["score"] > without_tasks["score"]
