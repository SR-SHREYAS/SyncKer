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

logger = get_logger(__name__)


class PlanningHandler:
    """Maps planning requests to planning service calls."""

    def __init__(self, planning_service: PlanningService) -> None:
        self.planning_service = planning_service

    def create_task(self, user_id: int, payload: TaskCreateRequest) -> TaskResponse:
        """Handle task creation requests."""
        try:
            task = self.planning_service.create_task(
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
            logger.info("task create handled for user_id=%s task_id=%s", user_id, task.id)
            return response
        except AppError:
            logger.exception("task create failed for user_id=%s", user_id)
            raise

    def list_tasks(self, user_id: int) -> list[TaskResponse]:
        """Handle task list requests."""
        try:
            tasks = self.planning_service.list_tasks(user_id)
            response = [TaskResponse.model_validate(task) for task in tasks]
            logger.info("task list handled for user_id=%s count=%s", user_id, len(response))
            return response
        except AppError:
            logger.exception("task list failed for user_id=%s", user_id)
            raise

    def update_task(self, user_id: int, task_id: int, payload: TaskUpdateRequest) -> TaskResponse:
        """Handle task update requests."""
        try:
            task = self.planning_service.update_task(
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
            logger.info("task update handled for user_id=%s task_id=%s", user_id, task_id)
            return response
        except AppError:
            logger.exception("task update failed for user_id=%s task_id=%s", user_id, task_id)
            raise

    def delete_task(self, user_id: int, task_id: int) -> None:
        """Handle task delete requests."""
        try:
            self.planning_service.delete_task(user_id, task_id)
            logger.info("task delete handled for user_id=%s task_id=%s", user_id, task_id)
        except AppError:
            logger.exception("task delete failed for user_id=%s task_id=%s", user_id, task_id)
            raise

    def create_availability_block(
        self,
        user_id: int,
        payload: AvailabilityBlockCreateRequest,
    ) -> AvailabilityBlockResponse:
        """Handle availability block creation requests."""
        try:
            block = self.planning_service.create_availability_block(
                user_id=user_id,
                day_of_week=payload.day_of_week,
                start_time=payload.start_time,
                end_time=payload.end_time,
                is_recurring=payload.is_recurring,
                specific_date=payload.specific_date,
            )
            response = AvailabilityBlockResponse.model_validate(block)
            logger.info("availability create handled for user_id=%s block_id=%s", user_id, block.id)
            return response
        except AppError:
            logger.exception("availability create failed for user_id=%s", user_id)
            raise

    def list_availability_blocks(self, user_id: int) -> list[AvailabilityBlockResponse]:
        """Handle availability block list requests."""
        try:
            blocks = self.planning_service.list_availability_blocks(user_id)
            response = [AvailabilityBlockResponse.model_validate(block) for block in blocks]
            logger.info("availability list handled for user_id=%s count=%s", user_id, len(response))
            return response
        except AppError:
            logger.exception("availability list failed for user_id=%s", user_id)
            raise

    def update_availability_block(
        self,
        user_id: int,
        block_id: int,
        payload: AvailabilityBlockUpdateRequest,
    ) -> AvailabilityBlockResponse:
        """Handle availability block update requests."""
        try:
            block = self.planning_service.update_availability_block(
                user_id,
                block_id,
                day_of_week=payload.day_of_week,
                start_time=payload.start_time,
                end_time=payload.end_time,
                is_recurring=payload.is_recurring,
                specific_date=payload.specific_date,
            )
            response = AvailabilityBlockResponse.model_validate(block)
            logger.info("availability update handled for user_id=%s block_id=%s", user_id, block_id)
            return response
        except AppError:
            logger.exception("availability update failed for user_id=%s block_id=%s", user_id, block_id)
            raise

    def delete_availability_block(self, user_id: int, block_id: int) -> None:
        """Handle availability block delete requests."""
        try:
            self.planning_service.delete_availability_block(user_id, block_id)
            logger.info("availability delete handled for user_id=%s block_id=%s", user_id, block_id)
        except AppError:
            logger.exception("availability delete failed for user_id=%s block_id=%s", user_id, block_id)
            raise

    def create_routine_block(
        self,
        user_id: int,
        payload: RoutineBlockCreateRequest,
    ) -> RoutineBlockResponse:
        """Handle routine block creation requests."""
        try:
            block = self.planning_service.create_routine_block(
                user_id=user_id,
                title=payload.title,
                day_of_week=payload.day_of_week,
                start_time=payload.start_time,
                end_time=payload.end_time,
                is_recurring=payload.is_recurring,
                specific_date=payload.specific_date,
            )
            response = RoutineBlockResponse.model_validate(block)
            logger.info("routine create handled for user_id=%s block_id=%s", user_id, block.id)
            return response
        except AppError:
            logger.exception("routine create failed for user_id=%s", user_id)
            raise

    def list_routine_blocks(self, user_id: int) -> list[RoutineBlockResponse]:
        """Handle routine block list requests."""
        try:
            blocks = self.planning_service.list_routine_blocks(user_id)
            response = [RoutineBlockResponse.model_validate(block) for block in blocks]
            logger.info("routine list handled for user_id=%s count=%s", user_id, len(response))
            return response
        except AppError:
            logger.exception("routine list failed for user_id=%s", user_id)
            raise

    def update_routine_block(
        self,
        user_id: int,
        block_id: int,
        payload: RoutineBlockUpdateRequest,
    ) -> RoutineBlockResponse:
        """Handle routine block update requests."""
        try:
            block = self.planning_service.update_routine_block(
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
            logger.info("routine update handled for user_id=%s block_id=%s", user_id, block_id)
            return response
        except AppError:
            logger.exception("routine update failed for user_id=%s block_id=%s", user_id, block_id)
            raise

    def delete_routine_block(self, user_id: int, block_id: int) -> None:
        """Handle routine block delete requests."""
        try:
            self.planning_service.delete_routine_block(user_id, block_id)
            logger.info("routine delete handled for user_id=%s block_id=%s", user_id, block_id)
        except AppError:
            logger.exception("routine delete failed for user_id=%s block_id=%s", user_id, block_id)
            raise
