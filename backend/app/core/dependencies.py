"""Shared FastAPI dependencies.

Dependencies are reusable objects or functions injected into routes.
"""

from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import get_db


def get_current_user_id(authorization: Annotated[str | None, Header()] = None) -> int:
    """Read the bearer token and extract the current user id."""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="missing Authorization header",
        )

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid Authorization header",
        )

    try:
        payload = decode_access_token(token)
        return int(payload["sub"])
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid or expired access token",
        ) from exc


CurrentUserId = Annotated[int, Depends(get_current_user_id)]

__all__ = ["CurrentUserId", "get_current_user_id", "get_db"]
