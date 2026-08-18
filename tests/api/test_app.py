"""Tests for the NEXUS read API."""

from datetime import UTC, datetime
from uuid import UUID

import psycopg
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from nexus.api.app import app, get_model_registry, get_repository
from nexus.domain.operational_event import OperationalEvent
from nexus.infrastructure.model_registry import ModelRunSummary, PersistedModelPrediction
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


class FakeModelRegistry:
    """Registry double for ML-read endpoint tests."""

    model_run_id = UUID("00000000-0000-0000-0000-000000000001")

    def list_runs(self, *, limit: int) -> list[ModelRunSummary]:
        return [
            ModelRunSummary(
                self.model_run_id,
                datetime(2026, 1, 1, tzinfo=UTC),
                "temporal-random-forest-v1",
                "data/models/example.joblib",
                0.4,
                100,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0,
            )
        ]

    def list_predictions(self, model_run_id: UUID, *, limit: int) -> list[PersistedModelPrediction]:
        assert model_run_id == self.model_run_id
        return [PersistedModelPrediction("evt-000001", 0.9, True, True)]


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """Provide an API client backed by deterministic repository responses."""
    monkeypatch.setenv("NEXUS_API_KEYS", "test-reader-key:reader")
    app.dependency_overrides[get_repository] = lambda: FakeRepository()
    app.dependency_overrides[get_model_registry] = lambda: FakeModelRegistry()
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_health_returns_ok_when_database_is_reachable(client: TestClient) -> None:
    assert client.get("/health").json() == {"status": "ok"}


def test_events_are_paginated_and_serialized(client: TestClient) -> None:
    response = client.get("/events?limit=1&offset=0", headers=_reader_headers())

    assert response.status_code == 200
    assert response.json()[0]["event_id"] == "evt-000001"


def test_metric_and_service_analytics_are_exposed(client: TestClient) -> None:
    assert (
        client.get("/analytics/metrics", headers=_reader_headers()).json()[0]["metric_name"]
        == "cpu_usage_percent"
    )
    assert (
        client.get("/analytics/services", headers=_reader_headers()).json()[0]["service"]
        == "customer-api"
    )


def test_persisted_model_results_are_exposed(client: TestClient) -> None:
    run = client.get("/ml/runs", headers=_reader_headers()).json()[0]
    predictions = client.get(
        f"/ml/runs/{run['model_run_id']}/predictions", headers=_reader_headers()
    ).json()

    assert run["test_f1"] == 1.0
    assert predictions[0]["risk_score"] == 0.9


def test_protected_routes_fail_closed_without_api_key(client: TestClient) -> None:
    response = client.get("/events")

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "ApiKey"


def test_protected_routes_reject_unknown_api_key(client: TestClient) -> None:
    assert client.get("/events", headers={"X-NEXUS-API-Key": "wrong-key"}).status_code == 401


def _reader_headers() -> dict[str, str]:
    return {"X-NEXUS-API-Key": "test-reader-key"}


def test_repository_connection_failure_maps_to_service_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Database connection errors are reported as an operational API failure."""

    def fail_connection(*args: object, **kwargs: object) -> None:
        raise psycopg.OperationalError("database unavailable")

    monkeypatch.setattr("nexus.api.app.PostgresEventRepository.connect", fail_connection)

    with pytest.raises(HTTPException, match="503") as error:
        next(get_repository())

    assert error.value.status_code == 503
