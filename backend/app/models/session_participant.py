"""Session participant ORM model."""

from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import ParticipantResponseStatus, ParticipantRole
from app.models.mixins import TimestampMixin


class SessionParticipant(TimestampMixin, Base):
    """Participants attached to a scheduled session."""

    __tablename__ = "session_participants"
    __table_args__ = (UniqueConstraint("session_id", "user_id", name="uq_session_participant"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    participant_role: Mapped[ParticipantRole] = mapped_column(
        Enum(ParticipantRole, name="participant_role"),
        nullable=False,
    )
    response_status: Mapped[ParticipantResponseStatus] = mapped_column(
        Enum(ParticipantResponseStatus, name="participant_response_status"),
        default=ParticipantResponseStatus.INVITED,
        nullable=False,
    )
    joined_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    session = relationship("Session", back_populates="participants")
