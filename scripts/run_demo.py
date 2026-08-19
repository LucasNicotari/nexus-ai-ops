"""Prepare a complete local NEXUS demonstration without destructive database resets."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from generate_temporal_training_data import main as generate_temporal_data
from train_and_register_temporal_model import main as train_and_register_model

from nexus.application.load_events import load_quality_approved_events
from nexus.infrastructure.postgres import PostgresEventRepository, PostgresSettings

TEMPORAL_DATASET_PATH = Path("data/synthetic/temporal_training_events.csv")


def main() -> None:
    """Migrate, generate, load, and train the local demonstrator in one command."""
    _apply_migrations()
    generate_temporal_data()

    repository = PostgresEventRepository.connect(PostgresSettings.from_environment())
    try:
        result = load_quality_approved_events(TEMPORAL_DATASET_PATH, repository)
    finally:
        repository.close()

    print(f"Persisted {result.persisted_events} temporal events through the quality gate")
    train_and_register_model()
    print("Demo data is ready. Start the API and observability profile to view Grafana.")


def _apply_migrations() -> None:
    """Apply the reviewed Alembic schema before any database operation."""
    subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], check=True)


if __name__ == "__main__":
    main()
