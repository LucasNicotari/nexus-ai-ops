"""Temporal anomaly-risk training and evaluation workflow."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction import DictVectorizer
from sklearn.pipeline import Pipeline

from nexus.ml.risk_prediction import PredictionEvaluation
from nexus.ml.temporal_features import TemporalDatasetSplit, TemporalFeatureRecord


@dataclass(frozen=True, slots=True)
class TemporalRiskPrediction:
    """Risk score produced for a chronologically held-out event."""

    event_id: str
    risk_score: float
    predicted_anomaly: bool
    expected_anomaly: bool


@dataclass(frozen=True, slots=True)
class TemporalRiskReport:
    """Validation-selected threshold and final isolated test evaluation."""

    alert_threshold: float
    validation_evaluation: PredictionEvaluation
    test_evaluation: PredictionEvaluation
    test_predictions: list[TemporalRiskPrediction]


class TemporalAnomalyRiskClassifier:
    """Train on the past, select on validation, and evaluate only on future data."""

    def __init__(self, *, random_state: int = 42) -> None:
        self._random_state = random_state

    def evaluate(self, split: TemporalDatasetSplit) -> TemporalRiskReport:
        """Return a test report without using test labels for model selection."""
        self._validate_partition_labels(split.train, "train")
        self._validate_partition_labels(split.validation, "validation")
        self._validate_partition_labels(split.test, "test")

        validation_model = self._build_pipeline()
        validation_model.fit(_features_for_all(split.train), _labels_for_all(split.train))
        validation_scores = validation_model.predict_proba(_features_for_all(split.validation))[
            :, 1
        ]
        threshold = _select_alert_threshold(split.validation, validation_scores)
        validation_predictions = _predictions_for(split.validation, validation_scores, threshold)

        final_model = self._build_pipeline()
        train_and_validation = [*split.train, *split.validation]
        final_model.fit(
            _features_for_all(train_and_validation), _labels_for_all(train_and_validation)
        )
        test_scores = final_model.predict_proba(_features_for_all(split.test))[:, 1]
        test_predictions = _predictions_for(split.test, test_scores, threshold)

        return TemporalRiskReport(
            alert_threshold=threshold,
            validation_evaluation=_evaluate(validation_predictions),
            test_evaluation=_evaluate(test_predictions),
            test_predictions=test_predictions,
        )

    def _build_pipeline(self) -> Pipeline:
        return Pipeline(
            [
                ("features", DictVectorizer(sparse=True)),
                (
                    "classifier",
                    RandomForestClassifier(
                        n_estimators=300,
                        class_weight="balanced",
                        min_samples_leaf=3,
                        random_state=self._random_state,
                    ),
                ),
            ]
        )

    @staticmethod
    def _validate_partition_labels(records: Sequence[TemporalFeatureRecord], name: str) -> None:
        labels = _labels_for_all(records)
        if not records or not any(labels) or all(labels):
            raise ValueError(f"{name} partition must contain both anomaly classes")


def _features_for_all(records: Sequence[TemporalFeatureRecord]) -> list[dict[str, float | str]]:
    return [
        {
            "metric_name": record.event.metric_name,
            "metric_value": record.event.metric_value,
            "service": record.event.service,
            "host": record.event.host,
            "lag_value": record.lag_value,
            "rolling_mean": record.rolling_mean,
            "rolling_standard_deviation": record.rolling_standard_deviation,
            "deviation_from_mean": record.deviation_from_mean,
            "hour_sin": record.hour_sin,
            "hour_cos": record.hour_cos,
        }
        for record in records
    ]


def _labels_for_all(records: Sequence[TemporalFeatureRecord]) -> list[bool]:
    return [record.event.is_anomaly for record in records]


def _select_alert_threshold(
    records: Sequence[TemporalFeatureRecord], scores: Sequence[float]
) -> float:
    candidates = (0.1, 0.2, 0.3, 0.4, 0.5)
    evaluations = [
        (threshold, _evaluate(_predictions_for(records, scores, threshold)))
        for threshold in candidates
    ]
    return max(
        evaluations,
        key=lambda item: (item[1].f1_score, item[1].recall, -item[0]),
    )[0]


def _predictions_for(
    records: Sequence[TemporalFeatureRecord], scores: Sequence[float], threshold: float
) -> list[TemporalRiskPrediction]:
    return [
        TemporalRiskPrediction(
            event_id=record.event.event_id,
            risk_score=round(float(score), 6),
            predicted_anomaly=bool(score >= threshold),
            expected_anomaly=record.event.is_anomaly,
        )
        for record, score in zip(records, scores, strict=True)
    ]


def _evaluate(predictions: Sequence[TemporalRiskPrediction]) -> PredictionEvaluation:
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
