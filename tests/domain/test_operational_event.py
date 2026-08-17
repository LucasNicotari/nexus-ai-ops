"""Tests for the operational event contract."""

from datetime import UTC, datetime

import pytest

from nexus.domain.operational_event import OperationalEvent


def test_event_rejects_a_naive_timestamp() -> None:
    """Operational events require an explicit timezone."""
    with pytest.raises(ValueError, match="timezone"):
        OperationalEvent(
            event_id="evt-000001",
            occurred_at=datetime(2026, 1, 1),
            host="app-01",
            service="customer-api",
            metric_name="cpu_usage_percent",
            metric_value=45.0,
            unit="percent",
            severity="normal",
            is_anomaly=False,
        )


def test_event_converts_to_a_serializable_row() -> None:
    """CSV output preserves the public event contract."""
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

    assert event.to_row()["occurred_at"] == "2026-01-01T00:00:00+00:00"
    assert event.to_row()["is_anomaly"] == "false"
