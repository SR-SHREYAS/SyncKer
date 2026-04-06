"""Profile ORM model."""

from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import ProfileRole
from app.models.mixins import TimestampMixin


class Profile(TimestampMixin, Base):
    """User-facing profile and scheduling context."""

    __tablename__ = "profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), unique=True, nullable=False
    )
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    role: Mapped[ProfileRole] = mapped_column(
        Enum(ProfileRole, name="profile_role"),
        nullable=False,
    )
    timezone: Mapped[str] = mapped_column(String(64), nullable=False)

    user = relationship("User", back_populates="profile")
