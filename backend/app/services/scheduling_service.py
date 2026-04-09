"""Scheduling business logic."""

from datetime import datetime, timedelta

from app.ai.scheduler_engine import SchedulerEngine
from app.core.exceptions import ConflictError, NotFoundError
from app.models.enums import SuggestionStatus, TaskPriority, TaskStatus
from app.models.session_suggestion import SessionSuggestion
from app.models.task import Task
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

    SHIFT_HORIZON_HOURS = 12

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
        tasks: list[Task] = []
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
        with self._get_shared_db_session().begin():
            suggestion = self.suggestion_repo.get_suggestion_by_id_for_update(
                suggestion_id
            )
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
                planned_tasks = self.task_repo.list_planned_tasks_by_user(
                    user_id=participant_user_id,
                    for_update=True,
                )
                planned_task_updates = self._plan_shifted_tasks_for_suggestion(
                    participant_user_id=participant_user_id,
                    participant_tasks=planned_tasks,
                    suggested_start_at=suggestion.suggested_start_at,
                    suggested_end_at=suggestion.suggested_end_at,
                )
                for task, shifted_start_at, shifted_end_at in planned_task_updates:
                    self.task_repo.update_task(
                        task,
                        planned_start_at=shifted_start_at,
                        planned_end_at=shifted_end_at,
                        auto_commit=False,
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
                    auto_commit=False,
                )

            suggestion = self.suggestion_repo.update_suggestion(
                suggestion,
                status=SuggestionStatus.ACCEPTED,
                auto_commit=False,
            )

        logger.info("scheduling apply service completed")
        return suggestion

    def _get_shared_db_session(self):
        """Return one shared DB session for repositories in this unit of work."""
        suggestion_db_session = getattr(self.suggestion_repo, "db", None)
        task_db_session = getattr(self.task_repo, "db", None)
        if suggestion_db_session is None or task_db_session is None:
            raise RuntimeError(
                "scheduling service requires repositories with db session access"
            )
        if suggestion_db_session is not task_db_session:
            raise RuntimeError(
                "scheduling service requires suggestion and task repositories to share one db session"
            )
        return suggestion_db_session

    def _plan_shifted_tasks_for_suggestion(
        self,
        *,
        participant_user_id: int,
        participant_tasks: list[Task],
        suggested_start_at: datetime,
        suggested_end_at: datetime,
    ) -> list[tuple[Task, datetime, datetime]]:
        """Plan task shifts for one participant before inserting collaboration block."""
        occupied_intervals = [(suggested_start_at, suggested_end_at)]
        movable_tasks: list[Task] = []
        for participant_task in participant_tasks:
            planned_start_at = participant_task.planned_start_at
            planned_end_at = participant_task.planned_end_at
            if planned_start_at is None or planned_end_at is None:
                continue
            if planned_end_at <= planned_start_at:
                continue

            if self._is_protected_task(participant_task):
                if self._intervals_overlap(
                    first_start=suggested_start_at,
                    first_end=suggested_end_at,
                    second_start=planned_start_at,
                    second_end=planned_end_at,
                ):
                    logger.error(
                        "scheduling apply blocked: protected participant task overlaps "
                        "participant_user_id=%s task_id=%s task_start=%s task_end=%s suggestion_start=%s suggestion_end=%s",
                        participant_user_id,
                        participant_task.id,
                        planned_start_at,
                        planned_end_at,
                        suggested_start_at,
                        suggested_end_at,
                    )
                    raise ConflictError(
                        "cannot apply suggestion: protected tasks block requested slot"
                    )
                occupied_intervals.append((planned_start_at, planned_end_at))
                continue

            movable_tasks.append(participant_task)

        merged_intervals = self._merge_intervals(occupied_intervals)
        shift_horizon_end = suggested_end_at + timedelta(hours=self.SHIFT_HORIZON_HOURS)
        planned_updates: list[tuple[Task, datetime, datetime]] = []
        for movable_task in movable_tasks:
            original_start_at = movable_task.planned_start_at
            original_end_at = movable_task.planned_end_at
            if original_start_at is None or original_end_at is None:
                continue

            task_duration = original_end_at - original_start_at
            shifted_start_at = self._find_next_available_start(
                candidate_start=original_start_at,
                duration=task_duration,
                occupied_intervals=merged_intervals,
                horizon_end=shift_horizon_end,
            )
            if shifted_start_at is None:
                logger.error(
                    "scheduling apply blocked: no feasible shifted slot "
                    "participant_user_id=%s task_id=%s task_start=%s task_end=%s suggestion_start=%s suggestion_end=%s horizon_end=%s",
                    participant_user_id,
                    movable_task.id,
                    original_start_at,
                    original_end_at,
                    suggested_start_at,
                    suggested_end_at,
                    shift_horizon_end,
                )
                raise ConflictError(
                    "cannot apply suggestion: no feasible slot after shifting lower-priority tasks"
                )

            shifted_end_at = shifted_start_at + task_duration
            merged_intervals = self._merge_intervals(
                [*merged_intervals, (shifted_start_at, shifted_end_at)]
            )
            if (
                shifted_start_at != original_start_at
                or shifted_end_at != original_end_at
            ):
                planned_updates.append((movable_task, shifted_start_at, shifted_end_at))

        return planned_updates

    def _is_protected_task(self, task: Task) -> bool:
        """Return True when task priority should not be shifted by scheduler."""
        task_priority = self._normalize_task_priority(task.priority)
        return task_priority == TaskPriority.HIGH

    def _normalize_task_priority(self, task_priority: object) -> TaskPriority | None:
        """Normalize enum or raw text priority into TaskPriority enum."""
        if isinstance(task_priority, TaskPriority):
            return task_priority
        if isinstance(task_priority, str):
            normalized_priority = task_priority.strip().lower()
            if normalized_priority in {"low", "medium", "high"}:
                return TaskPriority(normalized_priority)
        return None

    def _merge_intervals(
        self,
        intervals: list[tuple[datetime, datetime]],
    ) -> list[tuple[datetime, datetime]]:
        """Merge overlapping intervals to simplify availability checks."""
        if not intervals:
            return []
        sorted_intervals = sorted(intervals, key=lambda item: item[0])
        merged_intervals: list[tuple[datetime, datetime]] = [sorted_intervals[0]]
        for next_start_at, next_end_at in sorted_intervals[1:]:
            current_start_at, current_end_at = merged_intervals[-1]
            if next_start_at <= current_end_at:
                merged_intervals[-1] = (
                    current_start_at,
                    max(current_end_at, next_end_at),
                )
            else:
                merged_intervals.append((next_start_at, next_end_at))
        return merged_intervals

    def _find_next_available_start(
        self,
        *,
        candidate_start: datetime,
        duration: timedelta,
        occupied_intervals: list[tuple[datetime, datetime]],
        horizon_end: datetime,
    ) -> datetime | None:
        """Return earliest non-overlapping start >= candidate_start within horizon."""
        resolved_start = candidate_start
        for occupied_start, occupied_end in occupied_intervals:
            resolved_end = resolved_start + duration
            if resolved_end <= occupied_start:
                break
            if resolved_start >= occupied_end:
                continue
            resolved_start = occupied_end

        if (
            resolved_start != candidate_start
            and resolved_start + duration > horizon_end
        ):
            return None
        return resolved_start

    def _intervals_overlap(
        self,
        *,
        first_start: datetime,
        first_end: datetime,
        second_start: datetime,
        second_end: datetime,
    ) -> bool:
        """Return True when two intervals overlap."""
        return first_start < second_end and second_start < first_end

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
