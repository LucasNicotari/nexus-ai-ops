# ADR 0008: Versioned database migrations

## Status

Accepted

## Context

Repository methods previously created tables. That made schema state dependent on application
execution order and provided no auditable revision history.

## Decision

Alembic is the exclusive schema-evolution mechanism. CI starts PostgreSQL, runs
`alembic upgrade head`, and then executes integration tests.

## Consequences

DDL becomes ordered, reviewable and reproducible. Repositories only query and persist data. The
initial revision uses idempotent DDL to adopt existing local development databases; future changes
must be new incremental migrations.
