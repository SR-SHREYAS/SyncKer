"""Task persistence queries."""

from datetime import datetime

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.models.task import Task


class TaskRepository:
    """Database access for task records."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create_task(
        self,
        *,
        user_id: int,
        title: str,
        description: str | None,
        priority: str,
        status: str,
        estimated_minutes: int,
        deadline_at: datetime | None,
        planned_start_at: datetime | None,
        planned_end_at: datetime | None,
        skill_id: int | None,
        auto_commit: bool = True,
    ) -> Task:
        """Insert one task for a user."""
        if not auto_commit and not self._has_active_transaction():
            raise RuntimeError(
                "task create with auto_commit=False requires an active transaction"
            )

        task = Task(
            user_id=user_id,
            title=title,
            description=description,
            priority=priority,
            status=status,
            estimated_minutes=estimated_minutes,
            deadline_at=deadline_at,
            planned_start_at=planned_start_at,
            planned_end_at=planned_end_at,
            skill_id=skill_id,
        )
        self.db.add(task)
        if auto_commit:
            self.db.commit()
            self.db.refresh(task)
        else:
            self.db.flush()
        return task

    def get_task_by_id(self, task_id: int) -> Task | None:
        """Fetch one task by primary key."""
        stmt = select(Task).where(Task.id == task_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def list_tasks_by_user(self, user_id: int) -> list[Task]:
        """Return all tasks owned by one user."""
        stmt = (
            select(Task).where(Task.user_id == user_id).order_by(Task.created_at.desc())
        )
        return list(self.db.execute(stmt).scalars().all())

    def list_planned_tasks_by_user(
        self,
        *,
        user_id: int,
        for_update: bool = False,
    ) -> list[Task]:
        """Return tasks with planned slots ordered by planned start."""
        stmt = (
            select(Task)
            .where(
                Task.user_id == user_id,
                Task.planned_start_at.is_not(None),
                Task.planned_end_at.is_not(None),
            )
            .order_by(Task.planned_start_at.asc(), Task.id.asc())
        )
        if for_update:
            stmt = stmt.with_for_update()
        return list(self.db.execute(stmt).scalars().all())

    def has_planned_overlap_for_user(
        self,
        *,
        user_id: int,
        planned_start_at: datetime,
        planned_end_at: datetime,
        for_update: bool = False,
    ) -> bool:
        """Return True when one planned task overlaps the requested time range."""
        overlap_filter = and_(
            Task.user_id == user_id,
            Task.planned_start_at.is_not(None),
            Task.planned_end_at.is_not(None),
            Task.planned_start_at < planned_end_at,
            planned_start_at < Task.planned_end_at,
        )
        stmt = select(Task.id).where(overlap_filter).limit(1)
        if for_update:
            stmt = stmt.with_for_update()
        return self.db.execute(stmt).scalar_one_or_none() is not None

    def list_tasks_by_users(self, *, user_ids: list[int]) -> list[Task]:
        """Return all tasks owned by the given users in one query."""
        if not user_ids:
            return []

        stmt = (
            select(Task)
            .where(Task.user_id.in_(user_ids))
            .order_by(Task.user_id.asc(), Task.created_at.desc())
        )
        return list(self.db.execute(stmt).scalars().all())

    def update_task(
        self, task: Task, *, auto_commit: bool = True, **updates: object
    ) -> Task:
        """Apply field updates to an existing task."""
        if not auto_commit and not self._has_active_transaction():
            raise RuntimeError(
                "task update with auto_commit=False requires an active transaction"
            )
        for field, value in updates.items():
            setattr(task, field, value)

        self.db.add(task)
        if auto_commit:
            self.db.commit()
            self.db.refresh(task)
        else:
            self.db.flush()
        return task

    def delete_task(self, task: Task) -> None:
        """Delete one task record."""
        self.db.delete(task)
        self.db.commit()

    def _has_active_transaction(self) -> bool:
        """Return True when Session currently has an active transaction."""
        return bool(self.db.in_transaction())
