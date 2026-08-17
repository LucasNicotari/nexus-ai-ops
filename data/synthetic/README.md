# Synthetic datasets

Generated CSV files are intentionally ignored by Git because they are reproducible artifacts.

- `operational_events.csv`: compact 120-event smoke-test dataset.
- `temporal_training_events.csv`: three days of five-minute measurements, daily load variation, and recurring degradation windows for ML experiments.

Generate the datasets with the scripts in `scripts/`. Future dashboards, APIs, model experiments, and incident simulations should consume the shared event contract instead of creating incompatible datasets.
