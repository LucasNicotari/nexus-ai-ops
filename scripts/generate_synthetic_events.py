"""Generate the reproducible sample dataset used by NEXUS."""

from __future__ import annotations

import csv
from pathlib import Path

from nexus.synthetic.generator import generate_operational_events

OUTPUT_PATH = Path("data/synthetic/operational_events.csv")


def main() -> None:
    """Write the default operational event dataset as CSV."""
    events = generate_operational_events()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT_PATH.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=list(events[0].to_row()))
        writer.writeheader()
        writer.writerows(event.to_row() for event in events)

    print(f"Generated {len(events)} events at {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
