"""Train, serialize, and register the temporal anomaly-risk baseline."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import joblib

from nexus.infrastructure.model_registry import ModelRun, PostgresModelRegistry
from nexus.infrastructure.postgres import PostgresSettings
from nexus.ingestion.csv_reader import ingest_operational_events
from nexus.ml.temporal_features import build_temporal_feature_records, split_temporal_dataset
from nexus.ml.temporal_risk import TemporalAnomalyRiskClassifier
from nexus.quality.validator import assess_operational_event_quality

DATASET_PATH = Path("data/synthetic/temporal_training_events.csv")
ARTIFACT_DIRECTORY = Path("data/models")


def main() -> None:
    """Create a repeatable local model run and persist its held-out predictions."""
    events = ingest_operational_events(DATASET_PATH)
    quality_report = assess_operational_event_quality(events)
    if not quality_report.is_valid:
        raise ValueError(
            f"Refusing model training for {len(quality_report.issues)} quality issue(s)"
        )

    split = split_temporal_dataset(build_temporal_feature_records(events))
    classifier = TemporalAnomalyRiskClassifier()
    report = classifier.evaluate(split)
    inference_model = classifier.train_for_inference(
        [*split.train, *split.validation], alert_threshold=report.alert_threshold
    )

    model_run_id = uuid4()
    ARTIFACT_DIRECTORY.mkdir(parents=True, exist_ok=True)
    artifact_path = ARTIFACT_DIRECTORY / f"temporal-risk-{model_run_id}.joblib"
    joblib.dump(inference_model, artifact_path)

    registry = PostgresModelRegistry.connect(PostgresSettings.from_environment())
    try:
        registry.initialize_schema()
        registry.save_run(
            ModelRun(
                model_run_id=model_run_id,
                created_at=datetime.now(UTC),
                model_name="temporal-random-forest-v1",
                artifact_path=str(artifact_path),
                alert_threshold=report.alert_threshold,
                training_event_count=len(split.train) + len(split.validation),
                validation_evaluation=report.validation_evaluation,
                test_evaluation=report.test_evaluation,
            )
        )
        prediction_count = registry.save_predictions(model_run_id, report.test_predictions)
    finally:
        registry.close()

    print(f"Registered model run {model_run_id} with {prediction_count} test predictions")


if __name__ == "__main__":
    main()
