"""Integration test for the local PostgreSQL event repository."""

import os

import pytest

from nexus.infrastructure.postgres import PostgresEventRepository, PostgresSettings
from nexus.synthetic.generator import generate_operational_events


@pytest.mark.integration
def test_repository_persists_events_in_postgres() -> None:
    """The local Compose database accepts and stores a generated batch."""
    if os.getenv("RUN_POSTGRES_INTEGRATION") != "1":
        pytest.skip("set RUN_POSTGRES_INTEGRATION=1 to run against local PostgreSQL")

    repository = PostgresEventRepository.connect(PostgresSettings.from_environment())
    try:
        repository.initialize_schema()
        assert repository.upsert_events(generate_operational_events(2)) == 2
    finally:
        repository.close()
