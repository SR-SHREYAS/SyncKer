"""Scheduling request handlers."""

from app.core.exceptions import AppError
from app.schemas.scheduling import (
    SessionSuggestionResponse,
    SuggestionGenerationRequest,
    SuggestionStatusUpdateRequest,
)
from app.services.scheduling_service import SchedulingService
from app.utils.logger import get_logger

logger = get_logger(__name__)


class SchedulingHandler:
    """Maps scheduling requests to scheduling service calls."""

    def __init__(self, scheduling_service: SchedulingService) -> None:
        self.scheduling_service = scheduling_service

    def generate_suggestion(
        self,
        user_id: int,
        payload: SuggestionGenerationRequest,
    ) -> SessionSuggestionResponse:
        """Handle suggestion generation requests."""
        try:
            suggestion = self.scheduling_service.generate_suggestion(
                generated_for_user_id=user_id,
                learner_user_id=payload.learner_user_id,
                mentor_user_id=payload.mentor_user_id,
                skill_id=payload.skill_id,
                window_start_at=payload.window_start_at,
                window_end_at=payload.window_end_at,
                minimum_duration_minutes=payload.minimum_duration_minutes,
            )
            response = SessionSuggestionResponse.model_validate(suggestion)
            logger.info("scheduling generate handled for user_id=%s suggestion_id=%s", user_id, suggestion.id)
            return response
        except AppError:
            logger.exception("scheduling generate failed for user_id=%s", user_id)
            raise

    def list_suggestions(self, user_id: int) -> list[SessionSuggestionResponse]:
        """Handle suggestion list requests."""
        try:
            suggestions = self.scheduling_service.list_suggestions(user_id)
            response = [SessionSuggestionResponse.model_validate(item) for item in suggestions]
            logger.info("scheduling list handled for user_id=%s count=%s", user_id, len(response))
            return response
        except AppError:
            logger.exception("scheduling list failed for user_id=%s", user_id)
            raise

    def update_suggestion_status(
        self,
        user_id: int,
        suggestion_id: int,
        payload: SuggestionStatusUpdateRequest,
    ) -> SessionSuggestionResponse:
        """Handle suggestion status update requests."""
        try:
            suggestion = self.scheduling_service.update_suggestion_status(
                user_id,
                suggestion_id,
                status=payload.status,
            )
            response = SessionSuggestionResponse.model_validate(suggestion)
            logger.info(
                "scheduling status update handled for user_id=%s suggestion_id=%s",
                user_id,
                suggestion_id,
            )
            return response
        except AppError:
            logger.exception(
                "scheduling status update failed for user_id=%s suggestion_id=%s",
                user_id,
                suggestion_id,
            )
            raise
