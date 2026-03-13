"""Routine persistence queries."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.routine_block import RoutineBlock


class RoutineRepository:
    """Database access for routine blocks."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create_block(
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
        """Insert one routine block for a user."""
        block = RoutineBlock(
            user_id=user_id,
            title=title,
            day_of_week=day_of_week,
            start_time=start_time,
            end_time=end_time,
            is_recurring=is_recurring,
            specific_date=specific_date,
        )
        self.db.add(block)
        self.db.commit()
        self.db.refresh(block)
        return block

    def get_block_by_id(self, block_id: int) -> RoutineBlock | None:
        """Fetch one routine block by primary key."""
        stmt = select(RoutineBlock).where(RoutineBlock.id == block_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def list_blocks_by_user(self, user_id: int) -> list[RoutineBlock]:
        """Return all routine blocks owned by one user."""
        stmt = (
            select(RoutineBlock)
            .where(RoutineBlock.user_id == user_id)
            .order_by(RoutineBlock.created_at.desc())
        )
        return list(self.db.execute(stmt).scalars().all())

    def update_block(self, block: RoutineBlock, **updates: object) -> RoutineBlock:
        """Apply field updates to an existing routine block."""
        for field, value in updates.items():
            setattr(block, field, value)

        self.db.add(block)
        self.db.commit()
        self.db.refresh(block)
        return block

    def delete_block(self, block: RoutineBlock) -> None:
        """Delete one routine block."""
        self.db.delete(block)
        self.db.commit()
