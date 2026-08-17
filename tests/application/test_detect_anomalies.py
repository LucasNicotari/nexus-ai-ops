"""Tests for the quality-gated anomaly detection workflow."""

from pathlib import Path

from nexus.application.detect_anomalies import detect_quality_approved_anomalies
from nexus.synthetic.generator import generate_operational_events


def test_detection_workflow_returns_predictions_and_evaluation(tmp_path: Path) -> None:
    """The application workflow runs after a valid ingestion and quality step."""
    events = generate_operational_events()
    dataset = tmp_path / "events.csv"
    dataset.write_text(
        "event_id,occurred_at,host,service,metric_name,metric_value,unit,severity,is_anomaly\n"
        + "\n".join(",".join(event.to_row().values()) for event in events)
        + "\n",
        encoding="utf-8",
    )

    result = detect_quality_approved_anomalies(dataset)

    assert len(result.predictions) == 120
    assert result.evaluation.true_positives == 4
