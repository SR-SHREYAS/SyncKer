"""User API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.dependencies import CurrentUserId, get_db
from app.handlers.user_handler import UserHandler
from app.repositories.user_repo import UserRepository
from app.schemas.profile import ProfileCreateRequest, ProfileResponse, ProfileUpdateRequest
from app.schemas.user import UserResponse, UserUpdateRequest
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])


def get_user_handler(db: Annotated[Session, Depends(get_db)]) -> UserHandler:
    """Build the user dependency chain for route handlers."""
    user_repo = UserRepository(db)
    user_service = UserService(user_repo)
    return UserHandler(user_service)


@router.get("/me", response_model=UserResponse)
def get_me(
    current_user_id: CurrentUserId,
    handler: Annotated[UserHandler, Depends(get_user_handler)],
) -> UserResponse:
    """Return the authenticated user's account data."""
    return handler.get_me(current_user_id)


@router.patch("/me", response_model=UserResponse)
def update_me(
    payload: UserUpdateRequest,
    current_user_id: CurrentUserId,
    handler: Annotated[UserHandler, Depends(get_user_handler)],
) -> UserResponse:
    """Update the authenticated user's account data."""
    return handler.update_me(current_user_id, payload)


@router.get("/me/profile", response_model=ProfileResponse)
def get_profile(
    current_user_id: CurrentUserId,
    handler: Annotated[UserHandler, Depends(get_user_handler)],
) -> ProfileResponse:
    """Return the authenticated user's profile."""
    return handler.get_profile(current_user_id)


@router.post(
    "/me/profile",
    response_model=ProfileResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_profile(
    payload: ProfileCreateRequest,
    current_user_id: CurrentUserId,
    handler: Annotated[UserHandler, Depends(get_user_handler)],
) -> ProfileResponse:
    """Create the authenticated user's profile."""
    return handler.create_profile(current_user_id, payload)


@router.patch("/me/profile", response_model=ProfileResponse)
def update_profile(
    payload: ProfileUpdateRequest,
    current_user_id: CurrentUserId,
    handler: Annotated[UserHandler, Depends(get_user_handler)],
) -> ProfileResponse:
    """Update the authenticated user's profile."""
    return handler.update_profile(current_user_id, payload)
