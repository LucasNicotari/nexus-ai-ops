"""PostgreSQL persistence adapter for operational events."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Sequence

import psycopg

from nexus.domain.operational_event import OperationalEvent

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS operational_events (
    event_id TEXT PRIMARY KEY,
    occurred_at TIMESTAMPTZ NOT NULL,
    host TEXT NOT NULL,
    service TEXT NOT NULL,
    metric_name TEXT NOT NULL,
    metric_value DOUBLE PRECISION NOT NULL CHECK (metric_value >= 0),
    unit TEXT NOT NULL,
    severity TEXT NOT NULL CHECK (severity IN ('normal', 'warning', 'critical')),
    is_anomaly BOOLEAN NOT NULL
);
"""

_UPSERT_SQL = """
INSERT INTO operational_events (
    event_id, occurred_at, host, service, metric_name, metric_value, unit, severity, is_anomaly
) VALUES (
    %(event_id)s, %(occurred_at)s, %(host)s, %(service)s, %(metric_name)s,
    %(metric_value)s, %(unit)s, %(severity)s, %(is_anomaly)s
)
ON CONFLICT (event_id) DO UPDATE SET
    occurred_at = EXCLUDED.occurred_at,
    host = EXCLUDED.host,
    service = EXCLUDED.service,
    metric_name = EXCLUDED.metric_name,
    metric_value = EXCLUDED.metric_value,
    unit = EXCLUDED.unit,
    severity = EXCLUDED.severity,
    is_anomaly = EXCLUDED.is_anomaly;
"""


@dataclass(frozen=True, slots=True)
class PostgresSettings:
    """Connection settings for the local PostgreSQL service."""

    database: str
    user: str
    password: str
    host: str
    port: int

    @classmethod
    def from_environment(cls) -> PostgresSettings:
        """Load local connection settings without embedding secrets in code."""
        return cls(
            database=os.getenv("POSTGRES_DB", "nexus"),
            user=os.getenv("POSTGRES_USER", "nexus"),
            password=os.getenv("POSTGRES_PASSWORD", "change-me-for-local-development"),
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=int(os.getenv("POSTGRES_PORT", "5432")),
        )

    def connection_string(self) -> str:
        """Return a libpq-compatible connection string."""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


class PostgresEventRepository:
    """Persist operational events in PostgreSQL."""

    def __init__(self, connection: psycopg.Connection[object]) -> None:
        self._connection = connection

    @classmethod
    def connect(cls, settings: PostgresSettings) -> PostgresEventRepository:
        """Create a repository backed by the configured PostgreSQL service."""
        return cls(psycopg.connect(settings.connection_string()))

    def initialize_schema(self) -> None:
        """Create the minimal event table when it does not exist."""
        with self._connection.cursor() as cursor:
            cursor.execute(_SCHEMA_SQL)
        self._connection.commit()

    def upsert_events(self, events: Sequence[OperationalEvent]) -> int:
        """Insert or update a batch of events by event identifier."""
        if not events:
            return 0

        rows = [
            {
                "event_id": event.event_id,
                "occurred_at": event.occurred_at,
                "host": event.host,
                "service": event.service,
                "metric_name": event.metric_name,
                "metric_value": event.metric_value,
                "unit": event.unit,
                "severity": event.severity,
                "is_anomaly": event.is_anomaly,
            }
            for event in events
        ]
        with self._connection.cursor() as cursor:
            cursor.executemany(_UPSERT_SQL, rows)
        self._connection.commit()
        return len(rows)

    def close(self) -> None:
        """Release the database connection."""
        self._connection.close()
