"""Deterministic generator for synthetic IT operational events."""

from __future__ import annotations

import random
from datetime import UTC, datetime, timedelta

from nexus.domain.operational_event import OperationalEvent

DEFAULT_START_AT = datetime(2026, 1, 1, tzinfo=UTC)

_METRICS: tuple[tuple[str, str, float, float], ...] = (
    ("cpu_usage_percent", "percent", 45.0, 12.0),
    ("memory_usage_percent", "percent", 58.0, 10.0),
    ("http_latency_ms", "milliseconds", 120.0, 35.0),
    ("error_rate_percent", "percent", 0.8, 0.5),
)
_HOSTS: tuple[tuple[str, str], ...] = (
    ("app-01", "customer-api"),
    ("app-02", "customer-api"),
    ("worker-01", "billing-worker"),
)


def generate_operational_events(
    event_count: int = 120,
    *,
    seed: int = 42,
    start_at: datetime = DEFAULT_START_AT,
) -> list[OperationalEvent]:
    """Generate reproducible operational events with periodic anomalies."""
    if event_count < 1:
        raise ValueError("event_count must be greater than zero")
    if start_at.tzinfo is None:
        raise ValueError("start_at must include timezone information")

    generator = random.Random(seed)
    events: list[OperationalEvent] = []

    for index in range(event_count):
        metric_name, unit, baseline, variation = _METRICS[index % len(_METRICS)]
        host, service = _HOSTS[generator.randrange(len(_HOSTS))]
        is_anomaly = (index + 1) % 29 == 0
        metric_value = baseline + generator.uniform(-variation, variation)

        if is_anomaly:
            metric_value = baseline + (variation * generator.uniform(4.0, 6.0))

        severity = (
            "critical" if is_anomaly and metric_value > baseline + (variation * 5) else "warning"
        )
        if not is_anomaly:
            severity = "normal"

        events.append(
            OperationalEvent(
                event_id=f"evt-{index + 1:06d}",
                occurred_at=start_at + timedelta(minutes=index),
                host=host,
                service=service,
                metric_name=metric_name,
                metric_value=round(metric_value, 2),
                unit=unit,
                severity=severity,
                is_anomaly=is_anomaly,
            )
        )

    return events
