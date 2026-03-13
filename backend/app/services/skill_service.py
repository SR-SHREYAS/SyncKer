"""Skill business logic."""

from app.core.exceptions import ConflictError, NotFoundError
from app.models.skill import Skill
from app.models.user_skill import UserSkill
from app.repositories.skill_repo import SkillRepository
from app.utils.logger import get_logger

logger = get_logger(__name__)


class SkillService:
    """Business rules for skill catalog and user-skill links."""

    def __init__(self, skill_repo: SkillRepository) -> None:
        self.skill_repo = skill_repo

    def create_skill(self, *, name: str, slug: str, description: str | None = None) -> Skill:
        """Create a new skill if its slug is still available."""
        existing_skill = self.skill_repo.get_skill_by_slug(slug)
        if existing_skill is not None:
            logger.error("skill create blocked: slug already exists for slug=%s", slug)
            raise ConflictError("skill slug already exists")

        skill = self.skill_repo.create_skill(name=name, slug=slug, description=description)
        logger.info("skill create service completed for skill_id=%s", skill.id)
        return skill

    def list_skills(self) -> list[Skill]:
        """Return the current skill catalog."""
        skills = self.skill_repo.list_skills()
        logger.info("skill list service completed with count=%s", len(skills))
        return skills

    def attach_skill_to_user(
        self,
        *,
        user_id: int,
        skill_id: int,
        proficiency_level: str,
        is_teaching: bool = False,
        is_learning: bool = True,
    ) -> UserSkill:
        """Link one skill to one user for learning or teaching."""
        skill = self.skill_repo.get_skill_by_id(skill_id)
        if skill is None:
            logger.error("user skill attach blocked: skill not found for skill_id=%s", skill_id)
            raise NotFoundError("skill not found")

        existing_user_skill = self.skill_repo.get_user_skill(user_id=user_id, skill_id=skill_id)
        if existing_user_skill is not None:
            logger.error(
                "user skill attach blocked: relation already exists for user_id=%s skill_id=%s",
                user_id,
                skill_id,
            )
            raise ConflictError("user skill already exists")

        user_skill = self.skill_repo.attach_skill_to_user(
            user_id=user_id,
            skill_id=skill_id,
            proficiency_level=proficiency_level,
            is_teaching=is_teaching,
            is_learning=is_learning,
        )
        logger.info(
            "user skill attach service completed for user_id=%s skill_id=%s",
            user_id,
            skill_id,
        )
        return user_skill

    def list_user_skills(self, user_id: int) -> list[UserSkill]:
        """Return all skills linked to one user."""
        user_skills = self.skill_repo.list_user_skills(user_id)
        logger.info("user skill list service completed for user_id=%s count=%s", user_id, len(user_skills))
        return user_skills
