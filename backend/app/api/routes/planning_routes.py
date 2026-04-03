"""Planning API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.core.dependencies import CurrentUserId, get_db
from app.api.handlers.planning_handler import PlanningHandler
from app.repositories.availability_repo import AvailabilityRepository
from app.repositories.routine_repo import RoutineRepository
from app.repositories.task_repo import TaskRepository
from app.schemas.availability import (
    AvailabilityBlockCreateRequest,
    AvailabilityBlockResponse,
    AvailabilityBlockUpdateRequest,
)
from app.schemas.routine import (
    RoutineBlockCreateRequest,
    RoutineBlockResponse,
    RoutineBlockUpdateRequest,
)
from app.schemas.task import TaskCreateRequest, TaskResponse, TaskUpdateRequest
from app.services.planning_service import PlanningService

router = APIRouter(prefix="/planning", tags=["planning"])


def get_planning_handler(db: Annotated[Session, Depends(get_db)]) -> PlanningHandler:
    """Build the planning dependency chain for route handlers."""
    task_repo = TaskRepository(db)
    availability_repo = AvailabilityRepository(db)
    routine_repo = RoutineRepository(db)
    planning_service = PlanningService(task_repo, availability_repo, routine_repo)
    return PlanningHandler(planning_service)


@router.post("/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(
    payload: TaskCreateRequest,
    current_user_id: CurrentUserId,
    handler: Annotated[PlanningHandler, Depends(get_planning_handler)],
) -> TaskResponse:
    """Create one task for the authenticated user."""
    return handler.createPlanningTask(current_user_id, payload)


@router.get("/tasks", response_model=list[TaskResponse])
def list_tasks(
    current_user_id: CurrentUserId,
    handler: Annotated[PlanningHandler, Depends(get_planning_handler)],
) -> list[TaskResponse]:
    """Return tasks owned by the authenticated user."""
    return handler.listPlanningTasks(current_user_id)


@router.patch("/tasks/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: int,
    payload: TaskUpdateRequest,
    current_user_id: CurrentUserId,
    handler: Annotated[PlanningHandler, Depends(get_planning_handler)],
) -> TaskResponse:
    """Update one owned task."""
    return handler.updatePlanningTask(current_user_id, task_id, payload)


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: int,
    current_user_id: CurrentUserId,
    handler: Annotated[PlanningHandler, Depends(get_planning_handler)],
) -> Response:
    """Delete one owned task."""
    handler.deletePlanningTask(current_user_id, task_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/availability",
    response_model=AvailabilityBlockResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_availability_block(
    payload: AvailabilityBlockCreateRequest,
    current_user_id: CurrentUserId,
    handler: Annotated[PlanningHandler, Depends(get_planning_handler)],
) -> AvailabilityBlockResponse:
    """Create one availability block for the authenticated user."""
    return handler.createAvailabilityBlock(current_user_id, payload)


@router.get("/availability", response_model=list[AvailabilityBlockResponse])
def list_availability_blocks(
    current_user_id: CurrentUserId,
    handler: Annotated[PlanningHandler, Depends(get_planning_handler)],
) -> list[AvailabilityBlockResponse]:
    """Return availability blocks owned by the authenticated user."""
    return handler.listAvailabilityBlocks(current_user_id)


@router.patch("/availability/{block_id}", response_model=AvailabilityBlockResponse)
def update_availability_block(
    block_id: int,
    payload: AvailabilityBlockUpdateRequest,
    current_user_id: CurrentUserId,
    handler: Annotated[PlanningHandler, Depends(get_planning_handler)],
) -> AvailabilityBlockResponse:
    """Update one owned availability block."""
    return handler.updateAvailabilityBlock(current_user_id, block_id, payload)


@router.delete("/availability/{block_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_availability_block(
    block_id: int,
    current_user_id: CurrentUserId,
    handler: Annotated[PlanningHandler, Depends(get_planning_handler)],
) -> Response:
    """Delete one owned availability block."""
    handler.deleteAvailabilityBlock(current_user_id, block_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/routine", response_model=RoutineBlockResponse, status_code=status.HTTP_201_CREATED)
def create_routine_block(
    payload: RoutineBlockCreateRequest,
    current_user_id: CurrentUserId,
    handler: Annotated[PlanningHandler, Depends(get_planning_handler)],
) -> RoutineBlockResponse:
    """Create one routine block for the authenticated user."""
    return handler.createRoutineBlock(current_user_id, payload)


@router.get("/routine", response_model=list[RoutineBlockResponse])
def list_routine_blocks(
    current_user_id: CurrentUserId,
    handler: Annotated[PlanningHandler, Depends(get_planning_handler)],
) -> list[RoutineBlockResponse]:
    """Return routine blocks owned by the authenticated user."""
    return handler.listRoutineBlocks(current_user_id)


@router.patch("/routine/{block_id}", response_model=RoutineBlockResponse)
def update_routine_block(
    block_id: int,
    payload: RoutineBlockUpdateRequest,
    current_user_id: CurrentUserId,
    handler: Annotated[PlanningHandler, Depends(get_planning_handler)],
) -> RoutineBlockResponse:
    """Update one owned routine block."""
    return handler.updateRoutineBlock(current_user_id, block_id, payload)


@router.delete("/routine/{block_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_routine_block(
    block_id: int,
    current_user_id: CurrentUserId,
    handler: Annotated[PlanningHandler, Depends(get_planning_handler)],
) -> Response:
    """Delete one owned routine block."""
    handler.deleteRoutineBlock(current_user_id, block_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
