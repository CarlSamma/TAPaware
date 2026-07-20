"""Alembic environment for CHRONOS PostgreSQL migrations."""
from __future__ import annotations

import os
from logging.config import fileConfig
from typing import TYPE_CHECKING

from alembic import context
from sqlalchemy import create_engine

if TYPE_CHECKING:
    from sqlalchemy.engine import Connection

# Interpret the config file for Python logging.
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Autogenerate target metadata is intentionally None: we write manual
# migrations to keep CHRONOS schema decoupled from ORM definitions.
target_metadata = None


def get_url() -> str:
    """Return PostgreSQL DSN for CHRONOS migrations.

    Order of precedence:
    1. CHRONOS_DB_DSN environment variable.
    2. .env file loaded via pydantic settings.
    3. Local development default.
    """
    env_dsn = os.environ.get("CHRONOS_DB_DSN")
    if env_dsn:
        return env_dsn

    try:
        from tap.config import get_settings

        settings = get_settings()
        return str(settings.chronos_db_dsn)
    except Exception:  # pragma: no cover
        pass

    return "postgresql://tap:tap@localhost:5432/chronos"


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = create_engine(get_url(), future=True)

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
