"""Session ORM model."""

from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import SessionStatus
from app.models.mixins import TimestampMixin


class Session(TimestampMixin, Base):
    """Booked skill-sharing session created from a suggestion."""

    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_suggestion_id: Mapped[int | None] = mapped_column(
        ForeignKey("session_suggestions.id"),
        unique=True,
        nullable=True,
    )
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(180), nullable=False)
    scheduled_start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    scheduled_end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[SessionStatus] = mapped_column(
        Enum(SessionStatus, name="session_status"),
        default=SessionStatus.SCHEDULED,
        nullable=False,
    )
    created_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    skill = relationship("Skill", back_populates="sessions")
    suggestion = relationship("SessionSuggestion", back_populates="session")
    participants = relationship(
        "SessionParticipant",
        back_populates="session",
        cascade="all, delete-orphan",
    )
