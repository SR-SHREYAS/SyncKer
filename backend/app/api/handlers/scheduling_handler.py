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
    ensure_distinct_ids,
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
            ensure_positive_id(payload.learner_user_id, field_name="learner_user_id")
            ensure_positive_id(payload.mentor_user_id, field_name="mentor_user_id")
            ensure_positive_id(payload.skill_id, field_name="skill_id")
            ensure_distinct_ids(
                payload.learner_user_id,
                payload.mentor_user_id,
                context="suggestion generation",
            )

            suggestion = self.scheduling_service.GenerateSchedulingSuggestion(
                generated_for_user_id=user_id,
                learner_user_id=payload.learner_user_id,
                mentor_user_id=payload.mentor_user_id,
                skill_id=payload.skill_id,
                window_start_at=payload.window_start_at,
                window_end_at=payload.window_end_at,
                minimum_duration_minutes=payload.minimum_duration_minutes,
            )
            response = SessionSuggestionResponse.model_validate(suggestion)
            logger.info(
                "scheduling generateSchedulingSuggestion handled for user_id=%s suggestion_id=%s",
                user_id,
                suggestion.id,
            )
            return response
        except AppError:
            logger.exception("scheduling generateSchedulingSuggestion failed for user_id=%s", user_id)
            raise

    def listSchedulingSuggestions(self, user_id: int) -> list[SessionSuggestionResponse]:
        """Handle suggestion list requests."""
        try:
            ensure_positive_id(user_id, field_name="user_id")
            suggestions = self.scheduling_service.ListSchedulingSuggestions(user_id)
            response = [SessionSuggestionResponse.model_validate(item) for item in suggestions]
            logger.info("scheduling listSchedulingSuggestions handled for user_id=%s count=%s", user_id, len(response))
            return response
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
            suggestion = self.scheduling_service.UpdateSchedulingSuggestionStatus(
                user_id,
                suggestion_id,
                status=payload.status,
            )
            response = SessionSuggestionResponse.model_validate(suggestion)
            logger.info(
                "scheduling updateSchedulingSuggestionStatus handled for user_id=%s suggestion_id=%s",
                user_id,
                suggestion_id,
            )
            return response
        except AppError:
            logger.exception(
                "scheduling updateSchedulingSuggestionStatus failed for user_id=%s suggestion_id=%s",
                user_id,
                suggestion_id,
            )
            raise
