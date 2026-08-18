"""Tests for the NEXUS read API."""

from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from nexus.api.app import app, get_repository
from nexus.domain.operational_event import OperationalEvent
from nexus.infrastructure.postgres import MetricSummary, ServiceIncidentSummary


class FakeRepository:
    """Repository double for HTTP boundary tests."""

    def is_healthy(self) -> bool:
        return True

    def list_events(self, *, limit: int, offset: int) -> list[OperationalEvent]:
        event = OperationalEvent(
            event_id="evt-000001",
            occurred_at=datetime(2026, 1, 1, tzinfo=UTC),
            host="app-01",
            service="customer-api",
            metric_name="cpu_usage_percent",
            metric_value=45.0,
            unit="percent",
            severity="normal",
            is_anomaly=False,
        )
        return [event][offset : offset + limit]

    def metric_summaries(self) -> list[MetricSummary]:
        return [MetricSummary("cpu_usage_percent", 1, 45.0, 45.0, 45.0, 0)]

    def service_incident_summaries(self) -> list[ServiceIncidentSummary]:
        return [ServiceIncidentSummary("customer-api", 1, 0, datetime(2026, 1, 1, tzinfo=UTC))]


@pytest.fixture
def client() -> TestClient:
    """Provide an API client backed by deterministic repository responses."""
    app.dependency_overrides[get_repository] = lambda: FakeRepository()
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_health_returns_ok_when_database_is_reachable(client: TestClient) -> None:
    assert client.get("/health").json() == {"status": "ok"}


def test_events_are_paginated_and_serialized(client: TestClient) -> None:
    response = client.get("/events?limit=1&offset=0")

    assert response.status_code == 200
    assert response.json()[0]["event_id"] == "evt-000001"


def test_metric_and_service_analytics_are_exposed(client: TestClient) -> None:
    assert client.get("/analytics/metrics").json()[0]["metric_name"] == "cpu_usage_percent"
    assert client.get("/analytics/services").json()[0]["service"] == "customer-api"
