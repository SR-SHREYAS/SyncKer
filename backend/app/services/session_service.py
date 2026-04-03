"""Session business logic."""

from app.core.exceptions import ConflictError, NotFoundError
from app.models.enums import (
    ParticipantResponseStatus,
    ParticipantRole,
    SessionStatus,
    SuggestionStatus,
)
from app.models.session import Session
from app.repositories.session_repo import SessionRepository
from app.repositories.suggestion_repo import SuggestionRepository
from app.utils.logger import get_logger

logger = get_logger(__name__)


class SessionService:
    """Business rules for booked sessions."""

    def __init__(
        self,
        session_repo: SessionRepository,
        suggestion_repo: SuggestionRepository,
    ) -> None:
        self.session_repo = session_repo
        self.suggestion_repo = suggestion_repo

    def CreateSessionFromSuggestion(self, user_id: int, *, suggestion_id: int, title: str) -> Session:
        """Create a booked session from one owned suggestion."""
        suggestion = self.suggestion_repo.get_suggestion_by_id(suggestion_id)
        if suggestion is None or suggestion.generated_for_user_id != user_id:
            logger.error(
                "session create blocked: suggestion not found for user_id=%s suggestion_id=%s",
                user_id,
                suggestion_id,
            )
            raise NotFoundError("suggestion not found")

        existing_session = self.session_repo.get_session_by_suggestion_id(suggestion_id)
        if existing_session is not None:
            logger.error(
                "session create blocked: session already exists for suggestion_id=%s",
                suggestion_id,
            )
            raise ConflictError("session already exists for this suggestion")

        session = self.session_repo.create_session(
            session_suggestion_id=suggestion.id,
            skill_id=suggestion.skill_id,
            title=title,
            scheduled_start_at=suggestion.suggested_start_at,
            scheduled_end_at=suggestion.suggested_end_at,
            status=SessionStatus.SCHEDULED,
            created_by_user_id=user_id,
        )
        self.session_repo.create_participant(
            session_id=session.id,
            user_id=suggestion.mentor_user_id,
            participant_role=ParticipantRole.MENTOR,
            response_status=ParticipantResponseStatus.ACCEPTED,
        )
        self.session_repo.create_participant(
            session_id=session.id,
            user_id=suggestion.learner_user_id,
            participant_role=ParticipantRole.LEARNER,
            response_status=ParticipantResponseStatus.ACCEPTED,
        )
        self.suggestion_repo.update_suggestion(suggestion, status=SuggestionStatus.ACCEPTED)
        session = self.session_repo.get_session_by_id(session.id) or session
        logger.info("session create service completed for user_id=%s session_id=%s", user_id, session.id)
        return session

    def ListSessions(self, user_id: int) -> list[Session]:
        """Return sessions created by the current user."""
        sessions = self.session_repo.list_sessions_for_user(user_id)
        logger.info("session list service completed for user_id=%s count=%s", user_id, len(sessions))
        return sessions

    def GetSessionById(self, user_id: int, session_id: int) -> Session:
        """Return one owned session."""
        session = self.session_repo.get_session_by_id(session_id)
        if session is None or session.created_by_user_id != user_id:
            logger.error("session get blocked: session not found for user_id=%s session_id=%s", user_id, session_id)
            raise NotFoundError("session not found")
        logger.info("session get service completed for user_id=%s session_id=%s", user_id, session_id)
        return session
