# ADR 0006: Expose a thin synchronous FastAPI read API

## Context

NEXUS needs a stable integration boundary for dashboards and future consumers, but model training and evaluation are not request-time operations.

## Decision

Expose health, paginated events, metric analytics, and service incident indicators through synchronous FastAPI routes backed by request-scoped PostgreSQL repositories. Do not expose model training or temporal evaluation endpoints.

## Consequences

The API remains fast, read-only, and reusable by dashboards or external clients. A future inference endpoint requires a versioned model artifact and an explicit prediction storage policy.
