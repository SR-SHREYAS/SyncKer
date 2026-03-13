"""Central route registry."""

from fastapi import APIRouter

from app.api.auth import router as auth_router
from app.api.users import router as users_router

api_router = APIRouter()

# Auth APIs
api_router.include_router(auth_router)

# User APIs
api_router.include_router(users_router)
