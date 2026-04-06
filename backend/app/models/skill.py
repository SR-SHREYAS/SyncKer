"""Skill ORM model."""

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin


class Skill(TimestampMixin, Base):
    """Reusable skill catalog entry."""

    __tablename__ = "skills"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(
        String(120), unique=True, index=True, nullable=False
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    user_skills = relationship("UserSkill", back_populates="skill")
    tasks = relationship("Task", back_populates="skill")
    suggestions = relationship("SessionSuggestion", back_populates="skill")
    sessions = relationship("Session", back_populates="skill")
