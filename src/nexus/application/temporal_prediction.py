"""Quality-gated temporal anomaly-risk prediction workflow."""

from pathlib import Path

from nexus.ingestion.csv_reader import ingest_operational_events
from nexus.ml.temporal_features import build_temporal_feature_records, split_temporal_dataset
from nexus.ml.temporal_risk import TemporalAnomalyRiskClassifier, TemporalRiskReport
from nexus.quality.validator import assess_operational_event_quality


def evaluate_temporal_risk(path: Path) -> TemporalRiskReport:
    """Build causal features and evaluate risk on a chronologically isolated test set."""
    events = ingest_operational_events(path)
    quality_report = assess_operational_event_quality(events)
    if not quality_report.is_valid:
        raise ValueError(
            f"Refusing temporal prediction for {len(quality_report.issues)} quality issue(s)"
        )
    records = build_temporal_feature_records(events)
    return TemporalAnomalyRiskClassifier().evaluate(split_temporal_dataset(records))
