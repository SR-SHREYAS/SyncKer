"""Availability block ORM model."""

from datetime import date, time

from sqlalchemy import Boolean, Date, ForeignKey, Integer, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin


class AvailabilityBlock(TimestampMixin, Base):
    """Free time blocks used by the scheduler.

    These represent when a user says they are available.
    """

    __tablename__ = "availability_blocks"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    day_of_week: Mapped[int | None] = mapped_column(Integer, nullable=True)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    specific_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    user = relationship("User", back_populates="availability_blocks")
