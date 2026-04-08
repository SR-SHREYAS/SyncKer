from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest
from sqlalchemy.exc import IntegrityError

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.models.enums import SuggestionStatus
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
    def __init__(self) -> None:
        self.last_create_payload = None
        self._next_suggestion_id = 101
        self.suggestions_by_id: dict[int, SimpleNamespace] = {}

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

    def update_suggestion(self, suggestion, **updates):
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
    def __init__(self) -> None:
        self._next_task_id = 1
        self.tasks_by_user: dict[int, list[SimpleNamespace]] = {}
        self.created_tasks: list[SimpleNamespace] = []

    def list_tasks_by_user(self, user_id: int):
        return list(self.tasks_by_user.get(user_id, []))

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
        skill_id: int | None
    ):
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


def test_generate_scheduling_suggestion_rejects_participant_outside_team() -> None:
    team_repo = _FakeTeamRepo()
    user_repo = _FakeUserRepo()
    team_service = TeamService(team_repo, user_repo)
    team = team_service.CreateTeamWorkspace(
        current_user_id=1, name="Core Team", description=None
    )
    team_service.AddTeamParticipant(
        current_user_id=1, team_id=team.id, participant_user_id=2
    )

    scheduling_service = SchedulingService(
        suggestion_repo=_FakeSuggestionRepo(),
        scheduler_engine=_FakeSchedulerEngine(),
        task_repo=_FakeTaskRepo(),
        availability_repo=_FakeEmptyRepo(),
        routine_repo=_FakeEmptyRepo(),
        skill_repo=_FakeSkillRepo(),
        team_service=team_service,
    )

    with pytest.raises(ForbiddenError):
        scheduling_service.GenerateSchedulingSuggestion(
            team_id=team.id,
            generated_for_user_id=1,
            participant_user_ids=[1, 2, 3],
            collaboration_title="Sync meeting",
            skill_id=10,
            window_start_at=datetime.now(UTC),
            window_end_at=datetime.now(UTC) + timedelta(days=1),
            minimum_duration_minutes=30,
        )


def test_generate_scheduling_suggestion_saves_team_context() -> None:
    team_repo = _FakeTeamRepo()
    user_repo = _FakeUserRepo()
    team_service = TeamService(team_repo, user_repo)
    team = team_service.CreateTeamWorkspace(
        current_user_id=1, name="Core Team", description=None
    )
    team_service.AddTeamParticipant(
        current_user_id=1, team_id=team.id, participant_user_id=2
    )

    suggestion_repo = _FakeSuggestionRepo()
    scheduling_service = SchedulingService(
        suggestion_repo=suggestion_repo,
        scheduler_engine=_FakeSchedulerEngine(),
        task_repo=_FakeTaskRepo(),
        availability_repo=_FakeEmptyRepo(),
        routine_repo=_FakeEmptyRepo(),
        skill_repo=_FakeSkillRepo(),
        team_service=team_service,
    )

    suggestion = scheduling_service.GenerateSchedulingSuggestion(
        team_id=team.id,
        generated_for_user_id=1,
        participant_user_ids=[1, 2],
        collaboration_title="Sprint planning",
        skill_id=10,
        window_start_at=datetime.now(UTC),
        window_end_at=datetime.now(UTC) + timedelta(days=1),
        minimum_duration_minutes=30,
    )

    assert suggestion.team_id == team.id
    assert suggestion_repo.last_create_payload["team_id"] == team.id


def test_apply_scheduling_suggestion_creates_collaboration_tasks() -> None:
    team_repo = _FakeTeamRepo()
    user_repo = _FakeUserRepo()
    team_service = TeamService(team_repo, user_repo)
    team = team_service.CreateTeamWorkspace(
        current_user_id=1, name="Core Team", description=None
    )
    team_service.AddTeamParticipant(
        current_user_id=1, team_id=team.id, participant_user_id=2
    )

    suggestion_repo = _FakeSuggestionRepo()
    task_repo = _FakeTaskRepo()
    scheduling_service = SchedulingService(
        suggestion_repo=suggestion_repo,
        scheduler_engine=_FakeSchedulerEngine(),
        task_repo=task_repo,
        availability_repo=_FakeEmptyRepo(),
        routine_repo=_FakeEmptyRepo(),
        skill_repo=_FakeSkillRepo(),
        team_service=team_service,
    )

    suggested_start_at = datetime.now(UTC).replace(second=0, microsecond=0)
    suggested_end_at = suggested_start_at + timedelta(minutes=45)
    suggestion_repo.suggestions_by_id[501] = SimpleNamespace(
        id=501,
        team_id=team.id,
        generated_for_user_id=1,
        mentor_user_id=1,
        learner_user_id=2,
        participant_user_ids=[1, 2],
        collaboration_title="Sprint planning",
        skill_id=10,
        suggested_start_at=suggested_start_at,
        suggested_end_at=suggested_end_at,
        score=88.0,
        status=SuggestionStatus.PENDING,
        explanation="best overlap found",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    applied_suggestion = scheduling_service.ApplySchedulingSuggestionToTimetable(
        user_id=1,
        suggestion_id=501,
    )

    assert applied_suggestion.status == SuggestionStatus.ACCEPTED
    assert len(task_repo.created_tasks) == 2
    assert {task.user_id for task in task_repo.created_tasks} == {1, 2}
    assert all(task.title == "Sprint planning" for task in task_repo.created_tasks)
    assert all(
        task.planned_start_at == suggested_start_at for task in task_repo.created_tasks
    )
    assert all(
        task.planned_end_at == suggested_end_at for task in task_repo.created_tasks
    )
    assert all(task.estimated_minutes == 45 for task in task_repo.created_tasks)


def test_apply_scheduling_suggestion_is_idempotent_for_accepted_status() -> None:
    team_repo = _FakeTeamRepo()
    user_repo = _FakeUserRepo()
    team_service = TeamService(team_repo, user_repo)
    team = team_service.CreateTeamWorkspace(
        current_user_id=1, name="Core Team", description=None
    )
    team_service.AddTeamParticipant(
        current_user_id=1, team_id=team.id, participant_user_id=2
    )

    suggestion_repo = _FakeSuggestionRepo()
    task_repo = _FakeTaskRepo()
    scheduling_service = SchedulingService(
        suggestion_repo=suggestion_repo,
        scheduler_engine=_FakeSchedulerEngine(),
        task_repo=task_repo,
        availability_repo=_FakeEmptyRepo(),
        routine_repo=_FakeEmptyRepo(),
        skill_repo=_FakeSkillRepo(),
        team_service=team_service,
    )

    suggested_start_at = datetime.now(UTC).replace(second=0, microsecond=0)
    suggestion_repo.suggestions_by_id[502] = SimpleNamespace(
        id=502,
        team_id=team.id,
        generated_for_user_id=1,
        mentor_user_id=1,
        learner_user_id=2,
        participant_user_ids=[1, 2],
        collaboration_title="Daily sync",
        skill_id=10,
        suggested_start_at=suggested_start_at,
        suggested_end_at=suggested_start_at + timedelta(minutes=30),
        score=75.0,
        status=SuggestionStatus.ACCEPTED,
        explanation="already applied",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    applied_suggestion = scheduling_service.ApplySchedulingSuggestionToTimetable(
        user_id=1,
        suggestion_id=502,
    )

    assert applied_suggestion.status == SuggestionStatus.ACCEPTED
    assert task_repo.created_tasks == []


def test_apply_scheduling_suggestion_rejects_non_owner_user() -> None:
    team_repo = _FakeTeamRepo()
    user_repo = _FakeUserRepo()
    team_service = TeamService(team_repo, user_repo)
    team = team_service.CreateTeamWorkspace(
        current_user_id=1, name="Core Team", description=None
    )
    team_service.AddTeamParticipant(
        current_user_id=1, team_id=team.id, participant_user_id=2
    )

    suggestion_repo = _FakeSuggestionRepo()
    task_repo = _FakeTaskRepo()
    scheduling_service = SchedulingService(
        suggestion_repo=suggestion_repo,
        scheduler_engine=_FakeSchedulerEngine(),
        task_repo=task_repo,
        availability_repo=_FakeEmptyRepo(),
        routine_repo=_FakeEmptyRepo(),
        skill_repo=_FakeSkillRepo(),
        team_service=team_service,
    )

    suggested_start_at = datetime.now(UTC).replace(second=0, microsecond=0)
    suggestion_repo.suggestions_by_id[503] = SimpleNamespace(
        id=503,
        team_id=team.id,
        generated_for_user_id=1,
        mentor_user_id=1,
        learner_user_id=2,
        participant_user_ids=[1, 2],
        collaboration_title="Planning sync",
        skill_id=10,
        suggested_start_at=suggested_start_at,
        suggested_end_at=suggested_start_at + timedelta(minutes=30),
        score=81.0,
        status=SuggestionStatus.PENDING,
        explanation="best overlap found",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    with pytest.raises(NotFoundError):
        scheduling_service.ApplySchedulingSuggestionToTimetable(
            user_id=2,
            suggestion_id=503,
        )


def test_apply_scheduling_suggestion_rejects_conflicting_timetable_slot() -> None:
    team_repo = _FakeTeamRepo()
    user_repo = _FakeUserRepo()
    team_service = TeamService(team_repo, user_repo)
    team = team_service.CreateTeamWorkspace(
        current_user_id=1, name="Core Team", description=None
    )
    team_service.AddTeamParticipant(
        current_user_id=1, team_id=team.id, participant_user_id=2
    )

    suggestion_repo = _FakeSuggestionRepo()
    task_repo = _FakeTaskRepo()
    scheduling_service = SchedulingService(
        suggestion_repo=suggestion_repo,
        scheduler_engine=_FakeSchedulerEngine(),
        task_repo=task_repo,
        availability_repo=_FakeEmptyRepo(),
        routine_repo=_FakeEmptyRepo(),
        skill_repo=_FakeSkillRepo(),
        team_service=team_service,
    )

    suggested_start_at = datetime.now(UTC).replace(second=0, microsecond=0)
    suggested_end_at = suggested_start_at + timedelta(minutes=60)
    suggestion_repo.suggestions_by_id[504] = SimpleNamespace(
        id=504,
        team_id=team.id,
        generated_for_user_id=1,
        mentor_user_id=1,
        learner_user_id=2,
        participant_user_ids=[1, 2],
        collaboration_title="Conflict test sync",
        skill_id=10,
        suggested_start_at=suggested_start_at,
        suggested_end_at=suggested_end_at,
        score=92.0,
        status=SuggestionStatus.PENDING,
        explanation="best overlap found",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    task_repo.tasks_by_user[2] = [
        SimpleNamespace(
            id=1,
            user_id=2,
            title="Existing task",
            description=None,
            priority="medium",
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
        scheduling_service.ApplySchedulingSuggestionToTimetable(
            user_id=1,
            suggestion_id=504,
        )

    assert task_repo.created_tasks == []
    assert suggestion_repo.suggestions_by_id[504].status == SuggestionStatus.PENDING
