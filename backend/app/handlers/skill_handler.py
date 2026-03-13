"""Skill request handlers."""

from app.core.exceptions import AppError
from app.schemas.skill import (
    SkillCreateRequest,
    SkillResponse,
    UserSkillCreateRequest,
    UserSkillResponse,
)
from app.services.skill_service import SkillService
from app.utils.logger import get_logger

logger = get_logger(__name__)


class SkillHandler:
    """Maps skill-related requests to skill service calls."""

    def __init__(self, skill_service: SkillService) -> None:
        self.skill_service = skill_service

    def create_skill(self, payload: SkillCreateRequest) -> SkillResponse:
        """Handle skill creation requests."""
        try:
            skill = self.skill_service.create_skill(
                name=payload.name,
                slug=payload.slug,
                description=payload.description,
            )
            response = SkillResponse.model_validate(skill)
            logger.info("skill create handled for skill_id=%s", skill.id)
            return response
        except AppError:
            logger.exception("skill create failed for slug=%s", payload.slug)
            raise

    def list_skills(self) -> list[SkillResponse]:
        """Handle skill catalog listing requests."""
        try:
            skills = self.skill_service.list_skills()
            response = [SkillResponse.model_validate(skill) for skill in skills]
            logger.info("skill list handled with count=%s", len(response))
            return response
        except AppError:
            logger.exception("skill list failed")
            raise

    def attach_skill_to_user(self, user_id: int, payload: UserSkillCreateRequest) -> UserSkillResponse:
        """Handle user-skill creation requests."""
        try:
            user_skill = self.skill_service.attach_skill_to_user(
                user_id=user_id,
                skill_id=payload.skill_id,
                proficiency_level=payload.proficiency_level,
                is_teaching=payload.is_teaching,
                is_learning=payload.is_learning,
            )
            response = UserSkillResponse.model_validate(user_skill)
            logger.info(
                "user skill attach handled for user_id=%s skill_id=%s",
                user_id,
                payload.skill_id,
            )
            return response
        except AppError:
            logger.exception(
                "user skill attach failed for user_id=%s skill_id=%s",
                user_id,
                payload.skill_id,
            )
            raise

    def list_user_skills(self, user_id: int) -> list[UserSkillResponse]:
        """Handle user-skill listing requests."""
        try:
            user_skills = self.skill_service.list_user_skills(user_id)
            response = [UserSkillResponse.model_validate(user_skill) for user_skill in user_skills]
            logger.info("user skill list handled for user_id=%s count=%s", user_id, len(response))
            return response
        except AppError:
            logger.exception("user skill list failed for user_id=%s", user_id)
            raise
