"""Team persistence queries."""

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.team import Team
from app.models.team_member import TeamMember


class TeamRepository:
    """Database access for team workspaces and members."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create_team(self, *, name: str, description: str | None, owner_user_id: int) -> Team:
        """Insert one team workspace."""
        team = Team(name=name, description=description, owner_user_id=owner_user_id)
        self.db.add(team)
        self.db.commit()
        self.db.refresh(team)
        return team

    def get_team_by_id(self, team_id: int) -> Team | None:
        """Fetch one team by primary key."""
        stmt = (
            select(Team)
            .options(joinedload(Team.members).joinedload(TeamMember.user))
            .where(Team.id == team_id)
        )
        return self.db.execute(stmt).unique().scalar_one_or_none()

    def list_teams_for_user(self, user_id: int) -> list[Team]:
        """Return all teams where the user is a member."""
        stmt = (
            select(Team)
            .join(TeamMember, TeamMember.team_id == Team.id)
            .where(TeamMember.user_id == user_id)
            .order_by(Team.created_at.desc())
        )
        return list(self.db.execute(stmt).scalars().all())

    def add_team_member(self, *, team_id: int, user_id: int) -> TeamMember:
        """Insert one team membership."""
        membership = TeamMember(team_id=team_id, user_id=user_id)
        self.db.add(membership)
        self.db.commit()
        self.db.refresh(membership)
        return membership

    def get_team_member(self, *, team_id: int, user_id: int) -> TeamMember | None:
        """Fetch one team membership by team and user ids."""
        stmt = select(TeamMember).where(TeamMember.team_id == team_id, TeamMember.user_id == user_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def list_team_members(self, team_id: int) -> list[TeamMember]:
        """Return team members with user details."""
        stmt = (
            select(TeamMember)
            .options(joinedload(TeamMember.user))
            .where(TeamMember.team_id == team_id)
            .order_by(TeamMember.created_at.asc())
        )
        return list(self.db.execute(stmt).scalars().all())
