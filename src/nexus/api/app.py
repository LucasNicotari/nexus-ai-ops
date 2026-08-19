"""FastAPI application exposing NEXUS read operations."""

from collections.abc import Generator
from dataclasses import asdict

import psycopg
from fastapi import Depends, FastAPI, HTTPException, Query, status
from prometheus_client import make_asgi_app

from nexus.api.observability import request_observability
from nexus.api.schemas import (
    EventIngestionResponse,
    HealthResponse,
    MetricSummaryResponse,
    ModelPredictionResponse,
    ModelRunResponse,
    OperationalEventRequest,
    OperationalEventResponse,
    ServiceIncidentSummaryResponse,
)
from nexus.api.security import Principal, require_reader
from nexus.domain.operational_event import OperationalEvent
from nexus.infrastructure.model_registry import PostgresModelRegistry
from nexus.infrastructure.postgres import PostgresEventRepository, PostgresSettings
from nexus.quality.validator import assess_operational_event_quality

app = FastAPI(title="NEXUS AI Ops", version="0.1.0")
app.middleware("http")(request_observability)
app.mount("/metrics", make_asgi_app())


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
    principal: Principal = Depends(require_reader),
) -> list[OperationalEventResponse]:
    """Return a stable, bounded page of persisted events."""
    return [_event_response(event) for event in repository.list_events(limit=limit, offset=offset)]


@app.post("/events", response_model=EventIngestionResponse, status_code=status.HTTP_201_CREATED)
def ingest_events(
    events: list[OperationalEventRequest],
    repository: PostgresEventRepository = Depends(get_repository),
    principal: Principal = Depends(require_reader),
) -> EventIngestionResponse:
    """Persist a fully valid operational-event batch through the existing quality contract."""
    domain_events = [OperationalEvent(**event.model_dump()) for event in events]
    report = assess_operational_event_quality(domain_events)
    if not report.is_valid:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=[asdict(issue) for issue in report.issues],
        )
    return EventIngestionResponse(persisted_events=repository.upsert_events(domain_events))


@app.get("/analytics/metrics", response_model=list[MetricSummaryResponse])
def metric_summaries(
    repository: PostgresEventRepository = Depends(get_repository),
    principal: Principal = Depends(require_reader),
) -> list[MetricSummaryResponse]:
    """Return aggregate signal quality and anomaly volume by metric."""
    return [MetricSummaryResponse(**asdict(summary)) for summary in repository.metric_summaries()]


@app.get("/analytics/services", response_model=list[ServiceIncidentSummaryResponse])
def service_incident_summaries(
    repository: PostgresEventRepository = Depends(get_repository),
    principal: Principal = Depends(require_reader),
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
    principal: Principal = Depends(require_reader),
) -> list[ModelRunResponse]:
    """Return persisted model runs and their evaluation evidence."""
    return [ModelRunResponse(**asdict(run)) for run in registry.list_runs(limit=limit)]


@app.get("/ml/runs/{model_run_id}/predictions", response_model=list[ModelPredictionResponse])
def list_model_predictions(
    model_run_id: str,
    limit: int = Query(default=100, ge=1, le=500),
    registry: PostgresModelRegistry = Depends(get_model_registry),
    principal: Principal = Depends(require_reader),
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
