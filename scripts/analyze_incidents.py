"""Print the current anomaly-derived incident analytics report as JSON."""

from __future__ import annotations

import json
from dataclasses import asdict

from nexus.application.analytics import build_incident_analytics_report
from nexus.infrastructure.postgres import PostgresEventRepository, PostgresSettings


def main() -> None:
    """Read analytics from PostgreSQL and print a portable JSON report."""
    repository = PostgresEventRepository.connect(PostgresSettings.from_environment())
    try:
        report = build_incident_analytics_report(repository)
    finally:
        repository.close()

    print(json.dumps(asdict(report), default=str, indent=2))


if __name__ == "__main__":
    main()
