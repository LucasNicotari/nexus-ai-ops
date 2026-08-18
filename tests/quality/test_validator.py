"""Tests for operational event quality assessment."""

from dataclasses import replace
from datetime import timedelta

from nexus.quality.validator import assess_operational_event_quality
from nexus.synthetic.generator import generate_operational_events


def test_generated_events_pass_quality_assessment() -> None:
    """The standard deterministic dataset satisfies the initial quality rules."""
    report = assess_operational_event_quality(generate_operational_events())

    assert report.total_events == 120
    assert report.is_valid
    assert report.issues == ()


def test_quality_assessment_reports_duplicate_event_id() -> None:
    """Duplicate identifiers are reported without stopping the whole batch."""
    first_event, second_event = generate_operational_events(2)
    duplicate_event = replace(second_event, event_id=first_event.event_id)

    report = assess_operational_event_quality([first_event, duplicate_event])

    assert [issue.code for issue in report.issues] == ["duplicate_event_id"]


def test_quality_assessment_reports_out_of_order_timestamp() -> None:
    """Event timestamps must be monotonic in the ingestion batch."""
    first_event, second_event = generate_operational_events(2)
    out_of_order_event = replace(
        second_event, occurred_at=first_event.occurred_at - timedelta(minutes=1)
    )

    report = assess_operational_event_quality([first_event, out_of_order_event])

    assert [issue.code for issue in report.issues] == ["timestamp_out_of_order"]


def test_quality_assessment_reports_unknown_metric() -> None:
    """Unsupported measurements cannot silently enter later pipeline stages."""
    event = replace(generate_operational_events(1)[0], metric_name="disk_space_percent")

    report = assess_operational_event_quality([event])

    assert [issue.code for issue in report.issues] == ["unknown_metric"]
