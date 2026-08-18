"""Generate reproducible time-series data for model development."""

from __future__ import annotations

import csv
from pathlib import Path

from nexus.synthetic.generator import generate_temporal_operational_events

OUTPUT_PATH = Path("data/synthetic/temporal_training_events.csv")


def main() -> None:
    """Write three days of five-minute operational measurements as CSV."""
    events = generate_temporal_operational_events()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=list(events[0].to_row()))
        writer.writeheader()
        writer.writerows(event.to_row() for event in events)
    print(f"Generated {len(events)} temporal events at {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
