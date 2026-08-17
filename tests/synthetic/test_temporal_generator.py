"""Tests for the temporal synthetic dataset generator."""

from nexus.synthetic.generator import generate_temporal_operational_events


def test_temporal_generator_is_deterministic() -> None:
    """A fixed seed produces the same temporal dataset."""
    assert generate_temporal_operational_events(10) == generate_temporal_operational_events(10)


def test_temporal_generator_emits_all_metrics_and_degradation_windows() -> None:
    """The training dataset has periodic signals and labeled degradation events."""
    events = generate_temporal_operational_events(288)

    assert len(events) == 1_152
    assert {event.metric_name for event in events} == {
        "cpu_usage_percent",
        "memory_usage_percent",
        "http_latency_ms",
        "error_rate_percent",
    }
    assert any(event.is_anomaly for event in events)
    assert any(event.severity == "critical" for event in events)
