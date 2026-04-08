"""Skill persistence queries."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.skill import Skill
from app.models.user_skill import UserSkill


class SkillRepository:
    """Database access for skills and user-skill links."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create_skill(
        self, *, name: str, slug: str, description: str | None = None
    ) -> Skill:
        """Insert a new skill in the shared catalog."""
        skill = Skill(name=name, slug=slug, description=description)
        self.db.add(skill)
        self.db.commit()
        self.db.refresh(skill)
        return skill

    def get_skill_by_id(self, skill_id: int) -> Skill | None:
        """Fetch one skill by primary key."""
        stmt = select(Skill).where(Skill.id == skill_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_skill_by_slug(self, slug: str) -> Skill | None:
        """Fetch one skill by slug for clean URLs or lookups."""
        stmt = select(Skill).where(Skill.slug == slug)
        return self.db.execute(stmt).scalar_one_or_none()

    def list_skills(self) -> list[Skill]:
        """Return the full skill catalog ordered by name."""
        stmt = select(Skill).order_by(Skill.name.asc())
        return list(self.db.execute(stmt).scalars().all())

    def attach_skill_to_user(
        self,
        *,
        user_id: int,
        skill_id: int,
        proficiency_level: str,
        is_teaching: bool = False,
        is_learning: bool = True
    ) -> UserSkill:
        """Create a user-skill relation for learning or teaching."""
        user_skill = UserSkill(
            user_id=user_id,
            skill_id=skill_id,
            proficiency_level=proficiency_level,
            is_teaching=is_teaching,
            is_learning=is_learning,
        )
        self.db.add(user_skill)
        self.db.commit()
        self.db.refresh(user_skill)
        return user_skill

    def get_user_skill(self, *, user_id: int, skill_id: int) -> UserSkill | None:
        """Fetch one user-skill relation by user and skill."""
        stmt = select(UserSkill).where(
            UserSkill.user_id == user_id,
            UserSkill.skill_id == skill_id,
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def list_user_skills(self, user_id: int) -> list[UserSkill]:
        """Return all skills linked to one user."""
        stmt = (
            select(UserSkill)
            .where(UserSkill.user_id == user_id)
            .order_by(UserSkill.created_at.desc())
        )
        return list(self.db.execute(stmt).scalars().all())

    def update_user_skill(self, user_skill: UserSkill, **updates: object) -> UserSkill:
        """Apply field updates to an existing user-skill relation."""
        for field, value in updates.items():
            setattr(user_skill, field, value)

        self.db.add(user_skill)
        self.db.commit()
        self.db.refresh(user_skill)
        return user_skill
