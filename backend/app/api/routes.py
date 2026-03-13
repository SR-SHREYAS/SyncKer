"""Central route registry."""

from fastapi import APIRouter

from app.api.auth import router as auth_router
from app.api.planning import router as planning_router
from app.api.skills import router as skills_router
from app.api.users import router as users_router

api_router = APIRouter()

# Auth APIs
api_router.include_router(auth_router)

# User APIs
api_router.include_router(users_router)

# Skill APIs
api_router.include_router(skills_router)

# Planning APIs
api_router.include_router(planning_router)
