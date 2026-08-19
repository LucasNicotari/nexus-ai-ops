# ADR 0013: Repeatable local demonstration setup

## Status

Accepted

## Decision

Provide `scripts/run_demo.py` to apply migrations, generate the temporal dataset, load it through
the standard quality use case, and register a temporal model run.

## Rationale

Portfolio demonstrations need visible, reproducible data. Manual commands are easy to execute in
the wrong order and previously loaded only the short dataset rather than the temporal dataset used
by the ML pipeline.

## Consequences

The script does not reset PostgreSQL or remove model artifacts. Event loading is idempotent by
event ID, but each run intentionally creates a new registered model run and local artifact.
