"""Alembic migration environment.

Alembic reads the ORM metadata from here to create and run migrations.
"""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.core.config import settings
from app.db.base import Base
from app.models.availability_block import AvailabilityBlock  # noqa: F401
from app.models.profile import Profile  # noqa: F401
from app.models.routine_block import RoutineBlock  # noqa: F401
from app.models.session import Session  # noqa: F401
from app.models.session_participant import SessionParticipant  # noqa: F401
from app.models.session_suggestion import SessionSuggestion  # noqa: F401
from app.models.skill import Skill  # noqa: F401
from app.models.task import Task  # noqa: F401
from app.models.user import User  # noqa: F401
from app.models.user_skill import UserSkill  # noqa: F401

config = context.config
config.set_main_option("sqlalchemy.url", settings.database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations without creating a live database connection."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations against a live database connection."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
