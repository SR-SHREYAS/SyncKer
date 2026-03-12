"""Shared FastAPI dependencies."""
"""Shared FastAPI dependencies.

Dependencies are reusable objects or functions injected into routes.
"""

from app.db.session import get_db

__all__ = ["get_db"]
