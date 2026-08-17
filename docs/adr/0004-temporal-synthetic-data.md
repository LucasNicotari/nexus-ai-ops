# ADR 0004: Provide a temporal synthetic dataset alongside the compact fixture

## Context

The 120-event dataset is sufficient for smoke tests, but it is too small and lacks temporal structure for credible model evaluation, forecasting work, or reusable demos.

## Decision

Keep the compact generator unchanged and add a deterministic temporal generator. It emits every metric at five-minute intervals for three days, applies a daily load cycle, and injects recurring degradation windows. Generated files remain outside version control because scripts reproduce them exactly.

## Consequences

The project now has a stable source for analytics, dashboards, APIs, and ML experiments without duplicating event semantics. The scenarios are intentionally synthetic and periodic; they do not represent production traffic or validate a deployed model.
