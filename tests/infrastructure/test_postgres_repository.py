"""Integration test for the local PostgreSQL event repository."""

import os

import pytest
from alembic import command
from alembic.config import Config

from nexus.infrastructure.postgres import PostgresEventRepository, PostgresSettings
from nexus.synthetic.generator import generate_operational_events


def upgrade_database() -> None:
    """Apply the production migration path before integration assertions."""
    command.upgrade(Config("alembic.ini"), "head")


@pytest.mark.integration
def test_repository_persists_events_in_postgres() -> None:
    """The local Compose database accepts and stores a generated batch."""
    if os.getenv("RUN_POSTGRES_INTEGRATION") != "1":
        pytest.skip("set RUN_POSTGRES_INTEGRATION=1 to run against local PostgreSQL")

    upgrade_database()
    repository = PostgresEventRepository.connect(PostgresSettings.from_environment())
    try:
        assert repository.upsert_events(generate_operational_events(2)) == 2
    finally:
        repository.close()


@pytest.mark.integration
def test_repository_builds_incident_analytics() -> None:
    """Aggregations expose metric trends and anomaly-derived service indicators."""
    if os.getenv("RUN_POSTGRES_INTEGRATION") != "1":
        pytest.skip("set RUN_POSTGRES_INTEGRATION=1 to run against local PostgreSQL")

    upgrade_database()
    repository = PostgresEventRepository.connect(PostgresSettings.from_environment())
    try:
        repository.upsert_events(generate_operational_events())

        metric_summaries = repository.metric_summaries()
        service_summaries = repository.service_incident_summaries()
    finally:
        repository.close()

    assert len(metric_summaries) == 4
    assert sum(summary.anomaly_count for summary in metric_summaries) == 4
    assert service_summaries
