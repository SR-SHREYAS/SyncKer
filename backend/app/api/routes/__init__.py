"""Central route registry with entity-specific route modules."""

from fastapi import APIRouter

from app.api.routes.auth_routes import router as auth_router
from app.api.routes.planning_routes import router as planning_router
from app.api.routes.scheduling_routes import router as scheduling_router
from app.api.routes.session_routes import router as sessions_router
from app.api.routes.skill_routes import router as skills_router
from app.api.routes.team_routes import router as teams_router
from app.api.routes.user_routes import router as users_router

api_router = APIRouter()

# Auth APIs
api_router.include_router(auth_router)

# User APIs
api_router.include_router(users_router)

# Skill APIs
api_router.include_router(skills_router)

# Team Workspace APIs
api_router.include_router(teams_router)

# Planning APIs
api_router.include_router(planning_router)

# Scheduling APIs
api_router.include_router(scheduling_router)

# Session APIs
api_router.include_router(sessions_router)

__all__ = ["api_router"]
