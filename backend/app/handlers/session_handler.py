"""Session request handlers."""

from app.core.exceptions import AppError
from app.schemas.session import (
    SessionCreateFromSuggestionRequest,
    SessionDetailResponse,
    SessionParticipantResponse,
    SessionResponse,
)
from app.services.session_service import SessionService
from app.utils.logger import get_logger

logger = get_logger(__name__)


class SessionHandler:
    """Maps session requests to session service calls."""

    def __init__(self, session_service: SessionService) -> None:
        self.session_service = session_service

    def create_from_suggestion(
        self,
        user_id: int,
        payload: SessionCreateFromSuggestionRequest,
    ) -> SessionDetailResponse:
        """Handle session creation from a suggestion."""
        try:
            session = self.session_service.create_from_suggestion(
                user_id,
                suggestion_id=payload.suggestion_id,
                title=payload.title,
            )
            response = self._build_session_detail(session)
            logger.info("session create handled for user_id=%s session_id=%s", user_id, session.id)
            return response
        except AppError:
            logger.exception("session create failed for user_id=%s suggestion_id=%s", user_id, payload.suggestion_id)
            raise

    def list_sessions(self, user_id: int) -> list[SessionResponse]:
        """Handle session list requests."""
        try:
            sessions = self.session_service.list_sessions(user_id)
            response = [SessionResponse.model_validate(session) for session in sessions]
            logger.info("session list handled for user_id=%s count=%s", user_id, len(response))
            return response
        except AppError:
            logger.exception("session list failed for user_id=%s", user_id)
            raise

    def get_session(self, user_id: int, session_id: int) -> SessionDetailResponse:
        """Handle single-session detail requests."""
        try:
            session = self.session_service.get_session(user_id, session_id)
            response = self._build_session_detail(session)
            logger.info("session get handled for user_id=%s session_id=%s", user_id, session_id)
            return response
        except AppError:
            logger.exception("session get failed for user_id=%s session_id=%s", user_id, session_id)
            raise

    def _build_session_detail(self, session: object) -> SessionDetailResponse:
        """Build a session response that includes participants."""
        participants = [
            SessionParticipantResponse.model_validate(participant)
            for participant in getattr(session, "participants", [])
        ]
        return SessionDetailResponse(
            **SessionResponse.model_validate(session).model_dump(),
            participants=participants,
        )
