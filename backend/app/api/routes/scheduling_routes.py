"""Scheduling API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.ai.scheduler_engine import SchedulerEngine
from app.core.dependencies import CurrentUserId, get_db
from app.api.handlers.scheduling_handler import SchedulingHandler
from app.repositories.availability_repo import AvailabilityRepository
from app.repositories.routine_repo import RoutineRepository
from app.repositories.skill_repo import SkillRepository
from app.repositories.suggestion_repo import SuggestionRepository
from app.repositories.task_repo import TaskRepository
from app.repositories.team_repo import TeamRepository
from app.repositories.user_repo import UserRepository
from app.schemas.scheduling import (
    SessionSuggestionResponse,
    SuggestionGenerationRequest,
    SuggestionStatusUpdateRequest,
)
from app.services.scheduling_service import SchedulingService
from app.services.team_service import TeamService

router = APIRouter(prefix="/scheduling", tags=["scheduling"])


def get_scheduling_handler(
    db: Annotated[Session, Depends(get_db)],
) -> SchedulingHandler:
    """Build the scheduling dependency chain for route handlers."""
    suggestion_repo = SuggestionRepository(db)
    task_repo = TaskRepository(db)
    availability_repo = AvailabilityRepository(db)
    routine_repo = RoutineRepository(db)
    skill_repo = SkillRepository(db)
    team_repo = TeamRepository(db)
    user_repo = UserRepository(db)
    team_service = TeamService(team_repo, user_repo)
    scheduler_engine = SchedulerEngine()
    scheduling_service = SchedulingService(
        suggestion_repo,
        scheduler_engine,
        task_repo,
        availability_repo,
        routine_repo,
        skill_repo,
        team_service,
    )
    return SchedulingHandler(scheduling_service)


@router.post(
    "/suggestions/generate",
    response_model=SessionSuggestionResponse,
    status_code=status.HTTP_201_CREATED,
)
def generate_suggestion(
    payload: SuggestionGenerationRequest,
    current_user_id: CurrentUserId,
    handler: Annotated[SchedulingHandler, Depends(get_scheduling_handler)],
) -> SessionSuggestionResponse:
    """Generate one session suggestion for the authenticated user."""
    return handler.generateSchedulingSuggestion(current_user_id, payload)


@router.get("/suggestions", response_model=list[SessionSuggestionResponse])
def list_suggestions(
    current_user_id: CurrentUserId,
    handler: Annotated[SchedulingHandler, Depends(get_scheduling_handler)],
) -> list[SessionSuggestionResponse]:
    """Return suggestions generated for the authenticated user."""
    return handler.listSchedulingSuggestions(current_user_id)


@router.patch("/suggestions/{suggestion_id}", response_model=SessionSuggestionResponse)
def update_suggestion_status(
    suggestion_id: int,
    payload: SuggestionStatusUpdateRequest,
    current_user_id: CurrentUserId,
    handler: Annotated[SchedulingHandler, Depends(get_scheduling_handler)],
) -> SessionSuggestionResponse:
    """Update the status of one owned suggestion."""
    return handler.updateSchedulingSuggestionStatus(
        current_user_id, suggestion_id, payload
    )
