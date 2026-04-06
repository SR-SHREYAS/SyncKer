"""Team workspace request handlers."""

from app.core.exceptions import AppError, InternalServerError
from app.schemas.team import (
    TeamAddParticipantRequest,
    TeamMemberResponse,
    TeamCreateRequest,
    TeamResponse,
)
from app.services.team_service import TeamService
from app.utils.logger import get_logger
from app.utils.request_validation import ensure_positive_id

logger = get_logger(__name__)


class TeamHandler:
    """Maps team routes to team service calls."""

    def __init__(self, team_service: TeamService) -> None:
        self.team_service = team_service

    def createTeamWorkspace(self, current_user_id: int, payload: TeamCreateRequest) -> TeamResponse:
        """Handle team workspace creation requests."""
        try:
            ensure_positive_id(current_user_id, field_name="current_user_id")
            created_team = self.team_service.CreateTeamWorkspace(
                current_user_id=current_user_id,
                name=payload.name,
                description=payload.description,
            )
            team_response = TeamResponse.model_validate(created_team)
            logger.info("team create workspace handler completed")
            return team_response
        except AppError:
            logger.exception("team create workspace handler failed")
            raise

    def listCurrentUserTeams(self, current_user_id: int) -> list[TeamResponse]:
        """Handle list-team requests for the current user."""
        try:
            ensure_positive_id(current_user_id, field_name="current_user_id")
            teams = self.team_service.ListCurrentUserTeams(current_user_id)
            team_responses = [TeamResponse.model_validate(team) for team in teams]
            logger.info("team list current user teams handler completed")
            return team_responses
        except AppError:
            logger.exception("team list current user teams handler failed")
            raise

    def addTeamParticipant(
        self,
        current_user_id: int,
        team_id: int,
        payload: TeamAddParticipantRequest,
    ) -> TeamMemberResponse:
        """Handle team participant addition requests."""
        try:
            ensure_positive_id(current_user_id, field_name="current_user_id")
            ensure_positive_id(team_id, field_name="team_id")
            ensure_positive_id(
                payload.participant_user_id, field_name="participant_user_id"
            )
            added_member = self.team_service.AddTeamParticipant(
                current_user_id=current_user_id,
                team_id=team_id,
                participant_user_id=payload.participant_user_id,
            )
            member_response = self._build_team_member_response(added_member)
            logger.info("team add participant handler completed")
            return member_response
        except AppError:
            logger.exception("team add participant handler failed")
            raise

    def listTeamParticipants(self, current_user_id: int, team_id: int) -> list[TeamMemberResponse]:
        """Handle list-team-participants requests."""
        try:
            ensure_positive_id(current_user_id, field_name="current_user_id")
            ensure_positive_id(team_id, field_name="team_id")
            team_members = self.team_service.ListTeamParticipants(
                current_user_id=current_user_id,
                team_id=team_id,
            )
            member_responses = [
                self._build_team_member_response(member) for member in team_members
            ]
            logger.info("team list participants handler completed")
            return member_responses
        except AppError:
            logger.exception("team list participants handler failed")
            raise

    def _build_team_member_response(self, member: object) -> TeamMemberResponse:
        """Shape team membership output with user identity fields."""
        user = getattr(member, "user", None)
        if user is None:
            raise InternalServerError("team member user relationship not loaded")
        return TeamMemberResponse(
            team_member_id=getattr(member, "id"),
            team_id=getattr(member, "team_id"),
            user_id=getattr(member, "user_id"),
            username=getattr(user, "username"),
            email=getattr(user, "email"),
            joined_at=getattr(member, "created_at"),
        )
