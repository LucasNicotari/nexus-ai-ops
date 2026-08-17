"""Tests for deterministic synthetic event generation."""

from nexus.synthetic.generator import generate_operational_events


def test_generator_is_deterministic_for_a_seed() -> None:
    """The same seed produces the same event sequence."""
    assert generate_operational_events(5, seed=7) == generate_operational_events(5, seed=7)


def test_generator_creates_expected_event_contract() -> None:
    """The default sample includes normal and anomalous operational signals."""
    events = generate_operational_events()

    assert len(events) == 120
    assert events[0].event_id == "evt-000001"
    assert events[0].occurred_at.isoformat() == "2026-01-01T00:00:00+00:00"
    assert any(event.is_anomaly for event in events)
    assert {event.severity for event in events} >= {"normal", "warning", "critical"}
