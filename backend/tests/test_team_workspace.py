from datetime import UTC, datetime, timedelta
from dataclasses import dataclass
from types import SimpleNamespace

import pytest
from sqlalchemy.exc import IntegrityError

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.models.enums import SuggestionStatus, TaskPriority
from app.services.scheduling_service import SchedulingService
from app.services.team_service import TeamService


class _FakeUserRepo:
    def __init__(self) -> None:
        self.users = {
            1: SimpleNamespace(id=1, username="owner", email="owner@example.com"),
            2: SimpleNamespace(id=2, username="member", email="member@example.com"),
            3: SimpleNamespace(id=3, username="guest", email="guest@example.com"),
        }

    def get_by_id(self, user_id: int):
        return self.users.get(user_id)


class _FakeTeamRepo:
    def __init__(self) -> None:
        self._next_team_id = 1
        self._next_membership_id = 1
        self.teams: dict[int, SimpleNamespace] = {}
        self.memberships: dict[tuple[int, int], SimpleNamespace] = {}

    def create_team(self, *, name: str, description: str | None, owner_user_id: int):
        team = SimpleNamespace(
            id=self._next_team_id,
            name=name,
            description=description,
            owner_user_id=owner_user_id,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        self.teams[team.id] = team
        self._next_team_id += 1
        return team

    def get_team_by_id(self, team_id: int):
        return self.teams.get(team_id)

    def list_teams_for_user(self, user_id: int):
        team_ids = [
            team_id
            for (team_id, member_user_id) in self.memberships
            if member_user_id == user_id
        ]
        return [self.teams[item] for item in team_ids]

    def add_team_member(self, *, team_id: int, user_id: int):
        if (team_id, user_id) in self.memberships:
            raise IntegrityError(
                "duplicate membership",
                params=None,
                orig=Exception("duplicate membership"),
            )
        membership = SimpleNamespace(
            id=self._next_membership_id,
            team_id=team_id,
            user_id=user_id,
            created_at=datetime.now(UTC),
        )
        self.memberships[(team_id, user_id)] = membership
        self._next_membership_id += 1
        return membership

    def get_team_member(self, *, team_id: int, user_id: int):
        return self.memberships.get((team_id, user_id))

    def list_team_members(self, team_id: int):
        return [
            item
            for (member_team_id, _), item in self.memberships.items()
            if member_team_id == team_id
        ]


class _FakeSuggestionRepo:
    def __init__(self, db: object) -> None:
        self.last_create_payload = None
        self._next_suggestion_id = 101
        self.suggestions_by_id: dict[int, SimpleNamespace] = {}
        self.db = db

    def create_suggestion(self, **kwargs):
        self.last_create_payload = kwargs
        suggestion = SimpleNamespace(
            id=self._next_suggestion_id,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            **kwargs,
        )
        self.suggestions_by_id[suggestion.id] = suggestion
        self._next_suggestion_id += 1
        return suggestion

    def list_suggestions_for_user(self, user_id: int):
        return []

    def get_suggestion_by_id(self, suggestion_id: int):
        return self.suggestions_by_id.get(suggestion_id)

    def get_suggestion_by_id_for_update(self, suggestion_id: int):
        return self.suggestions_by_id.get(suggestion_id)

    def update_suggestion(self, suggestion, *, auto_commit: bool = True, **updates):
        if not auto_commit and not self.db.in_transaction():
            raise RuntimeError(
                "suggestion update with auto_commit=False requires an active transaction"
            )
        for field_name, field_value in updates.items():
            setattr(suggestion, field_name, field_value)
        self.suggestions_by_id[suggestion.id] = suggestion
        return suggestion


class _FakeSchedulerEngine:
    def generate(self, **kwargs):
        start_at = datetime.now(UTC) + timedelta(hours=1)
        return {
            "suggested_start_at": start_at,
            "suggested_end_at": start_at + timedelta(minutes=45),
            "score": 88.0,
            "status": SuggestionStatus.PENDING,
            "explanation": "best overlap found",
            "participant_user_ids": kwargs["participant_user_ids"],
        }


class _FakeEmptyRepo:
    def list_tasks_by_user(self, user_id: int):
        return []

    def list_blocks_by_user(self, user_id: int):
        return []


class _FakeTaskRepo:
    def __init__(self, db: object) -> None:
        self.db = db
        self._next_task_id = 1
        self.tasks_by_user: dict[int, list[SimpleNamespace]] = {}
        self.created_tasks: list[SimpleNamespace] = []

    def list_tasks_by_user(self, user_id: int):
        return list(self.tasks_by_user.get(user_id, []))

    def list_planned_tasks_by_user(
        self,
        *,
        user_id: int,
        for_update: bool = False,
    ) -> list[SimpleNamespace]:
        user_tasks = self.tasks_by_user.get(user_id, [])
        planned_tasks = [
            user_task
            for user_task in user_tasks
            if getattr(user_task, "planned_start_at", None) is not None
            and getattr(user_task, "planned_end_at", None) is not None
        ]
        return sorted(planned_tasks, key=lambda item: (item.planned_start_at, item.id))

    def create_task(
        self,
        *,
        user_id: int,
        title: str,
        description: str | None,
        priority: str,
        status: str,
        estimated_minutes: int,
        deadline_at: datetime | None,
        planned_start_at: datetime | None,
        planned_end_at: datetime | None,
        skill_id: int | None,
        auto_commit: bool = True,
    ):
        if not auto_commit and not self.db.in_transaction():
            raise RuntimeError(
                "task create with auto_commit=False requires an active transaction"
            )
        created_task = SimpleNamespace(
            id=self._next_task_id,
            user_id=user_id,
            title=title,
            description=description,
            priority=priority,
            status=status,
            estimated_minutes=estimated_minutes,
            deadline_at=deadline_at,
            planned_start_at=planned_start_at,
            planned_end_at=planned_end_at,
            skill_id=skill_id,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        self._next_task_id += 1
        self.created_tasks.append(created_task)
        self.tasks_by_user.setdefault(user_id, []).append(created_task)
        return created_task

    def update_task(self, task: object, *, auto_commit: bool = True, **updates: object):
        if not auto_commit and not self.db.in_transaction():
            raise RuntimeError(
                "task update with auto_commit=False requires an active transaction"
            )
        for field_name, field_value in updates.items():
            setattr(task, field_name, field_value)
        return task


class _FakeTransactionContext:
    def __init__(self, db_session: "_FakeDbSession") -> None:
        self.db_session = db_session

    def __enter__(self):
        self.db_session.transaction_depth += 1
        return self

    def __exit__(self, exc_type, exc, tb):
        self.db_session.transaction_depth -= 1
        return False


class _FakeDbSession:
    def __init__(self) -> None:
        self.transaction_depth = 0

    def begin(self):
        return _FakeTransactionContext(self)

    def in_transaction(self) -> bool:
        return self.transaction_depth > 0


class _FakeSkillRepo:
    def get_skill_by_id(self, skill_id: int):
        return SimpleNamespace(id=skill_id)

    def get_skill_by_slug(self, slug: str):
        return None

    def create_skill(self, *, name: str, slug: str, description: str):
        return SimpleNamespace(id=77)


def test_create_team_workspace_adds_owner_membership() -> None:
    team_repo = _FakeTeamRepo()
    user_repo = _FakeUserRepo()
    service = TeamService(team_repo, user_repo)

    team = service.CreateTeamWorkspace(
        current_user_id=1, name="Core Team", description="MVP workspace"
    )

    assert team.id == 1
    assert team.owner_user_id == 1
    assert team_repo.get_team_member(team_id=team.id, user_id=1) is not None


def test_add_team_participant_requires_owner() -> None:
    team_repo = _FakeTeamRepo()
    user_repo = _FakeUserRepo()
    service = TeamService(team_repo, user_repo)
    team = service.CreateTeamWorkspace(
        current_user_id=1, name="Core Team", description=None
    )

    with pytest.raises(ForbiddenError):
        service.AddTeamParticipant(
            current_user_id=2, team_id=team.id, participant_user_id=3
        )


def test_add_team_participant_maps_duplicate_membership_to_conflict_error() -> None:
    team_repo = _FakeTeamRepo()
    user_repo = _FakeUserRepo()
    service = TeamService(team_repo, user_repo)
    team = service.CreateTeamWorkspace(
        current_user_id=1, name="Core Team", description=None
    )

    service.AddTeamParticipant(
        current_user_id=1, team_id=team.id, participant_user_id=2
    )
    with pytest.raises(ConflictError):
        service.AddTeamParticipant(
            current_user_id=1, team_id=team.id, participant_user_id=2
        )


@dataclass
class _SchedulingScenario:
    team: SimpleNamespace
    team_service: TeamService
    suggestion_repo: _FakeSuggestionRepo
    task_repo: _FakeTaskRepo
    scheduling_service: SchedulingService


def _build_scheduling_scenario() -> _SchedulingScenario:
    team_repo = _FakeTeamRepo()
    user_repo = _FakeUserRepo()
    team_service = TeamService(team_repo, user_repo)
    team = team_service.CreateTeamWorkspace(
        current_user_id=1, name="Core Team", description=None
    )
    team_service.AddTeamParticipant(
        current_user_id=1, team_id=team.id, participant_user_id=2
    )

    shared_db = _FakeDbSession()
    suggestion_repo = _FakeSuggestionRepo(shared_db)
    task_repo = _FakeTaskRepo(shared_db)
    scheduling_service = SchedulingService(
        suggestion_repo=suggestion_repo,
        scheduler_engine=_FakeSchedulerEngine(),
        task_repo=task_repo,
        availability_repo=_FakeEmptyRepo(),
        routine_repo=_FakeEmptyRepo(),
        skill_repo=_FakeSkillRepo(),
        team_service=team_service,
    )
    return _SchedulingScenario(
        team=team,
        team_service=team_service,
        suggestion_repo=suggestion_repo,
        task_repo=task_repo,
        scheduling_service=scheduling_service,
    )


def _seed_suggestion(
    scenario: _SchedulingScenario,
    *,
    suggestion_id: int,
    status: SuggestionStatus,
    generated_for_user_id: int = 1,
    collaboration_title: str = "Sprint planning",
    suggested_start_at: datetime | None = None,
    suggested_end_at: datetime | None = None,
) -> SimpleNamespace:
    resolved_start_at = suggested_start_at or datetime.now(UTC).replace(
        second=0, microsecond=0
    )
    resolved_end_at = suggested_end_at or (resolved_start_at + timedelta(minutes=45))
    suggestion = SimpleNamespace(
        id=suggestion_id,
        team_id=scenario.team.id,
        generated_for_user_id=generated_for_user_id,
        mentor_user_id=1,
        learner_user_id=2,
        participant_user_ids=[1, 2],
        collaboration_title=collaboration_title,
        skill_id=10,
        suggested_start_at=resolved_start_at,
        suggested_end_at=resolved_end_at,
        score=88.0,
        status=status,
        explanation="best overlap found",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    scenario.suggestion_repo.suggestions_by_id[suggestion_id] = suggestion
    return suggestion


def test_generate_scheduling_suggestion_rejects_participant_outside_team() -> None:
    scenario = _build_scheduling_scenario()

    with pytest.raises(ForbiddenError):
        scenario.scheduling_service.GenerateSchedulingSuggestion(
            team_id=scenario.team.id,
            generated_for_user_id=1,
            participant_user_ids=[1, 2, 3],
            collaboration_title="Sync meeting",
            skill_id=10,
            window_start_at=datetime.now(UTC),
            window_end_at=datetime.now(UTC) + timedelta(days=1),
            minimum_duration_minutes=30,
        )


def test_generate_scheduling_suggestion_saves_team_context() -> None:
    scenario = _build_scheduling_scenario()

    suggestion = scenario.scheduling_service.GenerateSchedulingSuggestion(
        team_id=scenario.team.id,
        generated_for_user_id=1,
        participant_user_ids=[1, 2],
        collaboration_title="Sprint planning",
        skill_id=10,
        window_start_at=datetime.now(UTC),
        window_end_at=datetime.now(UTC) + timedelta(days=1),
        minimum_duration_minutes=30,
    )

    assert suggestion.team_id == scenario.team.id
    assert scenario.suggestion_repo.last_create_payload["team_id"] == scenario.team.id


def test_apply_scheduling_suggestion_creates_collaboration_tasks() -> None:
    scenario = _build_scheduling_scenario()
    seeded_suggestion = _seed_suggestion(
        scenario,
        suggestion_id=501,
        status=SuggestionStatus.PENDING,
    )

    applied_suggestion = (
        scenario.scheduling_service.ApplySchedulingSuggestionToTimetable(
            user_id=1,
            suggestion_id=seeded_suggestion.id,
        )
    )

    assert applied_suggestion.status == SuggestionStatus.ACCEPTED
    assert len(scenario.task_repo.created_tasks) == 2
    assert {task.user_id for task in scenario.task_repo.created_tasks} == {1, 2}
    assert all(
        task.title == seeded_suggestion.collaboration_title
        for task in scenario.task_repo.created_tasks
    )
    assert all(
        task.planned_start_at == seeded_suggestion.suggested_start_at
        for task in scenario.task_repo.created_tasks
    )
    assert all(
        task.planned_end_at == seeded_suggestion.suggested_end_at
        for task in scenario.task_repo.created_tasks
    )
    assert all(
        task.estimated_minutes == 45 for task in scenario.task_repo.created_tasks
    )


def test_apply_scheduling_suggestion_shifts_lower_priority_tasks() -> None:
    scenario = _build_scheduling_scenario()
    suggested_start_at = datetime.now(UTC).replace(second=0, microsecond=0)
    suggested_end_at = suggested_start_at + timedelta(minutes=60)
    seeded_suggestion = _seed_suggestion(
        scenario,
        suggestion_id=510,
        status=SuggestionStatus.PENDING,
        suggested_start_at=suggested_start_at,
        suggested_end_at=suggested_end_at,
    )
    overlapping_task = SimpleNamespace(
        id=90,
        user_id=2,
        title="Shift me",
        description=None,
        priority=TaskPriority.MEDIUM,
        status="pending",
        estimated_minutes=45,
        deadline_at=None,
        planned_start_at=suggested_start_at + timedelta(minutes=15),
        planned_end_at=suggested_start_at + timedelta(minutes=60),
        skill_id=None,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    scenario.task_repo.tasks_by_user[2] = [overlapping_task]

    applied_suggestion = (
        scenario.scheduling_service.ApplySchedulingSuggestionToTimetable(
            user_id=1,
            suggestion_id=seeded_suggestion.id,
        )
    )

    assert applied_suggestion.status == SuggestionStatus.ACCEPTED
    assert overlapping_task.planned_start_at == suggested_end_at
    assert overlapping_task.planned_end_at == suggested_end_at + timedelta(minutes=45)
    assert len(scenario.task_repo.created_tasks) == 2


def test_apply_scheduling_suggestion_rejects_non_overlapping_task_beyond_horizon() -> (
    None
):
    scenario = _build_scheduling_scenario()
    suggested_start_at = datetime.now(UTC).replace(second=0, microsecond=0)
    suggested_end_at = suggested_start_at + timedelta(minutes=60)
    seeded_suggestion = _seed_suggestion(
        scenario,
        suggestion_id=512,
        status=SuggestionStatus.PENDING,
        collaboration_title="Horizon-safe sync",
        suggested_start_at=suggested_start_at,
        suggested_end_at=suggested_end_at,
    )
    future_task = SimpleNamespace(
        id=91,
        user_id=2,
        title="Future non-overlap task",
        description=None,
        priority=TaskPriority.MEDIUM,
        status="pending",
        estimated_minutes=45,
        deadline_at=None,
        planned_start_at=suggested_end_at + timedelta(hours=13),
        planned_end_at=suggested_end_at + timedelta(hours=14),
        skill_id=None,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    scenario.task_repo.tasks_by_user[2] = [future_task]

    with pytest.raises(ConflictError):
        scenario.scheduling_service.ApplySchedulingSuggestionToTimetable(
            user_id=1,
            suggestion_id=seeded_suggestion.id,
        )

    assert scenario.task_repo.created_tasks == []
    assert (
        scenario.suggestion_repo.suggestions_by_id[seeded_suggestion.id].status
        == SuggestionStatus.PENDING
    )
    assert future_task.planned_start_at == suggested_end_at + timedelta(hours=13)
    assert future_task.planned_end_at == suggested_end_at + timedelta(hours=14)


def test_apply_scheduling_suggestion_is_idempotent_for_accepted_status() -> None:
    scenario = _build_scheduling_scenario()
    seeded_suggestion = _seed_suggestion(
        scenario,
        suggestion_id=502,
        status=SuggestionStatus.ACCEPTED,
        collaboration_title="Daily sync",
        suggested_end_at=datetime.now(UTC).replace(second=0, microsecond=0)
        + timedelta(minutes=30),
    )

    applied_suggestion = (
        scenario.scheduling_service.ApplySchedulingSuggestionToTimetable(
            user_id=1,
            suggestion_id=seeded_suggestion.id,
        )
    )

    assert applied_suggestion.status == SuggestionStatus.ACCEPTED
    assert scenario.task_repo.created_tasks == []


def test_apply_scheduling_suggestion_rejects_non_owner_user() -> None:
    scenario = _build_scheduling_scenario()
    seeded_suggestion = _seed_suggestion(
        scenario,
        suggestion_id=503,
        status=SuggestionStatus.PENDING,
        generated_for_user_id=1,
        collaboration_title="Planning sync",
    )

    with pytest.raises(NotFoundError):
        scenario.scheduling_service.ApplySchedulingSuggestionToTimetable(
            user_id=2,
            suggestion_id=seeded_suggestion.id,
        )


def test_apply_scheduling_suggestion_rejects_protected_task_overlap() -> None:
    scenario = _build_scheduling_scenario()
    suggested_start_at = datetime.now(UTC).replace(second=0, microsecond=0)
    suggested_end_at = suggested_start_at + timedelta(minutes=60)
    seeded_suggestion = _seed_suggestion(
        scenario,
        suggestion_id=504,
        status=SuggestionStatus.PENDING,
        collaboration_title="Conflict test sync",
        suggested_start_at=suggested_start_at,
        suggested_end_at=suggested_end_at,
    )
    scenario.task_repo.tasks_by_user[2] = [
        SimpleNamespace(
            id=1,
            user_id=2,
            title="Protected task",
            description=None,
            priority=TaskPriority.HIGH,
            status="pending",
            estimated_minutes=30,
            deadline_at=None,
            planned_start_at=suggested_start_at + timedelta(minutes=15),
            planned_end_at=suggested_end_at + timedelta(minutes=15),
            skill_id=None,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
    ]

    with pytest.raises(ConflictError):
        scenario.scheduling_service.ApplySchedulingSuggestionToTimetable(
            user_id=1,
            suggestion_id=seeded_suggestion.id,
        )

    assert scenario.task_repo.created_tasks == []
    assert (
        scenario.suggestion_repo.suggestions_by_id[seeded_suggestion.id].status
        == SuggestionStatus.PENDING
    )


def test_apply_scheduling_suggestion_rejects_unknown_priority_overlap() -> None:
    scenario = _build_scheduling_scenario()
    suggested_start_at = datetime.now(UTC).replace(second=0, microsecond=0)
    suggested_end_at = suggested_start_at + timedelta(minutes=60)
    seeded_suggestion = _seed_suggestion(
        scenario,
        suggestion_id=505,
        status=SuggestionStatus.PENDING,
        collaboration_title="Unknown priority conflict",
        suggested_start_at=suggested_start_at,
        suggested_end_at=suggested_end_at,
    )
    scenario.task_repo.tasks_by_user[2] = [
        SimpleNamespace(
            id=2,
            user_id=2,
            title="Unknown priority task",
            description=None,
            priority="urgent",
            status="pending",
            estimated_minutes=30,
            deadline_at=None,
            planned_start_at=suggested_start_at + timedelta(minutes=5),
            planned_end_at=suggested_end_at + timedelta(minutes=5),
            skill_id=None,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
    ]

    with pytest.raises(ConflictError):
        scenario.scheduling_service.ApplySchedulingSuggestionToTimetable(
            user_id=1,
            suggestion_id=seeded_suggestion.id,
        )

    assert scenario.task_repo.created_tasks == []
    assert (
        scenario.suggestion_repo.suggestions_by_id[seeded_suggestion.id].status
        == SuggestionStatus.PENDING
    )


def test_apply_scheduling_suggestion_rejects_when_no_feasible_shift_exists() -> None:
    scenario = _build_scheduling_scenario()
    suggested_start_at = datetime.now(UTC).replace(second=0, microsecond=0)
    suggested_end_at = suggested_start_at + timedelta(minutes=60)
    seeded_suggestion = _seed_suggestion(
        scenario,
        suggestion_id=511,
        status=SuggestionStatus.PENDING,
        collaboration_title="No feasible shift",
        suggested_start_at=suggested_start_at,
        suggested_end_at=suggested_end_at,
    )

    first_task = SimpleNamespace(
        id=1001,
        user_id=2,
        title="Movable task 1",
        description=None,
        priority=TaskPriority.MEDIUM,
        status="pending",
        estimated_minutes=30,
        deadline_at=None,
        planned_start_at=suggested_start_at,
        planned_end_at=suggested_start_at + timedelta(hours=4, minutes=10),
        skill_id=None,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    second_task = SimpleNamespace(
        id=1002,
        user_id=2,
        title="Movable task 2",
        description=None,
        priority=TaskPriority.MEDIUM,
        status="pending",
        estimated_minutes=30,
        deadline_at=None,
        planned_start_at=first_task.planned_end_at,
        planned_end_at=first_task.planned_end_at + timedelta(hours=4, minutes=10),
        skill_id=None,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    third_task = SimpleNamespace(
        id=1003,
        user_id=2,
        title="Movable task 3",
        description=None,
        priority=TaskPriority.MEDIUM,
        status="pending",
        estimated_minutes=30,
        deadline_at=None,
        planned_start_at=second_task.planned_end_at,
        planned_end_at=second_task.planned_end_at + timedelta(hours=4, minutes=10),
        skill_id=None,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    original_task_plans = {
        first_task.id: (first_task.planned_start_at, first_task.planned_end_at),
        second_task.id: (second_task.planned_start_at, second_task.planned_end_at),
        third_task.id: (third_task.planned_start_at, third_task.planned_end_at),
    }
    scenario.task_repo.tasks_by_user[2] = [third_task, first_task, second_task]

    with pytest.raises(ConflictError):
        scenario.scheduling_service.ApplySchedulingSuggestionToTimetable(
            user_id=1,
            suggestion_id=seeded_suggestion.id,
        )

    assert scenario.task_repo.created_tasks == []
    for movable_task in (first_task, second_task, third_task):
        original_start_at, original_end_at = original_task_plans[movable_task.id]
        assert movable_task.planned_start_at == original_start_at
        assert movable_task.planned_end_at == original_end_at
    assert (
        scenario.suggestion_repo.suggestions_by_id[seeded_suggestion.id].status
        == SuggestionStatus.PENDING
    )
