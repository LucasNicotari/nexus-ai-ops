"""Tests for causal temporal feature engineering and split boundaries."""

from nexus.ml.temporal_features import build_temporal_feature_records, split_temporal_dataset
from nexus.synthetic.generator import generate_temporal_operational_events


def test_feature_records_use_only_prior_measurements() -> None:
    """The first feature record uses a full history window before its event."""
    events = generate_temporal_operational_events(20)
    records = build_temporal_feature_records(events)

    first_cpu_record = next(
        record for record in records if record.event.metric_name == "cpu_usage_percent"
    )

    assert first_cpu_record.event.event_id == "evt-temporal-00012-0"
    assert first_cpu_record.lag_value != first_cpu_record.event.metric_value


def test_temporal_split_keeps_timestamps_in_distinct_partitions() -> None:
    """Events from one timestamp cannot leak across train, validation, and test."""
    records = build_temporal_feature_records(generate_temporal_operational_events())
    split = split_temporal_dataset(records)

    train_timestamps = {record.event.occurred_at for record in split.train}
    validation_timestamps = {record.event.occurred_at for record in split.validation}
    test_timestamps = {record.event.occurred_at for record in split.test}

    assert train_timestamps.isdisjoint(validation_timestamps)
    assert validation_timestamps.isdisjoint(test_timestamps)
    assert max(train_timestamps) < min(validation_timestamps) < min(test_timestamps)
