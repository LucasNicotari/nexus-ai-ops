# ADR 0007: Use local joblib artifacts with PostgreSQL model-run metadata

## Context

NEXUS needs reproducible model outputs before it needs a full experiment-tracking platform. The current project has one temporal model and one local environment.

## Decision

Serialize trained inference pipelines as local `joblib` artifacts and register run metadata, evaluation metrics, and held-out predictions in PostgreSQL. Expose persisted metadata through the read API. Defer MLflow until multiple models, parameter experiments, or remote artifact storage exist.

## Consequences

The system can audit what model generated a prediction without making HTTP requests retrain a model. Artifact files remain local and ignored by Git; PostgreSQL provides the queryable audit trail.
