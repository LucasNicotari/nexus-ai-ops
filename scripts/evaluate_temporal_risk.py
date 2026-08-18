"""Evaluate temporal anomaly risk on a chronologically isolated test set."""

import json
from dataclasses import asdict
from pathlib import Path

from nexus.application.temporal_prediction import evaluate_temporal_risk


def main() -> None:
    report = evaluate_temporal_risk(Path("data/synthetic/temporal_training_events.csv"))
    print(
        json.dumps(
            {
                "alert_threshold": report.alert_threshold,
                "validation": asdict(report.validation_evaluation),
                "validation_f1": report.validation_evaluation.f1_score,
                "test": asdict(report.test_evaluation),
                "test_f1": report.test_evaluation.f1_score,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
