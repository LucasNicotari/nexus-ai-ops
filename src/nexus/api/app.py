"""FastAPI application exposing NEXUS read operations."""

from collections.abc import Generator
from dataclasses import asdict

import psycopg
from fastapi import Depends, FastAPI, HTTPException, Query, status

from nexus.api.schemas import (
    HealthResponse,
    MetricSummaryResponse,
    OperationalEventResponse,
    ServiceIncidentSummaryResponse,
)
from nexus.domain.operational_event import OperationalEvent
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
