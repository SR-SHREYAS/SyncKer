"""Task persistence queries."""

from datetime import datetime

from sqlalchemy import select
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
            if self.db.in_transaction() is None:
                raise RuntimeError(
                    "task create with auto_commit=False requires an active transaction"
                )
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

    def update_task(self, task: Task, **updates: object) -> Task:
        """Apply field updates to an existing task."""
        for field, value in updates.items():
            setattr(task, field, value)

        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task

    def delete_task(self, task: Task) -> None:
        """Delete one task record."""
        self.db.delete(task)
        self.db.commit()
