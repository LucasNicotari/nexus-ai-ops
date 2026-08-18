"""Load quality-approved operational events into persistent storage."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from nexus.domain.operational_event import OperationalEvent
from nexus.ingestion.csv_reader import ingest_operational_events
from nexus.quality.validator import QualityReport, assess_operational_event_quality


class EventRepository(Protocol):
    """Persistence capability needed by the event loading workflow."""

    def initialize_schema(self) -> None:
        """Prepare the event storage structure."""

    def upsert_events(self, events: list[OperationalEvent]) -> int:
        """Store a batch of validated events."""


@dataclass(frozen=True, slots=True)
class LoadResult:
    """Outcome of loading a validated event batch."""

    persisted_events: int
    quality_report: QualityReport


def load_quality_approved_events(path: Path, repository: EventRepository) -> LoadResult:
    """Ingest, assess, and persist a CSV batch only when quality checks pass."""
    events = ingest_operational_events(path)
    quality_report = assess_operational_event_quality(events)

    if not quality_report.is_valid:
        raise ValueError(
            f"Refusing to persist a batch with {len(quality_report.issues)} quality issue(s)"
        )

    repository.initialize_schema()
    persisted_events = repository.upsert_events(events)
    return LoadResult(persisted_events=persisted_events, quality_report=quality_report)
