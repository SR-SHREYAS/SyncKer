"""FastAPI application entrypoint."""

from fastapi import FastAPI, Request

from app.api.routes import api_router
from app.core.config import settings
from app.core.exceptions import AppError
from app.utils.logger import configure_logging, get_logger
from app.utils.responses import error_response

configure_logging()
logger = get_logger(__name__)


app = FastAPI(title=settings.app_name)
app.include_router(api_router)


@app.exception_handler(AppError)
async def handle_app_error(_: Request, exc: AppError):
    """Return controlled application errors with a stable payload."""
    logger.error("application error handled")
    return error_response(status_code=exc.status_code, message=exc.message)


@app.exception_handler(Exception)
async def handle_unexpected_error(_: Request, exc: Exception):
    """Return a generic server error for unexpected failures."""
    logger.exception("unexpected server error handled")
    return error_response(status_code=500, message="internal server error")


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    """Simple health route for startup checks."""
    return {"status": "ok"}
