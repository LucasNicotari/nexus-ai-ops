"""Tests for the Isolation Forest anomaly detection baseline."""

import pytest

from nexus.ml.anomaly_detection import MetricIsolationForestDetector, evaluate_detection
from nexus.synthetic.generator import generate_operational_events


def test_detector_is_deterministic_for_the_synthetic_dataset() -> None:
    """A fixed random state keeps the baseline reproducible."""
    events = generate_operational_events()

    first_run = MetricIsolationForestDetector().detect(events)
    second_run = MetricIsolationForestDetector().detect(events)

    assert first_run == second_run


def test_detector_flags_expected_synthetic_anomalies() -> None:
    """Injected spikes should be found by the per-metric baseline."""
    predictions = MetricIsolationForestDetector().detect(generate_operational_events())
    evaluation = evaluate_detection(predictions)

    assert evaluation.true_positives == 4
    assert evaluation.recall == 1.0
    assert evaluation.precision >= 0.5


def test_detector_requires_enough_metric_history() -> None:
    """Small samples are not a reliable basis for an Isolation Forest."""
    with pytest.raises(ValueError, match="at least 10 events"):
        MetricIsolationForestDetector().detect(generate_operational_events(9))
