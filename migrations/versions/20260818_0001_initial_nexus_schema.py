"""Create the initial NEXUS operational and model registry schema."""

from alembic import op

revision = "20260818_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create tables and indexes; existing local tables are preserved."""
    op.execute("""
        CREATE TABLE IF NOT EXISTS operational_events (
            event_id TEXT PRIMARY KEY, occurred_at TIMESTAMPTZ NOT NULL, host TEXT NOT NULL,
            service TEXT NOT NULL, metric_name TEXT NOT NULL,
            metric_value DOUBLE PRECISION NOT NULL CHECK (metric_value >= 0), unit TEXT NOT NULL,
            severity TEXT NOT NULL CHECK (severity IN ('normal', 'warning', 'critical')),
            is_anomaly BOOLEAN NOT NULL
        );
    """)
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_operational_events_occurred_at "
        "ON operational_events (occurred_at);"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_operational_events_service_anomaly "
        "ON operational_events (service, is_anomaly);"
    )
    op.execute("""
        CREATE TABLE IF NOT EXISTS model_runs (
            model_run_id UUID PRIMARY KEY, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            model_name TEXT NOT NULL, artifact_path TEXT NOT NULL,
            alert_threshold DOUBLE PRECISION NOT NULL,
            training_event_count INTEGER NOT NULL, validation_precision DOUBLE PRECISION NOT NULL,
            validation_recall DOUBLE PRECISION NOT NULL, validation_f1 DOUBLE PRECISION NOT NULL,
            test_precision DOUBLE PRECISION NOT NULL, test_recall DOUBLE PRECISION NOT NULL,
            test_f1 DOUBLE PRECISION NOT NULL
        );
    """)
    op.execute("""
        CREATE TABLE IF NOT EXISTS model_predictions (
            model_run_id UUID NOT NULL REFERENCES model_runs(model_run_id), event_id TEXT NOT NULL,
            risk_score DOUBLE PRECISION NOT NULL, predicted_anomaly BOOLEAN NOT NULL,
            expected_anomaly BOOLEAN, PRIMARY KEY (model_run_id, event_id)
        );
    """)
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_model_predictions_run_risk "
        "ON model_predictions (model_run_id, risk_score DESC);"
    )


def downgrade() -> None:
    """Remove tables in foreign-key dependency order."""
    op.execute("DROP TABLE IF EXISTS model_predictions;")
    op.execute("DROP TABLE IF EXISTS model_runs;")
    op.execute("DROP TABLE IF EXISTS operational_events;")
