"""Planning request handlers."""

from app.core.exceptions import AppError
from app.schemas.availability import (
    AvailabilityBlockCreateRequest,
    AvailabilityBlockResponse,
    AvailabilityBlockUpdateRequest,
)
from app.schemas.routine import (
    RoutineBlockCreateRequest,
    RoutineBlockResponse,
    RoutineBlockUpdateRequest,
)
from app.schemas.task import (
    TaskCreateRequest,
    TaskResponse,
    TaskUpdateRequest,
    TeamTimetableParticipantResponse,
    TeamTimetableResponse,
)
from app.services.planning_service import PlanningService
from app.utils.logger import get_logger
from app.utils.request_validation import (
    ensure_optional_id_is_positive,
    ensure_payload_has_updates,
    ensure_positive_id,
    ensure_time_range,
)

logger = get_logger(__name__)


class PlanningHandler:
    """Maps planning requests to planning service calls."""

    def __init__(self, planning_service: PlanningService) -> None:
        self.planning_service = planning_service

    def createPlanningTask(
        self, user_id: int, payload: TaskCreateRequest
    ) -> TaskResponse:
        """Handle task creation requests."""
        try:
            ensure_positive_id(user_id, field_name="user_id")
            ensure_optional_id_is_positive(payload.skill_id, field_name="skill_id")

            created_task = self.planning_service.CreatePlanningTask(
                user_id=user_id,
                title=payload.title,
                description=payload.description,
                priority=payload.priority,
                status=payload.status,
                estimated_minutes=payload.estimated_minutes,
                deadline_at=payload.deadline_at,
                skill_id=payload.skill_id,
            )
            task_response = TaskResponse.model_validate(created_task)
            logger.info("task create handler completed")
            return task_response
        except AppError:
            logger.exception("task create handler failed")
            raise

    def listPlanningTasks(self, user_id: int) -> list[TaskResponse]:
        """Handle task list requests."""
        try:
            ensure_positive_id(user_id, field_name="user_id")
            tasks = self.planning_service.ListPlanningTasks(user_id)
            response = [TaskResponse.model_validate(task) for task in tasks]
            logger.info("task list handler completed")
            return response
        except AppError:
            logger.exception("task list handler failed")
            raise

    def updatePlanningTask(
        self, user_id: int, task_id: int, payload: TaskUpdateRequest
    ) -> TaskResponse:
        """Handle task update requests."""
        try:
            ensure_positive_id(user_id, field_name="user_id")
            ensure_positive_id(task_id, field_name="task_id")
            ensure_payload_has_updates(
                payload,
                field_names=(
                    "title",
                    "description",
                    "priority",
                    "status",
                    "estimated_minutes",
                    "deadline_at",
                    "skill_id",
                ),
            )
            ensure_optional_id_is_positive(payload.skill_id, field_name="skill_id")

            updated_task = self.planning_service.UpdatePlanningTask(
                user_id,
                task_id,
                title=payload.title,
                description=payload.description,
                priority=payload.priority,
                status=payload.status,
                estimated_minutes=payload.estimated_minutes,
                deadline_at=payload.deadline_at,
                skill_id=payload.skill_id,
            )
            task_response = TaskResponse.model_validate(updated_task)
            logger.info("task update handler completed")
            return task_response
        except AppError:
            logger.exception("task update handler failed")
            raise

    def deletePlanningTask(self, user_id: int, task_id: int) -> None:
        """Handle task delete requests."""
        try:
            ensure_positive_id(user_id, field_name="user_id")
            ensure_positive_id(task_id, field_name="task_id")
            self.planning_service.DeletePlanningTask(user_id, task_id)
            logger.info("task delete handler completed")
        except AppError:
            logger.exception("task delete handler failed")
            raise

    def listTeamTimetable(
        self, current_user_id: int, team_id: int
    ) -> TeamTimetableResponse:
        """Handle team timetable read requests."""
        try:
            # Validate request input.
            ensure_positive_id(current_user_id, field_name="current_user_id")
            ensure_positive_id(team_id, field_name="team_id")

            # Call service layer.
            participant_rows = self.planning_service.ListTeamTimetable(
                current_user_id=current_user_id, team_id=team_id
            )

            # Build response model.
            participants = [
                TeamTimetableParticipantResponse(
                    user_id=participant_row.user_id,
                    username=participant_row.username,
                    email=participant_row.email,
                    tasks=[
                        TaskResponse.model_validate(task)
                        for task in participant_row.tasks
                    ],
                )
                for participant_row in participant_rows
            ]
            team_timetable_response = TeamTimetableResponse(
                team_id=team_id, participants=participants
            )
            logger.info("team timetable list handler completed")
            return team_timetable_response
        except AppError:
            logger.exception("team timetable list handler failed")
            raise

    def createAvailabilityBlock(
        self, user_id: int, payload: AvailabilityBlockCreateRequest
    ) -> AvailabilityBlockResponse:
        """Handle availability block creation requests."""
        try:
            ensure_positive_id(user_id, field_name="user_id")

            block = self.planning_service.CreateAvailabilityBlock(
                user_id=user_id,
                day_of_week=payload.day_of_week,
                start_time=payload.start_time,
                end_time=payload.end_time,
                is_recurring=payload.is_recurring,
                specific_date=payload.specific_date,
            )
            response = AvailabilityBlockResponse.model_validate(block)
            logger.info("availability create handler completed")
            return response
        except AppError:
            logger.exception("availability create handler failed")
            raise

    def listAvailabilityBlocks(self, user_id: int) -> list[AvailabilityBlockResponse]:
        """Handle availability block list requests."""
        try:
            ensure_positive_id(user_id, field_name="user_id")
            blocks = self.planning_service.ListAvailabilityBlocks(user_id)
            response = [
                AvailabilityBlockResponse.model_validate(block) for block in blocks
            ]
            logger.info("availability list handler completed")
            return response
        except AppError:
            logger.exception("availability list handler failed")
            raise

    def updateAvailabilityBlock(
        self, user_id: int, block_id: int, payload: AvailabilityBlockUpdateRequest
    ) -> AvailabilityBlockResponse:
        """Handle availability block update requests."""
        try:
            ensure_positive_id(user_id, field_name="user_id")
            ensure_positive_id(block_id, field_name="block_id")
            ensure_payload_has_updates(
                payload,
                field_names=(
                    "day_of_week",
                    "start_time",
                    "end_time",
                    "is_recurring",
                    "specific_date",
                ),
            )
            ensure_time_range(
                start_time=payload.start_time,
                end_time=payload.end_time,
                context="availability block",
            )

            block = self.planning_service.UpdateAvailabilityBlock(
                user_id,
                block_id,
                day_of_week=payload.day_of_week,
                start_time=payload.start_time,
                end_time=payload.end_time,
                is_recurring=payload.is_recurring,
                specific_date=payload.specific_date,
            )
            response = AvailabilityBlockResponse.model_validate(block)
            logger.info("availability update handler completed")
            return response
        except AppError:
            logger.exception("availability update handler failed")
            raise

    def deleteAvailabilityBlock(self, user_id: int, block_id: int) -> None:
        """Handle availability block delete requests."""
        try:
            ensure_positive_id(user_id, field_name="user_id")
            ensure_positive_id(block_id, field_name="block_id")
            self.planning_service.DeleteAvailabilityBlock(user_id, block_id)
            logger.info("availability delete handler completed")
        except AppError:
            logger.exception("availability delete handler failed")
            raise

    def createRoutineBlock(
        self, user_id: int, payload: RoutineBlockCreateRequest
    ) -> RoutineBlockResponse:
        """Handle routine block creation requests."""
        try:
            ensure_positive_id(user_id, field_name="user_id")
            block = self.planning_service.CreateRoutineBlock(
                user_id=user_id,
                title=payload.title,
                day_of_week=payload.day_of_week,
                start_time=payload.start_time,
                end_time=payload.end_time,
                is_recurring=payload.is_recurring,
                specific_date=payload.specific_date,
            )
            response = RoutineBlockResponse.model_validate(block)
            logger.info("routine create handler completed")
            return response
        except AppError:
            logger.exception("routine create handler failed")
            raise

    def listRoutineBlocks(self, user_id: int) -> list[RoutineBlockResponse]:
        """Handle routine block list requests."""
        try:
            ensure_positive_id(user_id, field_name="user_id")
            blocks = self.planning_service.ListRoutineBlocks(user_id)
            response = [RoutineBlockResponse.model_validate(block) for block in blocks]
            logger.info("routine list handler completed")
            return response
        except AppError:
            logger.exception("routine list handler failed")
            raise

    def updateRoutineBlock(
        self, user_id: int, block_id: int, payload: RoutineBlockUpdateRequest
    ) -> RoutineBlockResponse:
        """Handle routine block update requests."""
        try:
            ensure_positive_id(user_id, field_name="user_id")
            ensure_positive_id(block_id, field_name="block_id")
            ensure_payload_has_updates(
                payload,
                field_names=(
                    "title",
                    "day_of_week",
                    "start_time",
                    "end_time",
                    "is_recurring",
                    "specific_date",
                ),
            )
            ensure_time_range(
                start_time=payload.start_time,
                end_time=payload.end_time,
                context="routine block",
            )

            block = self.planning_service.UpdateRoutineBlock(
                user_id,
                block_id,
                title=payload.title,
                day_of_week=payload.day_of_week,
                start_time=payload.start_time,
                end_time=payload.end_time,
                is_recurring=payload.is_recurring,
                specific_date=payload.specific_date,
            )
            response = RoutineBlockResponse.model_validate(block)
            logger.info("routine update handler completed")
            return response
        except AppError:
            logger.exception("routine update handler failed")
            raise

    def deleteRoutineBlock(self, user_id: int, block_id: int) -> None:
        """Handle routine block delete requests."""
        try:
            ensure_positive_id(user_id, field_name="user_id")
            ensure_positive_id(block_id, field_name="block_id")
            self.planning_service.DeleteRoutineBlock(user_id, block_id)
            logger.info("routine delete handler completed")
        except AppError:
            logger.exception("routine delete handler failed")
            raise
