"""Team workspace API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.handlers.team_handler import TeamHandler
from app.core.dependencies import CurrentUserId, get_db
from app.repositories.team_repo import TeamRepository
from app.repositories.user_repo import UserRepository
from app.schemas.team import (
    TeamAddParticipantRequest,
    TeamMemberResponse,
    TeamCreateRequest,
    TeamResponse,
)
from app.services.team_service import TeamService

router = APIRouter(prefix="/teams", tags=["teams"])


def get_team_handler(db: Annotated[Session, Depends(get_db)]) -> TeamHandler:
    """Build the team dependency chain for route handlers."""
    team_repo = TeamRepository(db)
    user_repo = UserRepository(db)
    team_service = TeamService(team_repo, user_repo)
    return TeamHandler(team_service)


@router.post("", response_model=TeamResponse, status_code=status.HTTP_201_CREATED)
def create_team_workspace(payload: TeamCreateRequest, current_user_id: CurrentUserId, handler: Annotated[TeamHandler, Depends(get_team_handler)]) -> TeamResponse:
    """Create one team workspace and set current user as owner."""
    return handler.createTeamWorkspace(current_user_id, payload)


@router.get("", response_model=list[TeamResponse])
def list_current_user_teams(current_user_id: CurrentUserId, handler: Annotated[TeamHandler, Depends(get_team_handler)]) -> list[TeamResponse]:
    """Return all teams where current user is a member."""
    return handler.listCurrentUserTeams(current_user_id)


@router.post("/{team_id}/members", response_model=TeamMemberResponse, status_code=status.HTTP_201_CREATED)
def add_team_participant(team_id: int, payload: TeamAddParticipantRequest, current_user_id: CurrentUserId, handler: Annotated[TeamHandler, Depends(get_team_handler)]) -> TeamMemberResponse:
    """Add one participant to a team workspace."""
    return handler.addTeamParticipant(current_user_id, team_id, payload)


@router.get("/{team_id}/members", response_model=list[TeamMemberResponse])
def list_team_participants(team_id: int, current_user_id: CurrentUserId, handler: Annotated[TeamHandler, Depends(get_team_handler)]) -> list[TeamMemberResponse]:
    """Return participants in one team workspace."""
    return handler.listTeamParticipants(current_user_id, team_id)
