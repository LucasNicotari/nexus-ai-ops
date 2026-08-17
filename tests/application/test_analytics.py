"""Tests for the incident analytics application service."""

from datetime import UTC, datetime

from nexus.application.analytics import build_incident_analytics_report
from nexus.infrastructure.postgres import MetricSummary, ServiceIncidentSummary


class StubAnalyticsRepository:
    """Repository double that supplies stable analytics data."""

    def metric_summaries(self) -> list[MetricSummary]:
        return [
            MetricSummary(
                metric_name="cpu_usage_percent",
                event_count=30,
                average_value=48.5,
                minimum_value=30.0,
                maximum_value=100.0,
                anomaly_count=1,
            )
        ]

    def service_incident_summaries(self) -> list[ServiceIncidentSummary]:
        return [
            ServiceIncidentSummary(
                service="customer-api",
                anomalous_event_count=2,
                critical_event_count=1,
                last_anomaly_at=datetime(2026, 1, 1, tzinfo=UTC),
            )
        ]


def test_build_incident_analytics_report() -> None:
    """The read model exposes metric and service-level views together."""
    report = build_incident_analytics_report(StubAnalyticsRepository())

    assert report.metric_summaries[0].anomaly_count == 1
    assert report.service_incident_summaries[0].service == "customer-api"
