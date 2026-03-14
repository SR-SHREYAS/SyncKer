"""Session API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.dependencies import CurrentUserId, get_db
from app.handlers.session_handler import SessionHandler
from app.repositories.session_repo import SessionRepository
from app.repositories.suggestion_repo import SuggestionRepository
from app.schemas.session import (
    SessionCreateFromSuggestionRequest,
    SessionDetailResponse,
    SessionResponse,
)
from app.services.session_service import SessionService

router = APIRouter(prefix="/sessions", tags=["sessions"])


def get_session_handler(db: Annotated[Session, Depends(get_db)]) -> SessionHandler:
    """Build the session dependency chain for route handlers."""
    session_repo = SessionRepository(db)
    suggestion_repo = SuggestionRepository(db)
    session_service = SessionService(session_repo, suggestion_repo)
    return SessionHandler(session_service)


@router.post(
    "/from-suggestion",
    response_model=SessionDetailResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_session_from_suggestion(
    payload: SessionCreateFromSuggestionRequest,
    current_user_id: CurrentUserId,
    handler: Annotated[SessionHandler, Depends(get_session_handler)],
) -> SessionDetailResponse:
    """Create one booked session from a suggestion."""
    return handler.create_from_suggestion(current_user_id, payload)


@router.get("", response_model=list[SessionResponse])
def list_sessions(
    current_user_id: CurrentUserId,
    handler: Annotated[SessionHandler, Depends(get_session_handler)],
) -> list[SessionResponse]:
    """Return sessions created by the authenticated user."""
    return handler.list_sessions(current_user_id)


@router.get("/{session_id}", response_model=SessionDetailResponse)
def get_session(
    session_id: int,
    current_user_id: CurrentUserId,
    handler: Annotated[SessionHandler, Depends(get_session_handler)],
) -> SessionDetailResponse:
    """Return one owned session with participants."""
    return handler.get_session(current_user_id, session_id)
