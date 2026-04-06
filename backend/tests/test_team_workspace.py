from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest
from sqlalchemy.exc import IntegrityError

from app.core.exceptions import ConflictError, ForbiddenError
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
        team_ids = [team_id for (team_id, member_user_id) in self.memberships if member_user_id == user_id]
        return [self.teams[item] for item in team_ids]

    def add_team_member(self, *, team_id: int, user_id: int):
        if (team_id, user_id) in self.memberships:
            raise IntegrityError("duplicate membership", params=None, orig=Exception("duplicate membership"))
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
        return [item for (member_team_id, _), item in self.memberships.items() if member_team_id == team_id]


class _FakeSuggestionRepo:
    def __init__(self) -> None:
        self.last_create_payload = None

    def create_suggestion(self, **kwargs):
        self.last_create_payload = kwargs
        return SimpleNamespace(
            id=101,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            **kwargs,
        )

    def list_suggestions_for_user(self, user_id: int):
        return []

    def get_suggestion_by_id(self, suggestion_id: int):
        return None

    def update_suggestion(self, suggestion, **updates):
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

    team = service.CreateTeamWorkspace(current_user_id=1, name="Core Team", description="MVP workspace")

    assert team.id == 1
    assert team.owner_user_id == 1
    assert team_repo.get_team_member(team_id=team.id, user_id=1) is not None


def test_add_team_participant_requires_owner() -> None:
    team_repo = _FakeTeamRepo()
    user_repo = _FakeUserRepo()
    service = TeamService(team_repo, user_repo)
    team = service.CreateTeamWorkspace(current_user_id=1, name="Core Team", description=None)

    with pytest.raises(ForbiddenError):
        service.AddTeamParticipant(current_user_id=2, team_id=team.id, participant_user_id=3)


def test_add_team_participant_maps_duplicate_membership_to_conflict_error() -> None:
    team_repo = _FakeTeamRepo()
    user_repo = _FakeUserRepo()
    service = TeamService(team_repo, user_repo)
    team = service.CreateTeamWorkspace(current_user_id=1, name="Core Team", description=None)

    service.AddTeamParticipant(current_user_id=1, team_id=team.id, participant_user_id=2)
    with pytest.raises(ConflictError):
        service.AddTeamParticipant(current_user_id=1, team_id=team.id, participant_user_id=2)


def test_generate_scheduling_suggestion_rejects_participant_outside_team() -> None:
    team_repo = _FakeTeamRepo()
    user_repo = _FakeUserRepo()
    team_service = TeamService(team_repo, user_repo)
    team = team_service.CreateTeamWorkspace(current_user_id=1, name="Core Team", description=None)
    team_service.AddTeamParticipant(current_user_id=1, team_id=team.id, participant_user_id=2)

    scheduling_service = SchedulingService(
        suggestion_repo=_FakeSuggestionRepo(),
        scheduler_engine=_FakeSchedulerEngine(),
        task_repo=_FakeEmptyRepo(),
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
    team = team_service.CreateTeamWorkspace(current_user_id=1, name="Core Team", description=None)
    team_service.AddTeamParticipant(current_user_id=1, team_id=team.id, participant_user_id=2)

    suggestion_repo = _FakeSuggestionRepo()
    scheduling_service = SchedulingService(
        suggestion_repo=suggestion_repo,
        scheduler_engine=_FakeSchedulerEngine(),
        task_repo=_FakeEmptyRepo(),
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
