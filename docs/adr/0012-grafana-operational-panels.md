# ADR 0012: Grafana operational panels from PostgreSQL

## Status

Accepted

## Decision

Provision PostgreSQL as a second Grafana data source and query it directly for event volume,
anomalies, and services with critical signals.

## Rationale

Prometheus measures API behaviour; PostgreSQL is the source of truth for NEXUS business data.
Using both makes the dashboard distinguish service health from operational intelligence.

## Consequences

The Grafana container receives local PostgreSQL credentials through Compose environment variables.
This is acceptable for the private local stack. A production deployment requires a dedicated
read-only database role and a managed secret source.
