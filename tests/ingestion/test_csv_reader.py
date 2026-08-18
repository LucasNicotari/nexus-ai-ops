"""Tests for operational event CSV ingestion."""

from pathlib import Path

import pytest

from nexus.ingestion.csv_reader import ingest_operational_events
from nexus.synthetic.generator import generate_operational_events


def test_ingestion_reads_generated_events(tmp_path: Path) -> None:
    """A generated CSV can be restored into the domain contract."""
    events = generate_operational_events(2)
    dataset = tmp_path / "events.csv"
    dataset.write_text(
        "event_id,occurred_at,host,service,metric_name,metric_value,unit,severity,is_anomaly\n"
        + "\n".join(",".join(event.to_row().values()) for event in events)
        + "\n",
        encoding="utf-8",
    )

    ingested_events = ingest_operational_events(dataset)

    assert ingested_events == events


def test_ingestion_rejects_csv_with_missing_columns(tmp_path: Path) -> None:
    """The reader explains the structural contract violation."""
    dataset = tmp_path / "incomplete.csv"
    dataset.write_text("event_id,host\nevt-000001,app-01\n", encoding="utf-8")

    with pytest.raises(ValueError, match="missing required columns:.*occurred_at"):
        ingest_operational_events(dataset)


def test_ingestion_reports_invalid_rows(tmp_path: Path) -> None:
    """Malformed values include the file location and row number in the error."""
    dataset = tmp_path / "invalid.csv"
    dataset.write_text(
        "event_id,occurred_at,host,service,metric_name,metric_value,unit,severity,is_anomaly\n"
        "evt-000001,2026-01-01T00:00:00+00:00,app-01,customer-api,cpu_usage_percent,45,percent,normal,yes\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match=r"invalid.csv:2"):
        ingest_operational_events(dataset)
