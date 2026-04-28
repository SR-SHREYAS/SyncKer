"""Session access integration tests."""

from collections.abc import Generator
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.ai.scheduler_engine import SchedulerEngine
from app.api.handlers.auth_handler import AuthHandler
from app.api.handlers.planning_handler import PlanningHandler
from app.api.handlers.scheduling_handler import SchedulingHandler
from app.api.handlers.session_handler import SessionHandler
from app.api.handlers.team_handler import TeamHandler
from app.core.exceptions import NotFoundError
from app.db.base import Base

# Import all model modules so relationship-based mappers are fully registered.
from app.models.availability_block import AvailabilityBlock  # noqa: F401
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
from app.models.enums import TaskPriority, TaskStatus
from app.repositories.availability_repo import AvailabilityRepository
from app.repositories.routine_repo import RoutineRepository
from app.repositories.session_repo import SessionRepository
from app.repositories.skill_repo import SkillRepository
from app.repositories.suggestion_repo import SuggestionRepository
from app.repositories.task_repo import TaskRepository
from app.repositories.team_repo import TeamRepository
from app.repositories.user_repo import UserRepository
from app.schemas.auth import RegisterRequest
from app.schemas.scheduling import SuggestionGenerationRequest
from app.schemas.session import SessionCreateFromSuggestionRequest
from app.schemas.task import TaskCreateRequest
from app.schemas.team import TeamAddParticipantRequest, TeamCreateRequest
from app.services.auth_service import AuthService
from app.services.planning_service import PlanningService
from app.services.scheduling_service import SchedulingService
from app.services.session_service import SessionService
from app.services.team_service import TeamService


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """Provide isolated in-memory SQLite session for integration tests."""
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


def _build_handlers(
    db_session: Session,
) -> tuple[
    AuthHandler,
    TeamHandler,
    PlanningHandler,
    SchedulingHandler,
    SessionHandler,
]:
    """Create handlers using one shared DB session."""
    user_repo = UserRepository(db_session)
    team_repo = TeamRepository(db_session)
    task_repo = TaskRepository(db_session)
    availability_repo = AvailabilityRepository(db_session)
    routine_repo = RoutineRepository(db_session)
    suggestion_repo = SuggestionRepository(db_session)
    skill_repo = SkillRepository(db_session)
    session_repo = SessionRepository(db_session)

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
    session_service = SessionService(session_repo, suggestion_repo)

    return (
        AuthHandler(auth_service),
        TeamHandler(team_service),
        PlanningHandler(planning_service),
        SchedulingHandler(scheduling_service),
        SessionHandler(session_service),
    )


def _create_session_fixture(
    db_session: Session,
) -> tuple[int, int, int, int, SessionHandler]:
    """Build one session with owner, participant, and outsider users."""
    (
        auth_handler,
        team_handler,
        planning_handler,
        scheduling_handler,
        session_handler,
    ) = _build_handlers(db_session)

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
    outsider_auth = auth_handler.registerUser(
        RegisterRequest(
            email="outsider@example.com",
            username="outsider_user",
            password="StrongPass123",
        )
    )
    owner_id = owner_auth.user.id
    participant_id = participant_auth.user.id
    outsider_id = outsider_auth.user.id

    created_team = team_handler.createTeamWorkspace(
        owner_id,
        TeamCreateRequest(
            name="Session Access Team",
            description="Session access coverage team",
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
            title="Owner task",
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
            title="Participant task",
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
            collaboration_title="Session access collaboration",
            skill_id=None,
            window_start_at=current_time,
            window_end_at=current_time + timedelta(hours=4),
            minimum_duration_minutes=30,
        ),
    )
    created_session = session_handler.createSessionFromSuggestion(
        owner_id,
        SessionCreateFromSuggestionRequest(
            suggestion_id=generated_suggestion.id,
            title=None,
        ),
    )

    return created_session.id, owner_id, participant_id, outsider_id, session_handler


def test_session_creator_can_list_and_get_session(db_session: Session) -> None:
    session_id, owner_id, _, _, session_handler = _create_session_fixture(db_session)

    listed_sessions = session_handler.listSessions(owner_id)
    fetched_session = session_handler.getSessionById(owner_id, session_id)

    assert [session.id for session in listed_sessions] == [session_id]
    assert fetched_session.id == session_id


def test_session_participant_can_list_and_get_session(db_session: Session) -> None:
    session_id, _, participant_id, _, session_handler = _create_session_fixture(
        db_session
    )

    listed_sessions = session_handler.listSessions(participant_id)
    fetched_session = session_handler.getSessionById(participant_id, session_id)

    assert [session.id for session in listed_sessions] == [session_id]
    assert fetched_session.id == session_id
    assert {participant.user_id for participant in fetched_session.participants} == {
        participant_id,
        fetched_session.created_by_user_id,
    }


def test_outsider_cannot_get_or_list_unrelated_session(db_session: Session) -> None:
    session_id, _, _, outsider_id, session_handler = _create_session_fixture(db_session)

    listed_sessions = session_handler.listSessions(outsider_id)

    assert listed_sessions == []
    with pytest.raises(NotFoundError, match="session not found"):
        session_handler.getSessionById(outsider_id, session_id)
