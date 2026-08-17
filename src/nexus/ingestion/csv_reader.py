"""CSV ingestion for operational events."""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path

from nexus.domain.operational_event import OperationalEvent

REQUIRED_COLUMNS = frozenset(
    {
        "event_id",
        "occurred_at",
        "host",
        "service",
        "metric_name",
        "metric_value",
        "unit",
        "severity",
        "is_anomaly",
    }
)


def ingest_operational_events(path: Path) -> list[OperationalEvent]:
    """Read a CSV dataset and return validated operational events."""
    with path.open(newline="", encoding="utf-8") as input_file:
        reader = csv.DictReader(input_file)
        _validate_columns(reader.fieldnames, path)

        events: list[OperationalEvent] = []
        for row_number, row in enumerate(reader, start=2):
            events.append(_parse_event(row, row_number, path))

    return events


def _validate_columns(columns: list[str] | None, path: Path) -> None:
    if columns is None:
        raise ValueError(f"CSV file has no header: {path}")

    missing_columns = REQUIRED_COLUMNS.difference(columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"CSV file is missing required columns: {missing}")


def _parse_event(row: dict[str, str], row_number: int, path: Path) -> OperationalEvent:
    try:
        return OperationalEvent(
            event_id=row["event_id"],
            occurred_at=datetime.fromisoformat(row["occurred_at"]),
            host=row["host"],
            service=row["service"],
            metric_name=row["metric_name"],
            metric_value=float(row["metric_value"]),
            unit=row["unit"],
            severity=row["severity"],
            is_anomaly=_parse_boolean(row["is_anomaly"]),
        )
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError(f"Invalid operational event at {path}:{row_number}") from error


def _parse_boolean(value: str) -> bool:
    if value == "true":
        return True
    if value == "false":
        return False
    raise ValueError("is_anomaly must be true or false")
