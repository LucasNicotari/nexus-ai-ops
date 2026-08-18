"""FastAPI application exposing NEXUS read operations."""

from collections.abc import Generator
from dataclasses import asdict

import psycopg
from fastapi import Depends, FastAPI, HTTPException, Query, status

from nexus.api.schemas import (
    HealthResponse,
    MetricSummaryResponse,
    ModelPredictionResponse,
    ModelRunResponse,
    OperationalEventResponse,
    ServiceIncidentSummaryResponse,
)
from nexus.domain.operational_event import OperationalEvent
from nexus.infrastructure.model_registry import PostgresModelRegistry
from nexus.infrastructure.postgres import PostgresEventRepository, PostgresSettings

app = FastAPI(title="NEXUS AI Ops", version="0.1.0")


def get_repository() -> Generator[PostgresEventRepository]:
    """Provide a request-scoped PostgreSQL repository."""
    try:
        repository = PostgresEventRepository.connect(PostgresSettings.from_environment())
    except psycopg.Error as error:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE) from error
    try:
        yield repository
    finally:
        repository.close()


def get_model_registry() -> Generator[PostgresModelRegistry]:
    """Provide a request-scoped registry for persisted ML metadata."""
    try:
        registry = PostgresModelRegistry.connect(PostgresSettings.from_environment())
    except psycopg.Error as error:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE) from error
    try:
        yield registry
    finally:
        registry.close()


@app.get("/health", response_model=HealthResponse)
def health(repository: PostgresEventRepository = Depends(get_repository)) -> HealthResponse:
    """Return service health only when PostgreSQL is reachable."""
    try:
        healthy = repository.is_healthy()
    except psycopg.Error as error:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE) from error

    if not healthy:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE)
    return HealthResponse(status="ok")


@app.get("/events", response_model=list[OperationalEventResponse])
def list_events(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    repository: PostgresEventRepository = Depends(get_repository),
) -> list[OperationalEventResponse]:
    """Return a stable, bounded page of persisted events."""
    return [_event_response(event) for event in repository.list_events(limit=limit, offset=offset)]


@app.get("/analytics/metrics", response_model=list[MetricSummaryResponse])
def metric_summaries(
    repository: PostgresEventRepository = Depends(get_repository),
) -> list[MetricSummaryResponse]:
    """Return aggregate signal quality and anomaly volume by metric."""
    return [MetricSummaryResponse(**asdict(summary)) for summary in repository.metric_summaries()]


@app.get("/analytics/services", response_model=list[ServiceIncidentSummaryResponse])
def service_incident_summaries(
    repository: PostgresEventRepository = Depends(get_repository),
) -> list[ServiceIncidentSummaryResponse]:
    """Return anomaly-derived incident indicators by service."""
    return [
        ServiceIncidentSummaryResponse(**asdict(summary))
        for summary in repository.service_incident_summaries()
    ]


@app.get("/ml/runs", response_model=list[ModelRunResponse])
def list_model_runs(
    limit: int = Query(default=20, ge=1, le=100),
    registry: PostgresModelRegistry = Depends(get_model_registry),
) -> list[ModelRunResponse]:
    """Return persisted model runs and their evaluation evidence."""
    return [ModelRunResponse(**asdict(run)) for run in registry.list_runs(limit=limit)]


@app.get("/ml/runs/{model_run_id}/predictions", response_model=list[ModelPredictionResponse])
def list_model_predictions(
    model_run_id: str,
    limit: int = Query(default=100, ge=1, le=500),
    registry: PostgresModelRegistry = Depends(get_model_registry),
) -> list[ModelPredictionResponse]:
    """Return stored held-out predictions for one model run."""
    try:
        from uuid import UUID

        parsed_model_run_id = UUID(model_run_id)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY) from error
    return [
        ModelPredictionResponse(**asdict(prediction))
        for prediction in registry.list_predictions(parsed_model_run_id, limit=limit)
    ]


def _event_response(event: OperationalEvent) -> OperationalEventResponse:
    return OperationalEventResponse(
        event_id=event.event_id,
        occurred_at=event.occurred_at,
        host=event.host,
        service=event.service,
        metric_name=event.metric_name,
        metric_value=event.metric_value,
        unit=event.unit,
        severity=event.severity,
        is_anomaly=event.is_anomaly,
    )
