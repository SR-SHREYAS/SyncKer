"""Session persistence queries."""

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.session import Session as SessionModel
from app.models.session_participant import SessionParticipant


class SessionRepository:
    """Database access for sessions and session participants."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create_session(
        self,
        *,
        session_suggestion_id: int | None,
        skill_id: int,
        title: str,
        scheduled_start_at: object,
        scheduled_end_at: object,
        status: str,
        created_by_user_id: int,
    ) -> SessionModel:
        """Insert one scheduled session."""
        session = SessionModel(
            session_suggestion_id=session_suggestion_id,
            skill_id=skill_id,
            title=title,
            scheduled_start_at=scheduled_start_at,
            scheduled_end_at=scheduled_end_at,
            status=status,
            created_by_user_id=created_by_user_id,
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def get_session_by_id(self, session_id: int) -> SessionModel | None:
        """Fetch one session with participants loaded."""
        stmt = (
            select(SessionModel)
            .options(joinedload(SessionModel.participants))
            .where(SessionModel.id == session_id)
        )
        return self.db.execute(stmt).unique().scalar_one_or_none()

    def list_sessions_for_user(self, user_id: int) -> list[SessionModel]:
        """Return sessions created by one user."""
        stmt = (
            select(SessionModel)
            .where(SessionModel.created_by_user_id == user_id)
            .order_by(SessionModel.created_at.desc())
        )
        return list(self.db.execute(stmt).scalars().all())

    def update_session(self, session: SessionModel, **updates: object) -> SessionModel:
        """Apply field updates to an existing session."""
        for field, value in updates.items():
            setattr(session, field, value)

        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def create_participant(
        self,
        *,
        session_id: int,
        user_id: int,
        participant_role: str,
        response_status: str,
        joined_at: object = None,
    ) -> SessionParticipant:
        """Insert one participant for a session."""
        participant = SessionParticipant(
            session_id=session_id,
            user_id=user_id,
            participant_role=participant_role,
            response_status=response_status,
            joined_at=joined_at,
        )
        self.db.add(participant)
        self.db.commit()
        self.db.refresh(participant)
        return participant

    def list_participants(self, session_id: int) -> list[SessionParticipant]:
        """Return participants linked to one session."""
        stmt = (
            select(SessionParticipant)
            .where(SessionParticipant.session_id == session_id)
            .order_by(SessionParticipant.created_at.asc())
        )
        return list(self.db.execute(stmt).scalars().all())

    def update_participant(self, participant: SessionParticipant, **updates: object) -> SessionParticipant:
        """Apply field updates to an existing session participant."""
        for field, value in updates.items():
            setattr(participant, field, value)

        self.db.add(participant)
        self.db.commit()
        self.db.refresh(participant)
        return participant
