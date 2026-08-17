"""Evaluate supervised anomaly-risk prediction on synthetic labeled data."""

import json
from dataclasses import asdict
from pathlib import Path

from nexus.application.predict_risk import predict_quality_approved_risk


def main() -> None:
    result = predict_quality_approved_risk(Path("data/synthetic/operational_events.csv"))
    high_risk_events = [item for item in result.predictions if item.predicted_anomaly]
    print(
        json.dumps(
            {
                "evaluation": asdict(result.evaluation),
                "precision": result.evaluation.precision,
                "recall": result.evaluation.recall,
                "f1_score": result.evaluation.f1_score,
                "high_risk_events": [asdict(item) for item in high_risk_events],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
