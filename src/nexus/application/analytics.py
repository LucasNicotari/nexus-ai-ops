"""Application service for anomaly-derived incident analytics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from nexus.infrastructure.postgres import MetricSummary, ServiceIncidentSummary


class AnalyticsRepository(Protocol):
    """Read capabilities required by the incident analytics workflow."""

    def metric_summaries(self) -> list[MetricSummary]:
        """Return aggregate statistics by metric."""

    def service_incident_summaries(self) -> list[ServiceIncidentSummary]:
        """Return anomaly-derived incident indicators by service."""


@dataclass(frozen=True, slots=True)
class IncidentAnalyticsReport:
    """Read model used by future APIs and dashboards."""

    metric_summaries: list[MetricSummary]
    service_incident_summaries: list[ServiceIncidentSummary]


def build_incident_analytics_report(repository: AnalyticsRepository) -> IncidentAnalyticsReport:
    """Build the current incident analytics read model from persisted events."""
    return IncidentAnalyticsReport(
        metric_summaries=repository.metric_summaries(),
        service_incident_summaries=repository.service_incident_summaries(),
    )
