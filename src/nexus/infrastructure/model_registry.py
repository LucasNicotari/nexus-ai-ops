"""Local PostgreSQL registry for model runs and persisted predictions."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Sequence
from uuid import UUID

import psycopg

from nexus.infrastructure.postgres import PostgresSettings
from nexus.ml.risk_prediction import PredictionEvaluation
from nexus.ml.temporal_risk import TemporalRiskPrediction

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS model_runs (
    model_run_id UUID PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    model_name TEXT NOT NULL,
    artifact_path TEXT NOT NULL,
    alert_threshold DOUBLE PRECISION NOT NULL,
    training_event_count INTEGER NOT NULL,
    validation_precision DOUBLE PRECISION NOT NULL,
    validation_recall DOUBLE PRECISION NOT NULL,
    validation_f1 DOUBLE PRECISION NOT NULL,
    test_precision DOUBLE PRECISION NOT NULL,
    test_recall DOUBLE PRECISION NOT NULL,
    test_f1 DOUBLE PRECISION NOT NULL
);

CREATE TABLE IF NOT EXISTS model_predictions (
    model_run_id UUID NOT NULL REFERENCES model_runs(model_run_id),
    event_id TEXT NOT NULL,
    risk_score DOUBLE PRECISION NOT NULL,
    predicted_anomaly BOOLEAN NOT NULL,
    expected_anomaly BOOLEAN,
    PRIMARY KEY (model_run_id, event_id)
);
"""


@dataclass(frozen=True, slots=True)
class ModelRun:
    """Metadata for one reproducible local model training execution."""

    model_run_id: UUID
    created_at: datetime
    model_name: str
    artifact_path: str
    alert_threshold: float
    training_event_count: int
    validation_evaluation: PredictionEvaluation
    test_evaluation: PredictionEvaluation


@dataclass(frozen=True, slots=True)
class PersistedModelPrediction:
    """Prediction result stored for a concrete model run."""

    event_id: str
    risk_score: float
    predicted_anomaly: bool
    expected_anomaly: bool | None


@dataclass(frozen=True, slots=True)
class ModelRunSummary:
    """Read model for a registered run and its stored evaluation metrics."""

    model_run_id: UUID
    created_at: datetime
    model_name: str
    artifact_path: str
    alert_threshold: float
    training_event_count: int
    validation_precision: float
    validation_recall: float
    validation_f1: float
    test_precision: float
    test_recall: float
    test_f1: float


class PostgresModelRegistry:
    """Persist local model metadata and inference outputs in PostgreSQL."""

    def __init__(self, connection: psycopg.Connection[object]) -> None:
        self._connection = connection

    @classmethod
    def connect(cls, settings: PostgresSettings) -> PostgresModelRegistry:
        """Create a registry using the project's local PostgreSQL connection settings."""
        return cls(psycopg.connect(settings.connection_string()))

    def initialize_schema(self) -> None:
        """Create the model registry tables if they do not already exist."""
        with self._connection.cursor() as cursor:
            cursor.execute(_SCHEMA_SQL)
        self._connection.commit()

    def save_run(self, model_run: ModelRun) -> None:
        """Persist model metadata and validation evidence."""
        query = """
        INSERT INTO model_runs (
            model_run_id, created_at, model_name, artifact_path, alert_threshold,
            training_event_count, validation_precision, validation_recall, validation_f1,
            test_precision, test_recall, test_f1
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        """
        with self._connection.cursor() as cursor:
            cursor.execute(
                query,
                (
                    model_run.model_run_id,
                    model_run.created_at,
                    model_run.model_name,
                    model_run.artifact_path,
                    model_run.alert_threshold,
                    model_run.training_event_count,
                    model_run.validation_evaluation.precision,
                    model_run.validation_evaluation.recall,
                    model_run.validation_evaluation.f1_score,
                    model_run.test_evaluation.precision,
                    model_run.test_evaluation.recall,
                    model_run.test_evaluation.f1_score,
                ),
            )
        self._connection.commit()

    def save_predictions(
        self, model_run_id: UUID, predictions: Sequence[TemporalRiskPrediction]
    ) -> int:
        """Persist final held-out predictions for a registered model run."""
        if not predictions:
            return 0
        query = """
        INSERT INTO model_predictions (
            model_run_id, event_id, risk_score, predicted_anomaly, expected_anomaly
        ) VALUES (
            %(model_run_id)s, %(event_id)s, %(risk_score)s, %(predicted_anomaly)s,
            %(expected_anomaly)s
        )
        ON CONFLICT (model_run_id, event_id) DO UPDATE SET
            risk_score = EXCLUDED.risk_score,
            predicted_anomaly = EXCLUDED.predicted_anomaly,
            expected_anomaly = EXCLUDED.expected_anomaly;
        """
        rows = [
            {
                "model_run_id": model_run_id,
                "event_id": prediction.event_id,
                "risk_score": prediction.risk_score,
                "predicted_anomaly": prediction.predicted_anomaly,
                "expected_anomaly": prediction.expected_anomaly,
            }
            for prediction in predictions
        ]
        with self._connection.cursor() as cursor:
            cursor.executemany(query, rows)
        self._connection.commit()
        return len(rows)

    def list_runs(self, *, limit: int) -> list[ModelRunSummary]:
        """Return newest registered model runs with their stored metrics."""
        query = """
        SELECT model_run_id, created_at, model_name, artifact_path, alert_threshold,
               training_event_count, validation_precision, validation_recall, validation_f1,
               test_precision, test_recall, test_f1
        FROM model_runs
        ORDER BY created_at DESC
        LIMIT %s;
        """
        with self._connection.cursor() as cursor:
            cursor.execute(query, (limit,))
            rows = cursor.fetchall()
        return [
            ModelRunSummary(
                model_run_id=row[0],
                created_at=row[1],
                model_name=row[2],
                artifact_path=row[3],
                alert_threshold=float(row[4]),
                training_event_count=row[5],
                validation_precision=float(row[6]),
                validation_recall=float(row[7]),
                validation_f1=float(row[8]),
                test_precision=float(row[9]),
                test_recall=float(row[10]),
                test_f1=float(row[11]),
            )
            for row in rows
        ]

    def list_predictions(self, model_run_id: UUID, *, limit: int) -> list[PersistedModelPrediction]:
        """Return persisted test predictions ordered by greatest risk first."""
        query = """
        SELECT event_id, risk_score, predicted_anomaly, expected_anomaly
        FROM model_predictions
        WHERE model_run_id = %s
        ORDER BY risk_score DESC, event_id
        LIMIT %s;
        """
        with self._connection.cursor() as cursor:
            cursor.execute(query, (model_run_id, limit))
            rows = cursor.fetchall()
        return [
            PersistedModelPrediction(
                event_id=row[0],
                risk_score=float(row[1]),
                predicted_anomaly=row[2],
                expected_anomaly=row[3],
            )
            for row in rows
        ]

    def close(self) -> None:
        """Release the registry connection."""
        self._connection.close()
