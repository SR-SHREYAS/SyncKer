"""Auth API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.core.exceptions import AuthenticationError, ConflictError
from app.handlers.auth_handler import AuthHandler
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
    try:
        return handler.register(payload)
    except ConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.post("/login", response_model=AuthResponse)
def login(
    payload: LoginRequest,
    handler: Annotated[AuthHandler, Depends(get_auth_handler)],
) -> AuthResponse:
    """Authenticate a user and return an access token."""
    try:
        return handler.login(payload)
    except AuthenticationError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
