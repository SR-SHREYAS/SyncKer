"""FastAPI application entrypoint."""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import api_router
from app.core.config import settings
from app.core.exceptions import AppError
from app.utils.logger import configure_logging, get_logger
from app.utils.responses import error_response

configure_logging()
logger = get_logger(__name__)


async def handle_app_error(_: Request, exc: AppError):
    """Return controlled application errors with a stable payload."""
    logger.error("application error handled")
    return error_response(status_code=exc.status_code, message=exc.message)


async def handle_unexpected_error(_: Request, exc: Exception):
    """Return a generic server error for unexpected failures."""
    logger.exception("unexpected server error handled")
    return error_response(status_code=500, message="internal server error")


def health_check() -> dict[str, str]:
    """Simple health route for startup checks."""
    return {"status": "ok"}


def create_app() -> FastAPI:
    """Build the FastAPI application with middleware and routes."""
    app = FastAPI(title=settings.app_name)

    if settings.cors_allowed_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_allowed_origins,
            allow_credentials=False,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    app.add_exception_handler(AppError, handle_app_error)
    app.add_exception_handler(Exception, handle_unexpected_error)
    app.include_router(api_router)
    app.add_api_route("/health", health_check, tags=["health"])
    return app


app = create_app()
