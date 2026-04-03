"""Auth API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.api.handlers.auth_handler import AuthHandler
from app.repositories.user_repo import UserRepository
from app.schemas.auth import AuthResponse, LoginRequest, RegisterRequest
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


def get_auth_handler(db: Annotated[Session, Depends(get_db)]) -> AuthHandler:
    """Build the auth dependency chain for route handlers."""
    user_repo = UserRepository(db)
    auth_service = AuthService(user_repo)
    return AuthHandler(auth_service)


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    payload: RegisterRequest,
    handler: Annotated[AuthHandler, Depends(get_auth_handler)],
) -> AuthResponse:
    """Register a new user account."""
    return handler.registerUser(payload)


@router.post("/login", response_model=AuthResponse)
def login(
    payload: LoginRequest,
    handler: Annotated[AuthHandler, Depends(get_auth_handler)],
) -> AuthResponse:
    """Authenticate a user and return an access token."""
    return handler.loginUser(payload)
