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
from app.schemas.task import TaskCreateRequest, TaskResponse, TaskUpdateRequest
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

    def createPlanningTask(self, user_id: int, payload: TaskCreateRequest) -> TaskResponse:
        """Handle task creation requests."""
        try:
            ensure_positive_id(user_id, field_name="user_id")
            ensure_optional_id_is_positive(payload.skill_id, field_name="skill_id")

            task = self.planning_service.CreatePlanningTask(
                user_id=user_id,
                title=payload.title,
                description=payload.description,
                priority=payload.priority,
                status=payload.status,
                estimated_minutes=payload.estimated_minutes,
                deadline_at=payload.deadline_at,
                skill_id=payload.skill_id,
            )
            response = TaskResponse.model_validate(task)
            logger.info("task createPlanningTask handled for user_id=%s task_id=%s", user_id, task.id)
            return response
        except AppError:
            logger.exception("task createPlanningTask failed for user_id=%s", user_id)
            raise

    def listPlanningTasks(self, user_id: int) -> list[TaskResponse]:
        """Handle task list requests."""
        try:
            ensure_positive_id(user_id, field_name="user_id")
            tasks = self.planning_service.ListPlanningTasks(user_id)
            response = [TaskResponse.model_validate(task) for task in tasks]
            logger.info("task listPlanningTasks handled for user_id=%s count=%s", user_id, len(response))
            return response
        except AppError:
            logger.exception("task listPlanningTasks failed for user_id=%s", user_id)
            raise

    def updatePlanningTask(self, user_id: int, task_id: int, payload: TaskUpdateRequest) -> TaskResponse:
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

            task = self.planning_service.UpdatePlanningTask(
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
            response = TaskResponse.model_validate(task)
            logger.info("task updatePlanningTask handled for user_id=%s task_id=%s", user_id, task_id)
            return response
        except AppError:
            logger.exception("task updatePlanningTask failed for user_id=%s task_id=%s", user_id, task_id)
            raise

    def deletePlanningTask(self, user_id: int, task_id: int) -> None:
        """Handle task delete requests."""
        try:
            ensure_positive_id(user_id, field_name="user_id")
            ensure_positive_id(task_id, field_name="task_id")
            self.planning_service.DeletePlanningTask(user_id, task_id)
            logger.info("task deletePlanningTask handled for user_id=%s task_id=%s", user_id, task_id)
        except AppError:
            logger.exception("task deletePlanningTask failed for user_id=%s task_id=%s", user_id, task_id)
            raise

    def createAvailabilityBlock(
        self,
        user_id: int,
        payload: AvailabilityBlockCreateRequest,
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
            logger.info("availability createAvailabilityBlock handled for user_id=%s block_id=%s", user_id, block.id)
            return response
        except AppError:
            logger.exception("availability createAvailabilityBlock failed for user_id=%s", user_id)
            raise

    def listAvailabilityBlocks(self, user_id: int) -> list[AvailabilityBlockResponse]:
        """Handle availability block list requests."""
        try:
            ensure_positive_id(user_id, field_name="user_id")
            blocks = self.planning_service.ListAvailabilityBlocks(user_id)
            response = [AvailabilityBlockResponse.model_validate(block) for block in blocks]
            logger.info("availability listAvailabilityBlocks handled for user_id=%s count=%s", user_id, len(response))
            return response
        except AppError:
            logger.exception("availability listAvailabilityBlocks failed for user_id=%s", user_id)
            raise

    def updateAvailabilityBlock(
        self,
        user_id: int,
        block_id: int,
        payload: AvailabilityBlockUpdateRequest,
    ) -> AvailabilityBlockResponse:
        """Handle availability block update requests."""
        try:
            ensure_positive_id(user_id, field_name="user_id")
            ensure_positive_id(block_id, field_name="block_id")
            ensure_payload_has_updates(
                payload,
                field_names=("day_of_week", "start_time", "end_time", "is_recurring", "specific_date"),
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
            logger.info("availability updateAvailabilityBlock handled for user_id=%s block_id=%s", user_id, block_id)
            return response
        except AppError:
            logger.exception("availability updateAvailabilityBlock failed for user_id=%s block_id=%s", user_id, block_id)
            raise

    def deleteAvailabilityBlock(self, user_id: int, block_id: int) -> None:
        """Handle availability block delete requests."""
        try:
            ensure_positive_id(user_id, field_name="user_id")
            ensure_positive_id(block_id, field_name="block_id")
            self.planning_service.DeleteAvailabilityBlock(user_id, block_id)
            logger.info("availability deleteAvailabilityBlock handled for user_id=%s block_id=%s", user_id, block_id)
        except AppError:
            logger.exception("availability deleteAvailabilityBlock failed for user_id=%s block_id=%s", user_id, block_id)
            raise

    def createRoutineBlock(
        self,
        user_id: int,
        payload: RoutineBlockCreateRequest,
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
            logger.info("routine createRoutineBlock handled for user_id=%s block_id=%s", user_id, block.id)
            return response
        except AppError:
            logger.exception("routine createRoutineBlock failed for user_id=%s", user_id)
            raise

    def listRoutineBlocks(self, user_id: int) -> list[RoutineBlockResponse]:
        """Handle routine block list requests."""
        try:
            ensure_positive_id(user_id, field_name="user_id")
            blocks = self.planning_service.ListRoutineBlocks(user_id)
            response = [RoutineBlockResponse.model_validate(block) for block in blocks]
            logger.info("routine listRoutineBlocks handled for user_id=%s count=%s", user_id, len(response))
            return response
        except AppError:
            logger.exception("routine listRoutineBlocks failed for user_id=%s", user_id)
            raise

    def updateRoutineBlock(
        self,
        user_id: int,
        block_id: int,
        payload: RoutineBlockUpdateRequest,
    ) -> RoutineBlockResponse:
        """Handle routine block update requests."""
        try:
            ensure_positive_id(user_id, field_name="user_id")
            ensure_positive_id(block_id, field_name="block_id")
            ensure_payload_has_updates(
                payload,
                field_names=("title", "day_of_week", "start_time", "end_time", "is_recurring", "specific_date"),
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
            logger.info("routine updateRoutineBlock handled for user_id=%s block_id=%s", user_id, block_id)
            return response
        except AppError:
            logger.exception("routine updateRoutineBlock failed for user_id=%s block_id=%s", user_id, block_id)
            raise

    def deleteRoutineBlock(self, user_id: int, block_id: int) -> None:
        """Handle routine block delete requests."""
        try:
            ensure_positive_id(user_id, field_name="user_id")
            ensure_positive_id(block_id, field_name="block_id")
            self.planning_service.DeleteRoutineBlock(user_id, block_id)
            logger.info("routine deleteRoutineBlock handled for user_id=%s block_id=%s", user_id, block_id)
        except AppError:
            logger.exception("routine deleteRoutineBlock failed for user_id=%s block_id=%s", user_id, block_id)
            raise
