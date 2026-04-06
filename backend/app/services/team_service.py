"""Team workspace business logic."""

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.models.team import Team
from app.models.team_member import TeamMember
from app.repositories.team_repo import TeamRepository
from app.repositories.user_repo import UserRepository
from app.utils.logger import get_logger
from sqlalchemy.exc import IntegrityError

logger = get_logger(__name__)


class TeamService:
    """Business rules for team creation and membership checks."""

    def __init__(self, team_repo: TeamRepository, user_repo: UserRepository) -> None:
        self.team_repo = team_repo
        self.user_repo = user_repo

    def CreateTeamWorkspace(self, *, current_user_id: int, name: str, description: str | None) -> Team:
        """Create a team and add creator as first member."""
        owner_user = self.user_repo.get_by_id(current_user_id)
        if owner_user is None:
            logger.error("team create blocked: user not found for user_id=%s", current_user_id)
            raise NotFoundError("user not found")

        created_team = self.team_repo.create_team(
            name=name,
            description=description,
            owner_user_id=current_user_id,
        )
        self.team_repo.add_team_member(team_id=created_team.id, user_id=current_user_id)
        created_team = self.team_repo.get_team_by_id(created_team.id) or created_team
        logger.info("team create service completed for user_id=%s team_id=%s", current_user_id, created_team.id)
        return created_team

    def AddTeamParticipant(self, *, current_user_id: int, team_id: int, participant_user_id: int) -> TeamMember:
        """Add one user into a team when requested by the team owner."""
        team = self._get_team_or_raise(team_id)

        if team.owner_user_id != current_user_id:
            logger.error(
                "team add participant blocked: requester is not owner for user_id=%s team_id=%s",
                current_user_id,
                team_id,
            )
            raise ForbiddenError("only the team owner can add participants")

        participant_user = self.user_repo.get_by_id(participant_user_id)
        if participant_user is None:
            logger.error("team add participant blocked: user not found for user_id=%s", participant_user_id)
            raise NotFoundError("participant user not found")

        try:
            created_membership = self.team_repo.add_team_member(team_id=team_id, user_id=participant_user_id)
        except IntegrityError:
            if hasattr(self.team_repo, "db"):
                self.team_repo.db.rollback()
            logger.error(
                "team add participant blocked: membership already exists for team_id=%s user_id=%s",
                team_id,
                participant_user_id,
            )
            raise ConflictError("participant is already a member of this team")

        logger.info(
            "team add participant service completed for team_id=%s participant_user_id=%s",
            team_id,
            participant_user_id,
        )
        return created_membership

    def ListCurrentUserTeams(self, current_user_id: int) -> list[Team]:
        """Return teams where the current user is a member."""
        teams = self.team_repo.list_teams_for_user(current_user_id)
        logger.info("team list service completed for user_id=%s count=%s", current_user_id, len(teams))
        return teams

    def ListTeamParticipants(self, *, current_user_id: int, team_id: int) -> list[TeamMember]:
        """Return members for one team if requester belongs to that team."""
        self._get_team_or_raise(team_id)
        self.AssertUserBelongsToTeam(team_id=team_id, user_id=current_user_id)
        team_members = self.team_repo.list_team_members(team_id)
        logger.info(
            "team list participants service completed for team_id=%s count=%s",
            team_id,
            len(team_members),
        )
        return team_members

    def AssertUserBelongsToTeam(self, *, team_id: int, user_id: int) -> None:
        """Raise an error when one user is not a member of the requested team."""
        self._get_team_or_raise(team_id)
        membership = self.team_repo.get_team_member(team_id=team_id, user_id=user_id)
        if membership is None:
            logger.error(
                "team membership check failed: user_id=%s is not in team_id=%s",
                user_id,
                team_id,
            )
            raise ForbiddenError("user is not a member of this team")

    def AssertParticipantsBelongToTeam(self, *, team_id: int, participant_user_ids: list[int]) -> None:
        """Raise when any participant is not a member of the requested team."""
        self._get_team_or_raise(team_id)
        for participant_user_id in participant_user_ids:
            membership = self.team_repo.get_team_member(team_id=team_id, user_id=participant_user_id)
            if membership is None:
                logger.error("team participant membership check failed for team_id=%s", team_id)
                raise ForbiddenError("one or more participants are not members of this team")

    def _get_team_or_raise(self, team_id: int) -> Team:
        """Get one team or raise when not found."""
        team = self.team_repo.get_team_by_id(team_id)
        if team is None:
            logger.error("team lookup blocked: team not found for team_id=%s", team_id)
            raise NotFoundError("team not found")
        return team
