"""Causal temporal feature engineering and chronological dataset splitting."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from math import cos, sin, sqrt, tau
from typing import Sequence

from nexus.domain.operational_event import OperationalEvent


@dataclass(frozen=True, slots=True)
class TemporalFeatureRecord:
    """An event enriched only with measurements available before its timestamp."""

    event: OperationalEvent
    lag_value: float
    rolling_mean: float
    rolling_standard_deviation: float
    deviation_from_mean: float
    hour_sin: float
    hour_cos: float


@dataclass(frozen=True, slots=True)
class TemporalDatasetSplit:
    """Chronologically isolated train, validation, and test partitions."""

    train: list[TemporalFeatureRecord]
    validation: list[TemporalFeatureRecord]
    test: list[TemporalFeatureRecord]


def build_temporal_feature_records(
    events: Sequence[OperationalEvent], *, window_size: int = 12
) -> list[TemporalFeatureRecord]:
    """Create rolling features without allowing a row to observe its future values."""
    if window_size < 2:
        raise ValueError("window_size must be at least 2")

    history_by_metric: dict[str, list[float]] = defaultdict(list)
    records: list[TemporalFeatureRecord] = []
    sorted_events = sorted(events, key=lambda event: (event.occurred_at, event.event_id))

    for event in sorted_events:
        history = history_by_metric[event.metric_name]
        if len(history) >= window_size:
            window = history[-window_size:]
            mean = sum(window) / len(window)
            variance = sum((value - mean) ** 2 for value in window) / len(window)
            standard_deviation = sqrt(variance)
            records.append(
                TemporalFeatureRecord(
                    event=event,
                    lag_value=history[-1],
                    rolling_mean=mean,
                    rolling_standard_deviation=standard_deviation,
                    deviation_from_mean=event.metric_value - mean,
                    hour_sin=sin(tau * event.occurred_at.hour / 24),
                    hour_cos=cos(tau * event.occurred_at.hour / 24),
                )
            )
        history.append(event.metric_value)

    return records


def split_temporal_dataset(
    records: Sequence[TemporalFeatureRecord],
    *,
    train_fraction: float = 0.6,
    validation_fraction: float = 0.2,
) -> TemporalDatasetSplit:
    """Split feature records by timestamp to prevent cross-partition time leakage."""
    if not 0 < train_fraction < 1:
        raise ValueError("train_fraction must be between zero and one")
    if not 0 < validation_fraction < 1:
        raise ValueError("validation_fraction must be between zero and one")
    if train_fraction + validation_fraction >= 1:
        raise ValueError("train and validation fractions must leave a test partition")

    timestamps = sorted({record.event.occurred_at for record in records})
    train_end = int(len(timestamps) * train_fraction)
    validation_end = int(len(timestamps) * (train_fraction + validation_fraction))
    if train_end == 0 or validation_end == train_end or validation_end == len(timestamps):
        raise ValueError("dataset is too small for the requested temporal split")

    train_cutoff = timestamps[train_end]
    validation_cutoff = timestamps[validation_end]
    train = [record for record in records if record.event.occurred_at < train_cutoff]
    validation = [
        record for record in records if train_cutoff <= record.event.occurred_at < validation_cutoff
    ]
    test = [record for record in records if record.event.occurred_at >= validation_cutoff]
    return TemporalDatasetSplit(train=train, validation=validation, test=test)
