"""Database metadata and model imports."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Shared base class for ORM models.

    ORM means Object Relational Mapping:
    Python classes map to database tables.
    """
