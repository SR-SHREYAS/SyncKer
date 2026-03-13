"""Shared response helpers."""

from fastapi.responses import JSONResponse


def error_response(*, status_code: int, message: str) -> JSONResponse:
    """Return a consistent error payload."""
    return JSONResponse(
        status_code=status_code,
        content={"detail": message},
    )
