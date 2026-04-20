from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base

# Import all model modules so relationship-based mappers are fully registered.
from app.models.availability_block import AvailabilityBlock  # noqa: F401
from app.models.profile import Profile  # noqa: F401
from app.models.routine_block import RoutineBlock  # noqa: F401
from app.models.session import Session as SessionModel  # noqa: F401
from app.models.session_participant import SessionParticipant  # noqa: F401
from app.models.session_suggestion import SessionSuggestion  # noqa: F401
from app.models.skill import Skill  # noqa: F401
from app.models.task import Task
from app.models.team import Team  # noqa: F401
from app.models.team_member import TeamMember  # noqa: F401
from app.models.user import User
from app.models.user_skill import UserSkill  # noqa: F401
from app.models.enums import TaskPriority, TaskStatus
from app.repositories.task_repo import TaskRepository


def _as_utc_naive(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value
    return value.astimezone(UTC).replace(tzinfo=None)


@pytest.fixture
def db_session() -> Session:
    engine = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


def _seed_user(db_session: Session, user_id: int, email: str, username: str) -> None:
    db_session.add(
        User(
            id=user_id,
            email=email,
            username=username,
            password_hash="test-password-hash",
            is_active=True,
        )
    )
    db_session.commit()


def _seed_task(
    db_session: Session,
    *,
    task_id: int,
    user_id: int,
    title: str,
    created_at: datetime,
) -> Task:
    task = Task(
        id=task_id,
        user_id=user_id,
        title=title,
        description=None,
        priority=TaskPriority.MEDIUM,
        status=TaskStatus.PENDING,
        estimated_minutes=30,
        deadline_at=None,
        planned_start_at=None,
        planned_end_at=None,
        skill_id=None,
        created_at=created_at,
        updated_at=created_at,
    )
    db_session.add(task)
    db_session.commit()
    return task


def test_list_tasks_by_users_with_empty_user_ids_returns_empty_list(
    db_session: Session,
) -> None:
    repository = TaskRepository(db_session)

    tasks = repository.list_tasks_by_users(user_ids=[])

    assert tasks == []


def test_list_tasks_by_users_orders_by_user_then_created_at_desc(
    db_session: Session,
) -> None:
    repository = TaskRepository(db_session)
    _seed_user(db_session, user_id=1, email="u1@example.com", username="u1")
    _seed_user(db_session, user_id=2, email="u2@example.com", username="u2")

    base_time = datetime.now(UTC)
    _seed_task(
        db_session,
        task_id=101,
        user_id=1,
        title="u1 older",
        created_at=base_time - timedelta(minutes=10),
    )
    _seed_task(
        db_session,
        task_id=102,
        user_id=1,
        title="u1 newer",
        created_at=base_time,
    )
    _seed_task(
        db_session,
        task_id=201,
        user_id=2,
        title="u2 older",
        created_at=base_time - timedelta(minutes=5),
    )
    _seed_task(
        db_session,
        task_id=202,
        user_id=2,
        title="u2 newer",
        created_at=base_time + timedelta(minutes=1),
    )

    tasks = repository.list_tasks_by_users(user_ids=[1, 2])

    assert [task.user_id for task in tasks] == [1, 1, 2, 2]
    assert [task.title for task in tasks] == [
        "u1 newer",
        "u1 older",
        "u2 newer",
        "u2 older",
    ]


def test_list_tasks_by_users_has_no_duplicates_or_omissions(
    db_session: Session,
) -> None:
    repository = TaskRepository(db_session)
    _seed_user(db_session, user_id=1, email="u1@example.com", username="u1")
    _seed_user(db_session, user_id=2, email="u2@example.com", username="u2")
    _seed_user(db_session, user_id=3, email="u3@example.com", username="u3")

    base_time = datetime.now(UTC)
    created_tasks = [
        _seed_task(
            db_session,
            task_id=301,
            user_id=1,
            title="u1 task 1",
            created_at=base_time,
        ),
        _seed_task(
            db_session,
            task_id=302,
            user_id=1,
            title="u1 task 2",
            created_at=base_time - timedelta(minutes=1),
        ),
        _seed_task(
            db_session,
            task_id=303,
            user_id=2,
            title="u2 task 1",
            created_at=base_time - timedelta(minutes=2),
        ),
        _seed_task(
            db_session,
            task_id=304,
            user_id=3,
            title="u3 task 1",
            created_at=base_time - timedelta(minutes=3),
        ),
    ]

    all_tasks = repository.list_tasks_by_users(user_ids=[1, 2, 3])
    assert len(all_tasks) == len(created_tasks)
    assert {(task.user_id, task.title) for task in all_tasks} == {
        (task.user_id, task.title) for task in created_tasks
    }

    subset_tasks = repository.list_tasks_by_users(user_ids=[1, 3])
    assert {task.user_id for task in subset_tasks} == {1, 3}
    assert all(task.user_id in {1, 3} for task in subset_tasks)


def test_create_task_persists_planned_timeslot_values(db_session: Session) -> None:
    repository = TaskRepository(db_session)
    _seed_user(db_session, user_id=10, email="owner@example.com", username="owner")

    current_time = datetime.now(UTC).replace(microsecond=0)
    planned_start_at = current_time + timedelta(minutes=15)
    planned_end_at = current_time + timedelta(minutes=75)

    created_task = repository.create_task(
        user_id=10,
        title="Task with planned times",
        description="Task description",
        priority=TaskPriority.MEDIUM,
        status=TaskStatus.PENDING,
        estimated_minutes=30,
        deadline_at=None,
        planned_start_at=planned_start_at,
        planned_end_at=planned_end_at,
        skill_id=None,
    )

    fetched_task = repository.get_task_by_id(created_task.id)

    assert fetched_task is not None
    assert _as_utc_naive(fetched_task.planned_start_at) == _as_utc_naive(
        planned_start_at
    )
    assert _as_utc_naive(fetched_task.planned_end_at) == _as_utc_naive(planned_end_at)
