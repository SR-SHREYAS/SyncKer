"""Skill API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.dependencies import CurrentUserId, get_db
from app.api.handlers.skill_handler import SkillHandler
from app.repositories.skill_repo import SkillRepository
from app.schemas.skill import (
    SkillCreateRequest,
    SkillResponse,
    UserSkillCreateRequest,
    UserSkillResponse,
)
from app.services.skill_service import SkillService

router = APIRouter(prefix="/skills", tags=["skills"])


def get_skill_handler(db: Annotated[Session, Depends(get_db)]) -> SkillHandler:
    """Build the skill dependency chain for route handlers."""
    skill_repo = SkillRepository(db)
    skill_service = SkillService(skill_repo)
    return SkillHandler(skill_service)


@router.post("", response_model=SkillResponse, status_code=status.HTTP_201_CREATED)
def create_skill(
    payload: SkillCreateRequest,
    handler: Annotated[SkillHandler, Depends(get_skill_handler)],
) -> SkillResponse:
    """Create one skill in the shared catalog."""
    return handler.createSkillCatalogEntry(payload)


@router.get("", response_model=list[SkillResponse])
def list_skills(
    handler: Annotated[SkillHandler, Depends(get_skill_handler)],
) -> list[SkillResponse]:
    """Return the shared skill catalog."""
    return handler.listSkillCatalog()


@router.post("/me", response_model=UserSkillResponse, status_code=status.HTTP_201_CREATED)
def attach_skill_to_me(
    payload: UserSkillCreateRequest,
    current_user_id: CurrentUserId,
    handler: Annotated[SkillHandler, Depends(get_skill_handler)],
) -> UserSkillResponse:
    """Attach one skill to the authenticated user."""
    return handler.attachSkillToCurrentUser(current_user_id, payload)


@router.get("/me", response_model=list[UserSkillResponse])
def list_my_skills(
    current_user_id: CurrentUserId,
    handler: Annotated[SkillHandler, Depends(get_skill_handler)],
) -> list[UserSkillResponse]:
    """Return skills linked to the authenticated user."""
    return handler.listCurrentUserSkills(current_user_id)
