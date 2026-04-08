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
from app.utils.request_validation import (
    ensure_positive_id,
)

logger = get_logger(__name__)


class SessionHandler:
    """Maps session requests to session service calls."""

    def __init__(self, session_service: SessionService) -> None:
        self.session_service = session_service

    def createSessionFromSuggestion(
        self, user_id: int, payload: SessionCreateFromSuggestionRequest
    ) -> SessionDetailResponse:
        """Handle session creation from a suggestion."""
        try:
            # Validate request input.
            ensure_positive_id(user_id, field_name="user_id")
            ensure_positive_id(payload.suggestion_id, field_name="suggestion_id")

            # Call service layer.
            created_session = self.session_service.CreateSessionFromSuggestion(
                user_id,
                suggestion_id=payload.suggestion_id,
                title=payload.title,
            )
            session_detail_response = self._build_session_detail(created_session)
            logger.info("session create from suggestion handler completed")
            return session_detail_response
        except AppError:
            logger.exception("session create from suggestion handler failed")
            raise

    def listSessions(self, user_id: int) -> list[SessionResponse]:
        """Handle session list requests."""
        try:
            # Validate request input.
            ensure_positive_id(user_id, field_name="user_id")

            # Call service layer.
            scheduled_sessions = self.session_service.ListSessions(user_id)
            session_responses = [
                SessionResponse.model_validate(session)
                for session in scheduled_sessions
            ]
            logger.info("session list handler completed")
            return session_responses
        except AppError:
            logger.exception("session list handler failed")
            raise

    def getSessionById(self, user_id: int, session_id: int) -> SessionDetailResponse:
        """Handle single-session detail requests."""
        try:
            # Validate request input.
            ensure_positive_id(user_id, field_name="user_id")
            ensure_positive_id(session_id, field_name="session_id")

            # Call service layer.
            session_record = self.session_service.GetSessionById(user_id, session_id)
            session_detail_response = self._build_session_detail(session_record)
            logger.info("session get by id handler completed")
            return session_detail_response
        except AppError:
            logger.exception("session get by id handler failed")
            raise

    def _build_session_detail(self, session: object) -> SessionDetailResponse:
        """Build a session response that includes participants."""
        ordered_participants = sorted(
            getattr(session, "participants", []),
            key=lambda participant: getattr(participant, "id"),
        )
        participants = [
            self._build_participant_response(participant, participant_index=index + 1)
            for index, participant in enumerate(ordered_participants)
        ]
        return SessionDetailResponse(
            **SessionResponse.model_validate(session).model_dump(),
            participants=participants,
        )

    def _build_participant_response(
        self, participant: object, *, participant_index: int
    ) -> SessionParticipantResponse:
        """Build one participant response with a neutral collaboration role label."""
        participant_role = getattr(participant, "participant_role")
        collaboration_role = f"participant_{participant_index}"
        return SessionParticipantResponse(
            id=getattr(participant, "id"),
            session_id=getattr(participant, "session_id"),
            user_id=getattr(participant, "user_id"),
            participant_role=participant_role,
            collaboration_role=collaboration_role,
            response_status=getattr(participant, "response_status"),
            joined_at=getattr(participant, "joined_at"),
            created_at=getattr(participant, "created_at"),
        )
