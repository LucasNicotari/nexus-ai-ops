"""Tests for the quality-gated event loading workflow."""

from pathlib import Path

import pytest

from nexus.application.load_events import load_quality_approved_events
from nexus.synthetic.generator import generate_operational_events


class InMemoryEventRepository:
    """Small repository double used to verify application behavior."""

    def __init__(self) -> None:
        self.events: list[object] = []

    def upsert_events(self, events: list[object]) -> int:
        self.events.extend(events)
        return len(events)


def test_load_persists_a_quality_approved_dataset(tmp_path: Path) -> None:
    """Valid events pass from ingestion through persistence."""
    dataset = tmp_path / "events.csv"
    event = generate_operational_events(1)[0]
    dataset.write_text(
        "event_id,occurred_at,host,service,metric_name,metric_value,unit,severity,is_anomaly\n"
        + ",".join(event.to_row().values())
        + "\n",
        encoding="utf-8",
    )
    repository = InMemoryEventRepository()

    result = load_quality_approved_events(dataset, repository)

    assert result.persisted_events == 1
    assert result.quality_report.is_valid
    assert len(repository.events) == 1


def test_load_rejects_a_dataset_with_quality_issues(tmp_path: Path) -> None:
    """Invalid quality batches never reach the repository."""
    dataset = tmp_path / "events.csv"
    row = generate_operational_events(1)[0].to_row()
    row["metric_name"] = "unknown_metric"
    dataset.write_text(
        "event_id,occurred_at,host,service,metric_name,metric_value,unit,severity,is_anomaly\n"
        + ",".join(row.values())
        + "\n",
        encoding="utf-8",
    )
    repository = InMemoryEventRepository()

    with pytest.raises(ValueError, match="quality issue"):
        load_quality_approved_events(dataset, repository)

    assert repository.events == []
