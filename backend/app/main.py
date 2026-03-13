"""FastAPI application entrypoint."""

from fastapi import FastAPI

from app.api.auth import router as auth_router
from app.core.config import settings


app = FastAPI(title=settings.app_name)
app.include_router(auth_router)


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    """Simple health route for startup checks."""
    return {"status": "ok"}
