"""Planning business logic."""

from app.core.exceptions import NotFoundError
from app.models.availability_block import AvailabilityBlock
from app.models.routine_block import RoutineBlock
from app.models.task import Task
from app.repositories.availability_repo import AvailabilityRepository
from app.repositories.routine_repo import RoutineRepository
from app.repositories.task_repo import TaskRepository
from app.utils.logger import get_logger

logger = get_logger(__name__)


class PlanningService:
    """Business rules for tasks, availability blocks, and routine blocks."""

    def __init__(
        self,
        task_repo: TaskRepository,
        availability_repo: AvailabilityRepository,
        routine_repo: RoutineRepository,
    ) -> None:
        self.task_repo = task_repo
        self.availability_repo = availability_repo
        self.routine_repo = routine_repo

    def CreatePlanningTask(
        self,
        *,
        user_id: int,
        title: str,
        description: str | None,
        priority: str,
        status: str,
        estimated_minutes: int,
        deadline_at: object,
        skill_id: int | None,
    ) -> Task:
        """Create one task owned by the current user."""
        task = self.task_repo.create_task(
            user_id=user_id,
            title=title,
            description=description,
            priority=priority,
            status=status,
            estimated_minutes=estimated_minutes,
            deadline_at=deadline_at,
            skill_id=skill_id,
        )
        logger.info("task create service completed for user_id=%s task_id=%s", user_id, task.id)
        return task

    def ListPlanningTasks(self, user_id: int) -> list[Task]:
        """Return all tasks owned by the current user."""
        tasks = self.task_repo.list_tasks_by_user(user_id)
        logger.info("task list service completed for user_id=%s count=%s", user_id, len(tasks))
        return tasks

    def UpdatePlanningTask(self, user_id: int, task_id: int, **updates: object) -> Task:
        """Update one owned task."""
        task = self.task_repo.get_task_by_id(task_id)
        if task is None or task.user_id != user_id:
            logger.error("task update blocked: task not found for user_id=%s task_id=%s", user_id, task_id)
            raise NotFoundError("task not found")

        filtered_updates = {field: value for field, value in updates.items() if value is not None}
        if filtered_updates:
            task = self.task_repo.update_task(task, **filtered_updates)

        logger.info("task update service completed for user_id=%s task_id=%s", user_id, task_id)
        return task

    def DeletePlanningTask(self, user_id: int, task_id: int) -> None:
        """Delete one owned task."""
        task = self.task_repo.get_task_by_id(task_id)
        if task is None or task.user_id != user_id:
            logger.error("task delete blocked: task not found for user_id=%s task_id=%s", user_id, task_id)
            raise NotFoundError("task not found")

        self.task_repo.delete_task(task)
        logger.info("task delete service completed for user_id=%s task_id=%s", user_id, task_id)

    def CreateAvailabilityBlock(
        self,
        *,
        user_id: int,
        day_of_week: int | None,
        start_time: object,
        end_time: object,
        is_recurring: bool,
        specific_date: object,
    ) -> AvailabilityBlock:
        """Create one availability block owned by the current user."""
        block = self.availability_repo.create_block(
            user_id=user_id,
            day_of_week=day_of_week,
            start_time=start_time,
            end_time=end_time,
            is_recurring=is_recurring,
            specific_date=specific_date,
        )
        logger.info(
            "availability create service completed for user_id=%s block_id=%s",
            user_id,
            block.id,
        )
        return block

    def ListAvailabilityBlocks(self, user_id: int) -> list[AvailabilityBlock]:
        """Return all availability blocks owned by the current user."""
        blocks = self.availability_repo.list_blocks_by_user(user_id)
        logger.info(
            "availability list service completed for user_id=%s count=%s",
            user_id,
            len(blocks),
        )
        return blocks

    def UpdateAvailabilityBlock(self, user_id: int, block_id: int, **updates: object) -> AvailabilityBlock:
        """Update one owned availability block."""
        block = self.availability_repo.get_block_by_id(block_id)
        if block is None or block.user_id != user_id:
            logger.error(
                "availability update blocked: block not found for user_id=%s block_id=%s",
                user_id,
                block_id,
            )
            raise NotFoundError("availability block not found")

        filtered_updates = {field: value for field, value in updates.items() if value is not None}
        if filtered_updates:
            block = self.availability_repo.update_block(block, **filtered_updates)

        logger.info(
            "availability update service completed for user_id=%s block_id=%s",
            user_id,
            block_id,
        )
        return block

    def DeleteAvailabilityBlock(self, user_id: int, block_id: int) -> None:
        """Delete one owned availability block."""
        block = self.availability_repo.get_block_by_id(block_id)
        if block is None or block.user_id != user_id:
            logger.error(
                "availability delete blocked: block not found for user_id=%s block_id=%s",
                user_id,
                block_id,
            )
            raise NotFoundError("availability block not found")

        self.availability_repo.delete_block(block)
        logger.info(
            "availability delete service completed for user_id=%s block_id=%s",
            user_id,
            block_id,
        )

    def CreateRoutineBlock(
        self,
        *,
        user_id: int,
        title: str,
        day_of_week: int | None,
        start_time: object,
        end_time: object,
        is_recurring: bool,
        specific_date: object,
    ) -> RoutineBlock:
        """Create one routine block owned by the current user."""
        block = self.routine_repo.create_block(
            user_id=user_id,
            title=title,
            day_of_week=day_of_week,
            start_time=start_time,
            end_time=end_time,
            is_recurring=is_recurring,
            specific_date=specific_date,
        )
        logger.info("routine create service completed for user_id=%s block_id=%s", user_id, block.id)
        return block

    def ListRoutineBlocks(self, user_id: int) -> list[RoutineBlock]:
        """Return all routine blocks owned by the current user."""
        blocks = self.routine_repo.list_blocks_by_user(user_id)
        logger.info("routine list service completed for user_id=%s count=%s", user_id, len(blocks))
        return blocks

    def UpdateRoutineBlock(self, user_id: int, block_id: int, **updates: object) -> RoutineBlock:
        """Update one owned routine block."""
        block = self.routine_repo.get_block_by_id(block_id)
        if block is None or block.user_id != user_id:
            logger.error(
                "routine update blocked: block not found for user_id=%s block_id=%s",
                user_id,
                block_id,
            )
            raise NotFoundError("routine block not found")

        filtered_updates = {field: value for field, value in updates.items() if value is not None}
        if filtered_updates:
            block = self.routine_repo.update_block(block, **filtered_updates)

        logger.info("routine update service completed for user_id=%s block_id=%s", user_id, block_id)
        return block

    def DeleteRoutineBlock(self, user_id: int, block_id: int) -> None:
        """Delete one owned routine block."""
        block = self.routine_repo.get_block_by_id(block_id)
        if block is None or block.user_id != user_id:
            logger.error(
                "routine delete blocked: block not found for user_id=%s block_id=%s",
                user_id,
                block_id,
            )
            raise NotFoundError("routine block not found")

        self.routine_repo.delete_block(block)
        logger.info("routine delete service completed for user_id=%s block_id=%s", user_id, block_id)
