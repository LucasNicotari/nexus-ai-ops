"""Supervised anomaly-risk prediction baseline."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction import DictVectorizer
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.pipeline import Pipeline

from nexus.domain.operational_event import OperationalEvent

_EXPECTED_METRIC_BASELINES = {
    "cpu_usage_percent": 45.0,
    "memory_usage_percent": 58.0,
    "http_latency_ms": 120.0,
    "error_rate_percent": 0.8,
}


@dataclass(frozen=True, slots=True)
class AnomalyRiskPrediction:
    """Out-of-fold risk estimate for one labeled operational event."""

    event_id: str
    risk_score: float
    predicted_anomaly: bool
    expected_anomaly: bool


@dataclass(frozen=True, slots=True)
class PredictionEvaluation:
    """Classification metrics from out-of-fold predictions."""

    true_positives: int
    false_positives: int
    false_negatives: int

    @property
    def precision(self) -> float:
        denominator = self.true_positives + self.false_positives
        return self.true_positives / denominator if denominator else 0.0

    @property
    def recall(self) -> float:
        denominator = self.true_positives + self.false_negatives
        return self.true_positives / denominator if denominator else 0.0

    @property
    def f1_score(self) -> float:
        denominator = self.precision + self.recall
        return 2 * self.precision * self.recall / denominator if denominator else 0.0


@dataclass(frozen=True, slots=True)
class RiskPredictionResult:
    """Predictions and evaluation from the supervised baseline."""

    predictions: list[AnomalyRiskPrediction]
    evaluation: PredictionEvaluation


class SupervisedAnomalyRiskClassifier:
    """Estimate anomaly risk from labeled synthetic operational events."""

    def __init__(
        self, *, random_state: int = 42, folds: int = 4, risk_threshold: float = 0.2
    ) -> None:
        self._random_state = random_state
        self._folds = folds
        self._risk_threshold = risk_threshold

    def evaluate(self, events: Sequence[OperationalEvent]) -> RiskPredictionResult:
        labels = [event.is_anomaly for event in events]
        if min(sum(labels), len(labels) - sum(labels)) < self._folds:
            raise ValueError(
                f"each class needs at least {self._folds} events for stratified evaluation"
            )
        probabilities = cross_val_predict(
            self._build_pipeline(),
            [_features_for(event) for event in events],
            labels,
            cv=StratifiedKFold(n_splits=self._folds, shuffle=True, random_state=self._random_state),
            method="predict_proba",
        )[:, 1]
        predictions = [
            AnomalyRiskPrediction(
                event_id=event.event_id,
                risk_score=round(float(probability), 6),
                predicted_anomaly=bool(probability >= self._risk_threshold),
                expected_anomaly=event.is_anomaly,
            )
            for event, probability in zip(events, probabilities, strict=True)
        ]
        return RiskPredictionResult(predictions, evaluate_predictions(predictions))

    def _build_pipeline(self) -> Pipeline:
        return Pipeline(
            [
                ("features", DictVectorizer(sparse=True)),
                (
                    "classifier",
                    RandomForestClassifier(
                        n_estimators=300,
                        class_weight="balanced",
                        min_samples_leaf=2,
                        random_state=self._random_state,
                    ),
                ),
            ]
        )


def evaluate_predictions(predictions: Sequence[AnomalyRiskPrediction]) -> PredictionEvaluation:
    """Calculate classification metrics from labeled predictions."""
    true_positives = int(
        sum(item.predicted_anomaly and item.expected_anomaly for item in predictions)
    )
    false_positives = int(
        sum(item.predicted_anomaly and not item.expected_anomaly for item in predictions)
    )
    false_negatives = int(
        sum(not item.predicted_anomaly and item.expected_anomaly for item in predictions)
    )
    return PredictionEvaluation(true_positives, false_positives, false_negatives)


def _features_for(event: OperationalEvent) -> dict[str, float | str]:
    baseline = _EXPECTED_METRIC_BASELINES[event.metric_name]
    return {
        "metric_name": event.metric_name,
        "metric_value": event.metric_value,
        "relative_to_baseline": event.metric_value / baseline,
        "service": event.service,
        "host": event.host,
    }
