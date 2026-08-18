# ADR 0001: Use psycopg with a minimal PostgreSQL repository

## Context

The first persistence need is to store quality-approved operational events locally. The project already runs PostgreSQL through Docker Compose and does not yet need relationship mapping, migrations automation, or asynchronous access.

## Decision

Use `psycopg` with a small repository that creates and upserts the `operational_events` table. Keep schema creation explicit and load configuration from environment variables.

## Consequences

The SQL remains visible and easy to explain in an interview. We defer SQLAlchemy and a migration tool such as Alembic until the schema gains multiple related entities or requires versioned migrations across environments.
