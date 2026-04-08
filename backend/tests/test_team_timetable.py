from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from app.api.handlers.planning_handler import PlanningHandler
from app.core.exceptions import ForbiddenError
from app.models.enums import TaskPriority, TaskStatus
from app.services.planning_service import PlanningService
from app.services.team_service import TeamService


class _FakeUserRepo:
    def __init__(self) -> None:
        self.users = {
            1: SimpleNamespace(id=1, username="owner", email="owner@example.com"),
            2: SimpleNamespace(id=2, username="member", email="member@example.com"),
            3: SimpleNamespace(id=3, username="viewer", email="viewer@example.com"),
        }

    def get_by_id(self, user_id: int):
        return self.users.get(user_id)


class _FakeTeamRepo:
    def __init__(self, user_repo: _FakeUserRepo) -> None:
        self.user_repo = user_repo
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
        membership = SimpleNamespace(
            id=self._next_membership_id,
            team_id=team_id,
            user_id=user_id,
            user=self.user_repo.get_by_id(user_id),
            created_at=datetime.now(UTC),
        )
        self.memberships[(team_id, user_id)] = membership
        self._next_membership_id += 1
        return membership

    def get_team_member(self, *, team_id: int, user_id: int):
        return self.memberships.get((team_id, user_id))

    def list_team_members(self, team_id: int):
        return [
            member
            for (member_team_id, _), member in self.memberships.items()
            if member_team_id == team_id
        ]


class _FakeTaskRepo:
    def __init__(self) -> None:
        self.tasks_by_user: dict[int, list[SimpleNamespace]] = {}

    def list_tasks_by_user(self, user_id: int):
        return self.tasks_by_user.get(user_id, [])

    def list_tasks_by_users(self, *, user_ids: list[int]):
        all_tasks: list[SimpleNamespace] = []
        for user_id in user_ids:
            all_tasks.extend(self.tasks_by_user.get(user_id, []))
        return all_tasks


class _FakeEmptyRepo:
    pass


def _build_task(*, task_id: int, user_id: int, title: str) -> SimpleNamespace:
    current_time = datetime.now(UTC)
    return SimpleNamespace(
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
        created_at=current_time,
        updated_at=current_time,
    )


def _build_planning_handler() -> tuple[PlanningHandler, _FakeTaskRepo, TeamService]:
    user_repo = _FakeUserRepo()
    team_repo = _FakeTeamRepo(user_repo)
    team_service = TeamService(team_repo, user_repo)
    task_repo = _FakeTaskRepo()
    planning_service = PlanningService(
        task_repo=task_repo,
        availability_repo=_FakeEmptyRepo(),
        routine_repo=_FakeEmptyRepo(),
        team_service=team_service,
    )
    return PlanningHandler(planning_service), task_repo, team_service


def test_list_team_timetable_returns_tasks_for_team_members() -> None:
    planning_handler, task_repo, team_service = _build_planning_handler()
    team = team_service.CreateTeamWorkspace(
        current_user_id=1,
        name="Sync Team",
        description=None,
    )
    team_service.AddTeamParticipant(
        current_user_id=1,
        team_id=team.id,
        participant_user_id=2,
    )

    task_repo.tasks_by_user[1] = [
        _build_task(task_id=11, user_id=1, title="Owner Task")
    ]
    task_repo.tasks_by_user[2] = [
        _build_task(task_id=21, user_id=2, title="Member Task")
    ]

    response = planning_handler.listTeamTimetable(current_user_id=1, team_id=team.id)

    assert response.team_id == team.id
    assert len(response.participants) == 2
    assert response.participants[0].user_id == 1
    assert response.participants[0].tasks[0].title == "Owner Task"
    assert response.participants[1].user_id == 2
    assert response.participants[1].tasks[0].title == "Member Task"


def test_list_team_timetable_blocks_non_member_user() -> None:
    planning_handler, task_repo, team_service = _build_planning_handler()
    team = team_service.CreateTeamWorkspace(
        current_user_id=1,
        name="Sync Team",
        description=None,
    )
    team_service.AddTeamParticipant(
        current_user_id=1,
        team_id=team.id,
        participant_user_id=2,
    )
    task_repo.tasks_by_user[1] = [
        _build_task(task_id=11, user_id=1, title="Owner Task")
    ]

    with pytest.raises(ForbiddenError):
        planning_handler.listTeamTimetable(current_user_id=3, team_id=team.id)


def test_list_team_timetable_returns_empty_task_lists() -> None:
    planning_handler, task_repo, team_service = _build_planning_handler()
    team = team_service.CreateTeamWorkspace(
        current_user_id=1,
        name="Sync Team",
        description=None,
    )
    team_service.AddTeamParticipant(
        current_user_id=1,
        team_id=team.id,
        participant_user_id=2,
    )
    task_repo.tasks_by_user[1] = []
    task_repo.tasks_by_user[2] = []

    response = planning_handler.listTeamTimetable(current_user_id=1, team_id=team.id)

    assert response.team_id == team.id
    assert len(response.participants) == 2
    assert response.participants[0].tasks == []
    assert response.participants[1].tasks == []
