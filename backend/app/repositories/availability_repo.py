"""Availability persistence queries."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.availability_block import AvailabilityBlock


class AvailabilityRepository:
    """Database access for availability blocks."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create_block(
        self,
        *,
        user_id: int,
        day_of_week: int | None,
        start_time: object,
        end_time: object,
        is_recurring: bool,
        specific_date: object,
    ) -> AvailabilityBlock:
        """Insert one availability block for a user."""
        block = AvailabilityBlock(
            user_id=user_id,
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

    def get_block_by_id(self, block_id: int) -> AvailabilityBlock | None:
        """Fetch one availability block by primary key."""
        stmt = select(AvailabilityBlock).where(AvailabilityBlock.id == block_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def list_blocks_by_user(self, user_id: int) -> list[AvailabilityBlock]:
        """Return all availability blocks owned by one user."""
        stmt = (
            select(AvailabilityBlock)
            .where(AvailabilityBlock.user_id == user_id)
            .order_by(AvailabilityBlock.created_at.desc())
        )
        return list(self.db.execute(stmt).scalars().all())

    def update_block(self, block: AvailabilityBlock, **updates: object) -> AvailabilityBlock:
        """Apply field updates to an existing availability block."""
        for field, value in updates.items():
            setattr(block, field, value)

        self.db.add(block)
        self.db.commit()
        self.db.refresh(block)
        return block

    def delete_block(self, block: AvailabilityBlock) -> None:
        """Delete one availability block."""
        self.db.delete(block)
        self.db.commit()
