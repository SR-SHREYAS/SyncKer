"""Database metadata and model imports."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Shared base class for ORM models.

    ORM means Object Relational Mapping:
    Python classes map to database tables.
    """


# Keep entity imports here so migration tools can "see" all tables in one place.
from app.models.availability_block import AvailabilityBlock  # noqa: E402,F401
from app.models.profile import Profile  # noqa: E402,F401
from app.models.routine_block import RoutineBlock  # noqa: E402,F401
from app.models.session import Session  # noqa: E402,F401
from app.models.session_participant import SessionParticipant  # noqa: E402,F401
from app.models.session_suggestion import SessionSuggestion  # noqa: E402,F401
from app.models.skill import Skill  # noqa: E402,F401
from app.models.task import Task  # noqa: E402,F401
from app.models.user import User  # noqa: E402,F401
from app.models.user_skill import UserSkill  # noqa: E402,F401
