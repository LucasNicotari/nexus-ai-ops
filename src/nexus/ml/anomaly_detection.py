"""Baseline anomaly detection for operational metrics."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Sequence

from sklearn.ensemble import IsolationForest

from nexus.domain.operational_event import OperationalEvent


@dataclass(frozen=True, slots=True)
class DetectedAnomaly:
    """Isolation Forest prediction associated with one operational event."""

    event_id: str
    metric_name: str
    anomaly_score: float
    predicted_anomaly: bool
    expected_anomaly: bool


@dataclass(frozen=True, slots=True)
class DetectionEvaluation:
    """Basic comparison of synthetic labels and model predictions."""

    true_positives: int
    false_positives: int
    false_negatives: int

    @property
    def precision(self) -> float:
        """Return the fraction of predicted anomalies that were expected anomalies."""
        denominator = self.true_positives + self.false_positives
        return self.true_positives / denominator if denominator else 0.0

    @property
    def recall(self) -> float:
        """Return the fraction of expected anomalies detected by the model."""
        denominator = self.true_positives + self.false_negatives
        return self.true_positives / denominator if denominator else 0.0


class MetricIsolationForestDetector:
    """Fit one Isolation Forest per metric to preserve measurement context."""

    def __init__(self, *, contamination: float = 0.05, random_state: int = 42) -> None:
        if not 0 < contamination <= 0.5:
            raise ValueError("contamination must be greater than zero and at most 0.5")
        self._contamination = contamination
        self._random_state = random_state

    def detect(self, events: Sequence[OperationalEvent]) -> list[DetectedAnomaly]:
        """Return deterministic anomaly predictions for a quality-approved event batch."""
        events_by_metric: dict[str, list[OperationalEvent]] = defaultdict(list)
        for event in events:
            events_by_metric[event.metric_name].append(event)

        predictions: dict[str, DetectedAnomaly] = {}
        for metric_name, metric_events in events_by_metric.items():
            if len(metric_events) < 10:
                raise ValueError(
                    f"metric {metric_name} needs at least 10 events for anomaly detection"
                )

            model = IsolationForest(
                contamination=self._contamination,
                random_state=self._random_state,
            )
            feature_values = [[event.metric_value] for event in metric_events]
            predicted_labels = model.fit_predict(feature_values)
            anomaly_scores = -model.decision_function(feature_values)

            for event, label, score in zip(
                metric_events, predicted_labels, anomaly_scores, strict=True
            ):
                predictions[event.event_id] = DetectedAnomaly(
                    event_id=event.event_id,
                    metric_name=metric_name,
                    anomaly_score=round(float(score), 6),
                    predicted_anomaly=bool(label == -1),
                    expected_anomaly=event.is_anomaly,
                )

        return [predictions[event.event_id] for event in events]


def evaluate_detection(predictions: Sequence[DetectedAnomaly]) -> DetectionEvaluation:
    """Evaluate predictions against synthetic labels without using them for training."""
    true_positives = int(
        sum(
            prediction.predicted_anomaly and prediction.expected_anomaly
            for prediction in predictions
        )
    )
    false_positives = int(
        sum(
            prediction.predicted_anomaly and not prediction.expected_anomaly
            for prediction in predictions
        )
    )
    false_negatives = int(
        sum(
            not prediction.predicted_anomaly and prediction.expected_anomaly
            for prediction in predictions
        )
    )
    return DetectionEvaluation(
        true_positives=true_positives,
        false_positives=false_positives,
        false_negatives=false_negatives,
    )
