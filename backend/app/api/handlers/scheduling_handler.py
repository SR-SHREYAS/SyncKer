"""Scheduling request handlers."""

from app.core.exceptions import AppError
from app.schemas.scheduling import (
    SessionSuggestionResponse,
    SuggestionGenerationRequest,
    SuggestionStatusUpdateRequest,
)
from app.services.scheduling_service import SchedulingService
from app.utils.logger import get_logger
from app.utils.request_validation import (
    ensure_id_in_list,
    ensure_optional_id_is_positive,
    ensure_participant_ids_list,
    ensure_positive_id,
)

logger = get_logger(__name__)


class SchedulingHandler:
    """Maps scheduling requests to scheduling service calls."""

    def __init__(self, scheduling_service: SchedulingService) -> None:
        self.scheduling_service = scheduling_service

    def generateSchedulingSuggestion(
        self,
        user_id: int,
        payload: SuggestionGenerationRequest,
    ) -> SessionSuggestionResponse:
        """Handle suggestion generation requests."""
        try:
            ensure_positive_id(user_id, field_name="user_id")
            ensure_positive_id(payload.team_id, field_name="team_id")
            ensure_optional_id_is_positive(payload.skill_id, field_name="skill_id")
            ensure_participant_ids_list(
                payload.participant_user_ids,
                context="suggestion generation",
            )
            ensure_id_in_list(
                value=user_id,
                values=payload.participant_user_ids,
                field_name="current_user_id",
                context="suggestion generation",
            )

            created_suggestion = self.scheduling_service.GenerateSchedulingSuggestion(
                team_id=payload.team_id,
                generated_for_user_id=user_id,
                participant_user_ids=payload.participant_user_ids,
                collaboration_title=payload.collaboration_title,
                skill_id=payload.skill_id,
                window_start_at=payload.window_start_at,
                window_end_at=payload.window_end_at,
                minimum_duration_minutes=payload.minimum_duration_minutes,
            )
            suggestion_response = self._build_suggestion_response(created_suggestion)
            logger.info(
                "scheduling generateSchedulingSuggestion handled for user_id=%s suggestion_id=%s",
                user_id,
                created_suggestion.id,
            )
            return suggestion_response
        except AppError:
            logger.exception("scheduling generateSchedulingSuggestion failed for user_id=%s", user_id)
            raise

    def listSchedulingSuggestions(self, user_id: int) -> list[SessionSuggestionResponse]:
        """Handle suggestion list requests."""
        try:
            ensure_positive_id(user_id, field_name="user_id")
            scheduling_suggestions = self.scheduling_service.ListSchedulingSuggestions(user_id)
            suggestion_responses = [self._build_suggestion_response(item) for item in scheduling_suggestions]
            logger.info(
                "scheduling listSchedulingSuggestions handled for user_id=%s count=%s",
                user_id,
                len(suggestion_responses),
            )
            return suggestion_responses
        except AppError:
            logger.exception("scheduling listSchedulingSuggestions failed for user_id=%s", user_id)
            raise

    def updateSchedulingSuggestionStatus(
        self,
        user_id: int,
        suggestion_id: int,
        payload: SuggestionStatusUpdateRequest,
    ) -> SessionSuggestionResponse:
        """Handle suggestion status update requests."""
        try:
            ensure_positive_id(user_id, field_name="user_id")
            ensure_positive_id(suggestion_id, field_name="suggestion_id")
            updated_suggestion = self.scheduling_service.UpdateSchedulingSuggestionStatus(
                user_id,
                suggestion_id,
                status=payload.status,
            )
            suggestion_response = self._build_suggestion_response(updated_suggestion)
            logger.info(
                "scheduling updateSchedulingSuggestionStatus handled for user_id=%s suggestion_id=%s",
                user_id,
                suggestion_id,
            )
            return suggestion_response
        except AppError:
            logger.exception(
                "scheduling updateSchedulingSuggestionStatus failed for user_id=%s suggestion_id=%s",
                user_id,
                suggestion_id,
            )
            raise

    def _build_suggestion_response(self, suggestion: object) -> SessionSuggestionResponse:
        """Build a neutral participant-based response for scheduling suggestions."""
        participant_user_ids = getattr(suggestion, "participant_user_ids", None)
        if not participant_user_ids:
            participant_user_ids = [
                getattr(suggestion, "mentor_user_id"),
                getattr(suggestion, "learner_user_id"),
            ]
        return SessionSuggestionResponse(
            id=getattr(suggestion, "id"),
            team_id=getattr(suggestion, "team_id", None),
            generated_for_user_id=getattr(suggestion, "generated_for_user_id"),
            participant_user_ids=list(participant_user_ids),
            collaboration_title=getattr(suggestion, "collaboration_title", "Collaboration Session"),
            skill_id=getattr(suggestion, "skill_id"),
            suggested_start_at=getattr(suggestion, "suggested_start_at"),
            suggested_end_at=getattr(suggestion, "suggested_end_at"),
            score=float(getattr(suggestion, "score")),
            status=getattr(suggestion, "status"),
            explanation=getattr(suggestion, "explanation"),
            created_at=getattr(suggestion, "created_at"),
        )
