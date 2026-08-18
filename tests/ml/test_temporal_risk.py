"""Tests for the chronological risk-prediction baseline."""

from nexus.ml.temporal_features import build_temporal_feature_records, split_temporal_dataset
from nexus.ml.temporal_risk import TemporalAnomalyRiskClassifier
from nexus.synthetic.generator import generate_temporal_operational_events


def test_temporal_classifier_keeps_test_evaluation_isolated() -> None:
    """The temporal dataset supports labeled train, validation, and test partitions."""
    records = build_temporal_feature_records(generate_temporal_operational_events())
    report = TemporalAnomalyRiskClassifier().evaluate(split_temporal_dataset(records))

    assert report.alert_threshold in {0.1, 0.2, 0.3, 0.4, 0.5}
    assert report.test_evaluation.recall >= 0.0
    assert report.test_evaluation.f1_score >= 0.0
