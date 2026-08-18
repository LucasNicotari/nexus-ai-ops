"""Alembic environment for the NEXUS PostgreSQL schema."""

from __future__ import annotations

import os

from alembic import context
from sqlalchemy import engine_from_config, pool

config = context.config


def database_url() -> str:
    """Build the database URL from the application's environment contract."""
    return os.getenv(
        "NEXUS_DATABASE_URL",
        "postgresql+psycopg://{user}:{password}@{host}:{port}/{database}".format(
            database=os.getenv("POSTGRES_DB", "nexus"),
            user=os.getenv("POSTGRES_USER", "nexus"),
            password=os.getenv("POSTGRES_PASSWORD", "change-me-for-local-development"),
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=os.getenv("POSTGRES_PORT", "5432"),
        ),
    )


def run_migrations_offline() -> None:
    """Emit migration SQL without connecting to PostgreSQL."""
    context.configure(url=database_url(), literal_binds=True, dialect_opts={"paramstyle": "named"})
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Apply migrations in one database transaction."""
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = database_url()
    connectable = engine_from_config(configuration, prefix="sqlalchemy.", poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
