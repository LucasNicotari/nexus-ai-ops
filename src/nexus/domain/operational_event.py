"""Domain contract for synthetic IT operational events."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class OperationalEvent:
    """A single measured signal from an IT operation."""

    event_id: str
    occurred_at: datetime
    host: str
    service: str
    metric_name: str
    metric_value: float
    unit: str
    severity: str
    is_anomaly: bool

    def __post_init__(self) -> None:
        """Reject invalid measurements at the domain boundary."""
        if not self.event_id:
            raise ValueError("event_id must not be empty")
        if self.occurred_at.tzinfo is None:
            raise ValueError("occurred_at must include timezone information")
        if self.metric_value < 0:
            raise ValueError("metric_value must be non-negative")
        if self.severity not in {"normal", "warning", "critical"}:
            raise ValueError("severity must be normal, warning, or critical")

    def to_row(self) -> dict[str, str]:
        """Convert the event into a CSV-compatible row."""
        return {
            "event_id": self.event_id,
            "occurred_at": self.occurred_at.isoformat(),
            "host": self.host,
            "service": self.service,
            "metric_name": self.metric_name,
            "metric_value": f"{self.metric_value:.2f}",
            "unit": self.unit,
            "severity": self.severity,
            "is_anomaly": str(self.is_anomaly).lower(),
        }
