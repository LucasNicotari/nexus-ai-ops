"""Run the baseline anomaly detector against the synthetic dataset."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from nexus.application.detect_anomalies import detect_quality_approved_anomalies

DATASET_PATH = Path("data/synthetic/operational_events.csv")


def main() -> None:
    """Print only predicted anomalous events and their evaluation."""
    result = detect_quality_approved_anomalies(DATASET_PATH)
    detected_events = [
        prediction for prediction in result.predictions if prediction.predicted_anomaly
    ]
    print(
        json.dumps(
            {
                "evaluation": asdict(result.evaluation),
                "precision": result.evaluation.precision,
                "recall": result.evaluation.recall,
                "detected_events": [asdict(prediction) for prediction in detected_events],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
