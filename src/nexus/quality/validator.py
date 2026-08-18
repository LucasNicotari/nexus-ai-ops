"""Quality rules for validated operational events."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from nexus.domain.operational_event import OperationalEvent

_METRIC_BOUNDS: dict[str, tuple[float, float]] = {
    "cpu_usage_percent": (0.0, 100.0),
    "memory_usage_percent": (0.0, 100.0),
    "http_latency_ms": (0.0, 5_000.0),
    "error_rate_percent": (0.0, 100.0),
}


@dataclass(frozen=True, slots=True)
class QualityIssue:
    """A non-structural problem found in an operational event."""

    code: str
    event_id: str
    message: str


@dataclass(frozen=True, slots=True)
class QualityReport:
    """Summary of data quality checks for a batch of operational events."""

    total_events: int
    issues: tuple[QualityIssue, ...]

    @property
    def is_valid(self) -> bool:
        """Return whether the assessed batch has no quality issues."""
        return not self.issues


def assess_operational_event_quality(events: Sequence[OperationalEvent]) -> QualityReport:
    """Assess identifier uniqueness, timestamp ordering, and metric ranges."""
    issues: list[QualityIssue] = []
    event_ids: set[str] = set()
    previous_timestamp = None

    for event in events:
        if event.event_id in event_ids:
            issues.append(
                QualityIssue(
                    code="duplicate_event_id",
                    event_id=event.event_id,
                    message="event_id must be unique within a batch",
                )
            )
        event_ids.add(event.event_id)

        if previous_timestamp is not None and event.occurred_at < previous_timestamp:
            issues.append(
                QualityIssue(
                    code="timestamp_out_of_order",
                    event_id=event.event_id,
                    message="occurred_at must not be earlier than the previous event",
                )
            )
        previous_timestamp = event.occurred_at

        bounds = _METRIC_BOUNDS.get(event.metric_name)
        if bounds is None:
            issues.append(
                QualityIssue(
                    code="unknown_metric",
                    event_id=event.event_id,
                    message=f"metric_name is not supported: {event.metric_name}",
                )
            )
        elif not bounds[0] <= event.metric_value <= bounds[1]:
            issues.append(
                QualityIssue(
                    code="metric_value_out_of_range",
                    event_id=event.event_id,
                    message=(
                        f"metric_value must be between {bounds[0]:.0f} and {bounds[1]:.0f} "
                        f"for {event.metric_name}"
                    ),
                )
            )

    return QualityReport(total_events=len(events), issues=tuple(issues))
