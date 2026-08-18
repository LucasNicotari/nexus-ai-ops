"""Workflow to run anomaly detection after ingestion and quality assessment."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from nexus.ingestion.csv_reader import ingest_operational_events
from nexus.ml.anomaly_detection import (
    DetectedAnomaly,
    DetectionEvaluation,
    MetricIsolationForestDetector,
    evaluate_detection,
)
from nexus.quality.validator import assess_operational_event_quality


@dataclass(frozen=True, slots=True)
class AnomalyDetectionResult:
    """Predictions and evaluation produced by the baseline detector."""

    predictions: list[DetectedAnomaly]
    evaluation: DetectionEvaluation


def detect_quality_approved_anomalies(path: Path) -> AnomalyDetectionResult:
    """Ingest a batch, enforce quality, and run the Isolation Forest baseline."""
    events = ingest_operational_events(path)
    quality_report = assess_operational_event_quality(events)
    if not quality_report.is_valid:
        raise ValueError(
            f"Refusing anomaly detection for {len(quality_report.issues)} quality issue(s)"
        )

    predictions = MetricIsolationForestDetector().detect(events)
    return AnomalyDetectionResult(
        predictions=predictions, evaluation=evaluate_detection(predictions)
    )
