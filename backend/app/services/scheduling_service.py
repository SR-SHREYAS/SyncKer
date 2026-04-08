"""Scheduling business logic."""

from datetime import datetime

from app.ai.scheduler_engine import SchedulerEngine
from app.core.exceptions import ConflictError, NotFoundError
from app.models.enums import SuggestionStatus, TaskPriority, TaskStatus
from app.models.session_suggestion import SessionSuggestion
from app.repositories.availability_repo import AvailabilityRepository
from app.repositories.routine_repo import RoutineRepository
from app.repositories.skill_repo import SkillRepository
from app.repositories.suggestion_repo import SuggestionRepository
from app.repositories.task_repo import TaskRepository
from app.services.team_service import TeamService
from app.utils.logger import get_logger
from sqlalchemy.exc import IntegrityError

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
        skill_repo: SkillRepository,
        team_service: TeamService,
    ) -> None:
        self.suggestion_repo = suggestion_repo
        self.scheduler_engine = scheduler_engine
        self.task_repo = task_repo
        self.availability_repo = availability_repo
        self.routine_repo = routine_repo
        self.skill_repo = skill_repo
        self.team_service = team_service

    def GenerateSchedulingSuggestion(
        self,
        *,
        team_id: int,
        generated_for_user_id: int,
        participant_user_ids: list[int],
        collaboration_title: str,
        skill_id: int | None,
        window_start_at: object,
        window_end_at: object,
        minimum_duration_minutes: int,
    ) -> SessionSuggestion:
        """Generate and save one planning-aware session suggestion."""
        self._ensure_participants_are_in_team(
            team_id=team_id,
            generated_for_user_id=generated_for_user_id,
            participant_user_ids=participant_user_ids,
        )
        resolved_skill_id = self._resolve_skill_id(skill_id)
        tasks: list[object] = []
        availability_blocks: list[object] = []
        routine_blocks: list[object] = []
        for participant_user_id in participant_user_ids:
            tasks.extend(self.task_repo.list_tasks_by_user(participant_user_id))
            availability_blocks.extend(
                self.availability_repo.list_blocks_by_user(participant_user_id)
            )
            routine_blocks.extend(
                self.routine_repo.list_blocks_by_user(participant_user_id)
            )

        scheduling_candidate = self.scheduler_engine.generate(
            participant_user_ids=participant_user_ids,
            skill_id=resolved_skill_id,
            minimum_duration_minutes=minimum_duration_minutes,
            window_start_at=window_start_at,
            window_end_at=window_end_at,
            tasks=tasks,
            availability_blocks=availability_blocks,
            routine_blocks=routine_blocks,
        )

        participant_one_user_id = participant_user_ids[0]
        participant_two_user_id = participant_user_ids[1]
        suggestion = self.suggestion_repo.create_suggestion(
            team_id=team_id,
            generated_for_user_id=generated_for_user_id,
            mentor_user_id=participant_one_user_id,
            learner_user_id=participant_two_user_id,
            participant_user_ids=participant_user_ids,
            collaboration_title=collaboration_title,
            skill_id=resolved_skill_id,
            suggested_start_at=scheduling_candidate["suggested_start_at"],
            suggested_end_at=scheduling_candidate["suggested_end_at"],
            score=scheduling_candidate["score"],
            status=SuggestionStatus.PENDING,
            explanation=scheduling_candidate["explanation"],
        )
        logger.info("scheduling generate service completed")
        return suggestion

    def _ensure_participants_are_in_team(
        self,
        *,
        team_id: int,
        generated_for_user_id: int,
        participant_user_ids: list[int],
    ) -> None:
        """Ensure scheduling request uses one real team and valid members."""
        self.team_service.AssertUserBelongsToTeam(
            team_id=team_id, user_id=generated_for_user_id
        )
        self.team_service.AssertParticipantsBelongToTeam(
            team_id=team_id,
            participant_user_ids=participant_user_ids,
        )

    def ListSchedulingSuggestions(self, user_id: int) -> list[SessionSuggestion]:
        """Return suggestions generated for the current user."""
        suggestions = self.suggestion_repo.list_suggestions_for_user(user_id)
        logger.info("scheduling list service completed")
        return suggestions

    def UpdateSchedulingSuggestionStatus(
        self, user_id: int, suggestion_id: int, *, status: SuggestionStatus
    ) -> SessionSuggestion:
        """Update the status of one owned suggestion."""
        suggestion = self.suggestion_repo.get_suggestion_by_id(suggestion_id)
        if suggestion is None or suggestion.generated_for_user_id != user_id:
            logger.error("scheduling status update blocked: suggestion not found")
            raise NotFoundError("suggestion not found")

        suggestion = self.suggestion_repo.update_suggestion(suggestion, status=status)
        logger.info("scheduling status update service completed")
        return suggestion

    def ApplySchedulingSuggestionToTimetable(
        self, user_id: int, suggestion_id: int
    ) -> SessionSuggestion:
        """Apply one pending suggestion by writing collaboration tasks."""
        suggestion = self.suggestion_repo.get_suggestion_by_id(suggestion_id)
        if suggestion is None or suggestion.generated_for_user_id != user_id:
            logger.error("scheduling apply blocked: suggestion not found")
            raise NotFoundError("suggestion not found")

        if suggestion.status == SuggestionStatus.ACCEPTED:
            logger.info("scheduling apply service completed")
            return suggestion

        if suggestion.status != SuggestionStatus.PENDING:
            logger.error("scheduling apply blocked: suggestion is not pending")
            raise ConflictError("only pending suggestions can be applied")

        if suggestion.team_id is not None:
            self._ensure_participants_are_in_team(
                team_id=suggestion.team_id,
                generated_for_user_id=user_id,
                participant_user_ids=suggestion.participant_user_ids,
            )

        for participant_user_id in suggestion.participant_user_ids:
            participant_tasks = self.task_repo.list_tasks_by_user(participant_user_id)
            has_conflict = self._has_planned_time_conflict(
                existing_tasks=participant_tasks,
                planned_start_at=suggestion.suggested_start_at,
                planned_end_at=suggestion.suggested_end_at,
            )
            if has_conflict:
                logger.error("scheduling apply blocked: participant timetable conflict")
                raise ConflictError(
                    "cannot apply suggestion: one or more participant timetable slots conflict"
                )

        collaboration_minutes = max(
            int(
                (
                    suggestion.suggested_end_at - suggestion.suggested_start_at
                ).total_seconds()
                // 60
            ),
            15,
        )
        for participant_user_id in suggestion.participant_user_ids:
            self.task_repo.create_task(
                user_id=participant_user_id,
                title=suggestion.collaboration_title,
                description="Auto-created collaboration block from accepted suggestion.",
                priority=TaskPriority.HIGH,
                status=TaskStatus.PENDING,
                estimated_minutes=collaboration_minutes,
                deadline_at=None,
                planned_start_at=suggestion.suggested_start_at,
                planned_end_at=suggestion.suggested_end_at,
                skill_id=suggestion.skill_id,
            )

        suggestion = self.suggestion_repo.update_suggestion(
            suggestion, status=SuggestionStatus.ACCEPTED
        )
        logger.info("scheduling apply service completed")
        return suggestion

    def _resolve_skill_id(self, skill_id: int | None) -> int:
        """Resolve a valid skill id while keeping skill optional for workflow."""
        if skill_id is not None:
            skill = self.skill_repo.get_skill_by_id(skill_id)
            if skill is None:
                raise NotFoundError("skill not found")
            return skill.id

        default_slug = "general-collaboration"
        existing_default = self.skill_repo.get_skill_by_slug(default_slug)
        if existing_default is not None:
            return existing_default.id

        try:
            created_default = self.skill_repo.create_skill(
                name="General Collaboration",
                slug=default_slug,
                description="Auto-created default category for collaboration scheduling.",
            )
            return created_default.id
        except IntegrityError:
            self.skill_repo.db.rollback()
            existing_after_race = self.skill_repo.get_skill_by_slug(default_slug)
            if existing_after_race is not None:
                return existing_after_race.id
            raise

    def _has_planned_time_conflict(
        self,
        *,
        existing_tasks: list[object],
        planned_start_at: datetime,
        planned_end_at: datetime,
    ) -> bool:
        """Return True when an existing planned block overlaps requested slot."""
        for task in existing_tasks:
            existing_start_at = getattr(task, "planned_start_at", None)
            existing_end_at = getattr(task, "planned_end_at", None)
            if existing_start_at is None or existing_end_at is None:
                continue

            overlaps = (
                planned_start_at < existing_end_at
                and existing_start_at < planned_end_at
            )
            if overlaps:
                return True
        return False
