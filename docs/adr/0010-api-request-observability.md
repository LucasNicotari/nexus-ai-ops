# ADR 0010: API request observability

## Status

Accepted

## Decision

Every HTTP response carries an `X-Request-ID`. The API accepts a caller-provided value or creates
a UUID, then emits one completion log containing the request ID, method, path, status code and
duration in milliseconds.

## Rationale

Correlation is required before adding dashboards or alerts. This small middleware avoids coupling
the MVP to a vendor while preserving the identifiers a future OpenTelemetry or log platform can
consume.

## Consequences

The middleware does not log request bodies, API keys, or database data. It provides correlation,
not distributed tracing, metrics aggregation, or external log retention.
