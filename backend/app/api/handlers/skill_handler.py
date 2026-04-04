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
from app.utils.request_validation import (
    ensure_non_empty_text,
    ensure_optional_non_empty_text,
    ensure_positive_id,
)

logger = get_logger(__name__)


class SkillHandler:
    """Maps skill-related requests to skill service calls."""

    def __init__(self, skill_service: SkillService) -> None:
        self.skill_service = skill_service

    def createSkillCatalogEntry(self, payload: SkillCreateRequest) -> SkillResponse:
        """Handle skill creation requests."""
        try:
            ensure_non_empty_text(payload.name, field_name="name")
            ensure_non_empty_text(payload.slug, field_name="slug")
            normalized_description = payload.description
            if normalized_description is not None:
                normalized_description = normalized_description.strip()
                if not normalized_description:
                    normalized_description = None
            ensure_optional_non_empty_text(normalized_description, field_name="description")

            created_skill = self.skill_service.CreateSkillCatalogEntry(
                name=payload.name,
                slug=payload.slug,
                description=normalized_description,
            )
            skill_response = SkillResponse.model_validate(created_skill)
            logger.info("skill createSkillCatalogEntry handled for skill_id=%s", created_skill.id)
            return skill_response
        except AppError:
            logger.exception("skill createSkillCatalogEntry failed for slug=%s", payload.slug)
            raise

    def listSkillCatalog(self) -> list[SkillResponse]:
        """Handle skill catalog listing requests."""
        try:
            skill_catalog = self.skill_service.ListSkillCatalog()
            skill_responses = [SkillResponse.model_validate(skill) for skill in skill_catalog]
            logger.info("skill listSkillCatalog handled with count=%s", len(skill_responses))
            return skill_responses
        except AppError:
            logger.exception("skill listSkillCatalog failed")
            raise

    def attachSkillToCurrentUser(self, user_id: int, payload: UserSkillCreateRequest) -> UserSkillResponse:
        """Handle user-skill creation requests."""
        try:
            ensure_positive_id(user_id, field_name="user_id")
            ensure_positive_id(payload.skill_id, field_name="skill_id")

            user_skill_relation = self.skill_service.AttachSkillToUser(
                user_id=user_id,
                skill_id=payload.skill_id,
                proficiency_level=payload.proficiency_level,
                is_teaching=payload.is_teaching,
                is_learning=payload.is_learning,
            )
            user_skill_response = UserSkillResponse.model_validate(user_skill_relation)
            logger.info(
                "user skill attachSkillToCurrentUser handled for user_id=%s skill_id=%s",
                user_id,
                payload.skill_id,
            )
            return user_skill_response
        except AppError:
            logger.exception(
                "user skill attachSkillToCurrentUser failed for user_id=%s skill_id=%s",
                user_id,
                payload.skill_id,
            )
            raise

    def listCurrentUserSkills(self, user_id: int) -> list[UserSkillResponse]:
        """Handle user-skill listing requests."""
        try:
            ensure_positive_id(user_id, field_name="user_id")
            user_skill_relations = self.skill_service.ListUserSkills(user_id)
            user_skill_responses = [
                UserSkillResponse.model_validate(user_skill_relation)
                for user_skill_relation in user_skill_relations
            ]
            logger.info(
                "user skill listCurrentUserSkills handled for user_id=%s count=%s",
                user_id,
                len(user_skill_responses),
            )
            return user_skill_responses
        except AppError:
            logger.exception("user skill listCurrentUserSkills failed for user_id=%s", user_id)
            raise
