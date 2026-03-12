"""User skill ORM model."""

from sqlalchemy import Boolean, Enum, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import ProficiencyLevel
from app.models.mixins import TimestampMixin


class UserSkill(TimestampMixin, Base):
    """Skill relation that captures teaching and learning intent."""

    __tablename__ = "user_skills"
    __table_args__ = (UniqueConstraint("user_id", "skill_id", name="uq_user_skill"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id"), nullable=False)
    proficiency_level: Mapped[ProficiencyLevel] = mapped_column(
        Enum(ProficiencyLevel, name="proficiency_level"),
        nullable=False,
    )
    is_teaching: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_learning: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    user = relationship("User", back_populates="skills")
    skill = relationship("Skill", back_populates="user_skills")
