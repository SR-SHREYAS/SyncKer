"""User ORM model."""

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin


class User(TimestampMixin, Base):
    """Core user table.

    This model is the base identity record used across the whole MVP.
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    profile = relationship("Profile", back_populates="user", uselist=False)
    skills = relationship("UserSkill", back_populates="user", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="user", cascade="all, delete-orphan")
    availability_blocks = relationship(
        "AvailabilityBlock",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    routine_blocks = relationship(
        "RoutineBlock",
        back_populates="user",
        cascade="all, delete-orphan",
    )
