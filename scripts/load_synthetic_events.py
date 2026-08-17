"""Load the generated synthetic event dataset into local PostgreSQL."""

from __future__ import annotations

from pathlib import Path

from nexus.application.load_events import load_quality_approved_events
from nexus.infrastructure.postgres import PostgresEventRepository, PostgresSettings

DATASET_PATH = Path("data/synthetic/operational_events.csv")


def main() -> None:
    """Persist the locally generated dataset after all initial checks pass."""
    repository = PostgresEventRepository.connect(PostgresSettings.from_environment())
    try:
        result = load_quality_approved_events(DATASET_PATH, repository)
    finally:
        repository.close()

    print(f"Persisted {result.persisted_events} quality-approved events")


if __name__ == "__main__":
    main()
