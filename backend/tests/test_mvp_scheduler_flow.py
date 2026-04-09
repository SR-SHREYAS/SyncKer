"""MVP scheduler smoke flow integration tests."""

from collections.abc import Generator
from datetime import UTC, datetime, timedelta

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.ai.scheduler_engine import SchedulerEngine
from app.api.handlers.auth_handler import AuthHandler
from app.api.handlers.planning_handler import PlanningHandler
from app.api.handlers.scheduling_handler import SchedulingHandler
from app.api.handlers.team_handler import TeamHandler
from app.core.dependencies import get_current_user_id
from app.core.exceptions import ConflictError, ForbiddenError
from app.db.base import Base

# Import all model modules so relationship-based mappers are fully registered.
from app.models.availability_block import AvailabilityBlock  # noqa: F401
from app.models.enums import SuggestionStatus, TaskPriority, TaskStatus
from app.models.profile import Profile  # noqa: F401
from app.models.routine_block import RoutineBlock  # noqa: F401
from app.models.session import Session as SessionModel  # noqa: F401
from app.models.session_participant import SessionParticipant  # noqa: F401
from app.models.session_suggestion import SessionSuggestion  # noqa: F401
from app.models.skill import Skill  # noqa: F401
from app.models.task import Task  # noqa: F401
from app.models.team import Team  # noqa: F401
from app.models.team_member import TeamMember  # noqa: F401
from app.models.user import User  # noqa: F401
from app.models.user_skill import UserSkill  # noqa: F401
from app.repositories.availability_repo import AvailabilityRepository
from app.repositories.routine_repo import RoutineRepository
from app.repositories.skill_repo import SkillRepository
from app.repositories.suggestion_repo import SuggestionRepository
from app.repositories.task_repo import TaskRepository
from app.repositories.team_repo import TeamRepository
from app.repositories.user_repo import UserRepository
from app.schemas.auth import RegisterRequest
from app.schemas.scheduling import (
    SuggestionGenerationRequest,
    SuggestionStatusUpdateRequest,
)
from app.schemas.task import TaskCreateRequest
from app.schemas.team import TeamAddParticipantRequest, TeamCreateRequest
from app.services.auth_service import AuthService
from app.services.planning_service import PlanningService
from app.services.scheduling_service import SchedulingService
from app.services.team_service import TeamService


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """Provide isolated in-memory SQLite session for integration flow tests."""
    engine = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    session_local = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    Base.metadata.create_all(bind=engine)
    db = session_local()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


def _build_handlers(db_session: Session) -> tuple[
    AuthHandler,
    TeamHandler,
    PlanningHandler,
    SchedulingHandler,
]:
    """Create handlers using one shared DB session."""
    user_repo = UserRepository(db_session)
    team_repo = TeamRepository(db_session)
    task_repo = TaskRepository(db_session)
    availability_repo = AvailabilityRepository(db_session)
    routine_repo = RoutineRepository(db_session)
    suggestion_repo = SuggestionRepository(db_session)
    skill_repo = SkillRepository(db_session)

    auth_service = AuthService(user_repo)
    team_service = TeamService(team_repo, user_repo)
    planning_service = PlanningService(
        task_repo,
        availability_repo,
        routine_repo,
        team_service,
    )
    scheduling_service = SchedulingService(
        suggestion_repo,
        SchedulerEngine(),
        task_repo,
        availability_repo,
        routine_repo,
        skill_repo,
        team_service,
    )

    return (
        AuthHandler(auth_service),
        TeamHandler(team_service),
        PlanningHandler(planning_service),
        SchedulingHandler(scheduling_service),
    )


def test_mvp_scheduler_flow_end_to_end(db_session: Session) -> None:
    """Cover core flow: register -> team -> tasks -> suggestion -> apply."""
    auth_handler, team_handler, planning_handler, scheduling_handler = _build_handlers(
        db_session
    )

    owner_auth = auth_handler.registerUser(
        RegisterRequest(
            email="owner@example.com",
            username="owner_user",
            password="StrongPass123",
        )
    )
    participant_auth = auth_handler.registerUser(
        RegisterRequest(
            email="participant@example.com",
            username="participant_user",
            password="StrongPass123",
        )
    )
    owner_id = owner_auth.user.id
    participant_id = participant_auth.user.id

    created_team = team_handler.createTeamWorkspace(
        owner_id,
        TeamCreateRequest(
            name="Alpha Team",
            description="MVP scheduler flow team",
        ),
    )
    team_handler.addTeamParticipant(
        owner_id,
        created_team.id,
        TeamAddParticipantRequest(participant_user_id=participant_id),
    )

    current_time = datetime.now(UTC).replace(second=0, microsecond=0)
    planning_handler.createPlanningTask(
        owner_id,
        TaskCreateRequest(
            title="Owner focus task",
            description="Owner work",
            priority=TaskPriority.MEDIUM,
            status=TaskStatus.PENDING,
            estimated_minutes=45,
            deadline_at=None,
            planned_start_at=current_time + timedelta(minutes=30),
            planned_end_at=current_time + timedelta(minutes=90),
            skill_id=None,
        ),
    )
    planning_handler.createPlanningTask(
        participant_id,
        TaskCreateRequest(
            title="Participant focus task",
            description="Participant work",
            priority=TaskPriority.MEDIUM,
            status=TaskStatus.PENDING,
            estimated_minutes=45,
            deadline_at=None,
            planned_start_at=current_time + timedelta(minutes=20),
            planned_end_at=current_time + timedelta(minutes=80),
            skill_id=None,
        ),
    )

    generated_suggestion = scheduling_handler.generateSchedulingSuggestion(
        owner_id,
        SuggestionGenerationRequest(
            team_id=created_team.id,
            participant_user_ids=[owner_id, participant_id],
            collaboration_title="MVP collaboration block",
            skill_id=None,
            window_start_at=current_time,
            window_end_at=current_time + timedelta(hours=4),
            minimum_duration_minutes=30,
        ),
    )
    assert generated_suggestion.status == SuggestionStatus.PENDING

    # Simulate request boundary so apply starts with a clean transaction.
    db_session.rollback()
    applied_suggestion = scheduling_handler.applySchedulingSuggestionToTimetable(
        owner_id,
        generated_suggestion.id,
    )
    assert applied_suggestion.status == SuggestionStatus.ACCEPTED

    owner_tasks = planning_handler.listPlanningTasks(owner_id)
    assert any(
        item.title == generated_suggestion.collaboration_title for item in owner_tasks
    )

    team_timetable = planning_handler.listTeamTimetable(owner_id, created_team.id)
    assert team_timetable.team_id == created_team.id
    assert {item.user_id for item in team_timetable.participants} == {
        owner_id,
        participant_id,
    }
    assert all(
        any(
            task_item.title == generated_suggestion.collaboration_title
            for task_item in item.tasks
        )
        for item in team_timetable.participants
    )


def test_invalid_token_is_rejected() -> None:
    """Reject malformed bearer tokens at dependency layer."""
    with pytest.raises(HTTPException) as raised_exception:
        get_current_user_id("Bearer invalid-token")

    assert raised_exception.value.status_code == 401
    assert raised_exception.value.detail == "invalid or expired access token"


def test_team_timetable_rejects_non_member_user(db_session: Session) -> None:
    """Reject timetable read when user is outside team membership."""
    auth_handler, team_handler, planning_handler, _ = _build_handlers(db_session)

    owner_auth = auth_handler.registerUser(
        RegisterRequest(
            email="team-owner@example.com",
            username="team_owner",
            password="StrongPass123",
        )
    )
    member_auth = auth_handler.registerUser(
        RegisterRequest(
            email="team-member@example.com",
            username="team_member",
            password="StrongPass123",
        )
    )
    outsider_auth = auth_handler.registerUser(
        RegisterRequest(
            email="team-outsider@example.com",
            username="team_outsider",
            password="StrongPass123",
        )
    )

    created_team = team_handler.createTeamWorkspace(
        owner_auth.user.id,
        TeamCreateRequest(
            name="Restricted Team",
            description="Only members can read timetable",
        ),
    )
    team_handler.addTeamParticipant(
        owner_auth.user.id,
        created_team.id,
        TeamAddParticipantRequest(participant_user_id=member_auth.user.id),
    )

    with pytest.raises(ForbiddenError) as raised_exception:
        planning_handler.listTeamTimetable(outsider_auth.user.id, created_team.id)

    assert str(raised_exception.value) == "user is not a member of this team"


def test_apply_suggestion_rejects_non_pending_status(db_session: Session) -> None:
    """Reject apply when suggestion status is already non-pending."""
    auth_handler, team_handler, _, scheduling_handler = _build_handlers(db_session)

    owner_auth = auth_handler.registerUser(
        RegisterRequest(
            email="status-owner@example.com",
            username="status_owner",
            password="StrongPass123",
        )
    )
    participant_auth = auth_handler.registerUser(
        RegisterRequest(
            email="status-participant@example.com",
            username="status_participant",
            password="StrongPass123",
        )
    )
    owner_id = owner_auth.user.id
    participant_id = participant_auth.user.id

    created_team = team_handler.createTeamWorkspace(
        owner_id,
        TeamCreateRequest(
            name="Status Team",
            description="Apply state validation team",
        ),
    )
    team_handler.addTeamParticipant(
        owner_id,
        created_team.id,
        TeamAddParticipantRequest(participant_user_id=participant_id),
    )

    current_time = datetime.now(UTC).replace(second=0, microsecond=0)
    generated_suggestion = scheduling_handler.generateSchedulingSuggestion(
        owner_id,
        SuggestionGenerationRequest(
            team_id=created_team.id,
            participant_user_ids=[owner_id, participant_id],
            collaboration_title="Reject then apply",
            skill_id=None,
            window_start_at=current_time,
            window_end_at=current_time + timedelta(hours=2),
            minimum_duration_minutes=30,
        ),
    )

    updated_suggestion = scheduling_handler.updateSchedulingSuggestionStatus(
        owner_id,
        generated_suggestion.id,
        SuggestionStatusUpdateRequest(status=SuggestionStatus.REJECTED),
    )
    assert updated_suggestion.status == SuggestionStatus.REJECTED

    # Simulate request boundary so apply starts with a clean transaction.
    db_session.rollback()
    with pytest.raises(ConflictError) as raised_exception:
        scheduling_handler.applySchedulingSuggestionToTimetable(
            owner_id,
            generated_suggestion.id,
        )

    assert str(raised_exception.value) == "only pending suggestions can be applied"
