"""Quality-gated workflow for supervised anomaly-risk prediction."""

from pathlib import Path

from nexus.ingestion.csv_reader import ingest_operational_events
from nexus.ml.risk_prediction import RiskPredictionResult, SupervisedAnomalyRiskClassifier
from nexus.quality.validator import assess_operational_event_quality


def predict_quality_approved_risk(path: Path) -> RiskPredictionResult:
    """Evaluate supervised risk prediction only after quality checks pass."""
    events = ingest_operational_events(path)
    quality_report = assess_operational_event_quality(events)
    if not quality_report.is_valid:
        raise ValueError(
            f"Refusing supervised prediction for {len(quality_report.issues)} quality issue(s)"
        )
    return SupervisedAnomalyRiskClassifier().evaluate(events)
