"""Scheduling business logic."""

from app.ai.scheduler_engine import SchedulerEngine
from app.core.exceptions import NotFoundError
from app.models.enums import SuggestionStatus
from app.models.session_suggestion import SessionSuggestion
from app.repositories.availability_repo import AvailabilityRepository
from app.repositories.routine_repo import RoutineRepository
from app.repositories.suggestion_repo import SuggestionRepository
from app.repositories.task_repo import TaskRepository
from app.utils.logger import get_logger

logger = get_logger(__name__)


class SchedulingService:
    """Business rules for generating and managing suggestions."""

    def __init__(
        self,
        suggestion_repo: SuggestionRepository,
        scheduler_engine: SchedulerEngine,
        task_repo: TaskRepository,
        availability_repo: AvailabilityRepository,
        routine_repo: RoutineRepository,
    ) -> None:
        self.suggestion_repo = suggestion_repo
        self.scheduler_engine = scheduler_engine
        self.task_repo = task_repo
        self.availability_repo = availability_repo
        self.routine_repo = routine_repo

    def generate_suggestion(
        self,
        *,
        generated_for_user_id: int,
        learner_user_id: int,
        mentor_user_id: int,
        skill_id: int,
        window_start_at: object,
        window_end_at: object,
        minimum_duration_minutes: int,
    ) -> SessionSuggestion:
        """Generate and save one planning-aware session suggestion."""
        learner_tasks = self.task_repo.list_tasks_by_user(learner_user_id)
        mentor_tasks = self.task_repo.list_tasks_by_user(mentor_user_id)
        learner_availability_blocks = self.availability_repo.list_blocks_by_user(learner_user_id)
        mentor_availability_blocks = self.availability_repo.list_blocks_by_user(mentor_user_id)
        learner_routine_blocks = self.routine_repo.list_blocks_by_user(learner_user_id)
        mentor_routine_blocks = self.routine_repo.list_blocks_by_user(mentor_user_id)
        result = self.scheduler_engine.generate(
            learner_user_id=learner_user_id,
            mentor_user_id=mentor_user_id,
            skill_id=skill_id,
            minimum_duration_minutes=minimum_duration_minutes,
            window_start_at=window_start_at,
            window_end_at=window_end_at,
            learner_tasks=learner_tasks,
            mentor_tasks=mentor_tasks,
            learner_availability_blocks=learner_availability_blocks,
            mentor_availability_blocks=mentor_availability_blocks,
            learner_routine_blocks=learner_routine_blocks,
            mentor_routine_blocks=mentor_routine_blocks,
        )
        suggestion = self.suggestion_repo.create_suggestion(
            generated_for_user_id=generated_for_user_id,
            mentor_user_id=mentor_user_id,
            learner_user_id=learner_user_id,
            skill_id=skill_id,
            suggested_start_at=result["suggested_start_at"],
            suggested_end_at=result["suggested_end_at"],
            score=result["score"],
            status=SuggestionStatus.PENDING,
            explanation=result["explanation"],
        )
        logger.info(
            "scheduling generate service completed for user_id=%s suggestion_id=%s",
            generated_for_user_id,
            suggestion.id,
        )
        return suggestion

    def list_suggestions(self, user_id: int) -> list[SessionSuggestion]:
        """Return suggestions generated for the current user."""
        suggestions = self.suggestion_repo.list_suggestions_for_user(user_id)
        logger.info("scheduling list service completed for user_id=%s count=%s", user_id, len(suggestions))
        return suggestions

    def update_suggestion_status(
        self,
        user_id: int,
        suggestion_id: int,
        *,
        status: SuggestionStatus,
    ) -> SessionSuggestion:
        """Update the status of one owned suggestion."""
        suggestion = self.suggestion_repo.get_suggestion_by_id(suggestion_id)
        if suggestion is None or suggestion.generated_for_user_id != user_id:
            logger.error(
                "scheduling status update blocked: suggestion not found for user_id=%s suggestion_id=%s",
                user_id,
                suggestion_id,
            )
            raise NotFoundError("suggestion not found")

        suggestion = self.suggestion_repo.update_suggestion(suggestion, status=status)
        logger.info(
            "scheduling status update service completed for user_id=%s suggestion_id=%s",
            user_id,
            suggestion_id,
        )
        return suggestion
