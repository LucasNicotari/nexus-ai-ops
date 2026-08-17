"""Tests for the supervised anomaly-risk prediction baseline."""

import pytest

from nexus.ml.risk_prediction import SupervisedAnomalyRiskClassifier
from nexus.synthetic.generator import generate_operational_events


def test_risk_classifier_produces_out_of_fold_predictions() -> None:
    result = SupervisedAnomalyRiskClassifier().evaluate(generate_operational_events())

    assert len(result.predictions) == 120
    assert all(0.0 <= item.risk_score <= 1.0 for item in result.predictions)
    assert 0.0 <= result.evaluation.f1_score <= 1.0


def test_risk_classifier_requires_enough_labeled_anomalies() -> None:
    with pytest.raises(ValueError, match="each class needs at least 4 events"):
        SupervisedAnomalyRiskClassifier().evaluate(generate_operational_events(100))
