# ADR 0011: Local Prometheus and Grafana observability

## Status

Accepted

## Decision

Expose vendor-neutral Prometheus metrics at `/metrics`, run Prometheus and Grafana OSS locally
through an optional Docker Compose profile, and provision a dashboard from version-controlled
files.

## Rationale

This makes the MVP demonstrable without sending operational data to a cloud account. Prometheus
stores numeric time-series data and Grafana visualizes it; both are common operational tools.

## Consequences

The API must run on the host at port 8000 while the observability profile is active. The metrics
endpoint is intentionally unauthenticated because Prometheus must scrape it; it exposes only
aggregate service telemetry, not events or database data.
