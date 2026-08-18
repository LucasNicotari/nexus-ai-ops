# ADR 0002: Use per-metric Isolation Forest as the anomaly detection baseline

## Context

The synthetic dataset contains an `is_anomaly` label, but real operational data often does not. Metrics also use incompatible scales: a latency in milliseconds cannot be directly compared with a percentage.

## Decision

Use a separate scikit-learn `IsolationForest` for each metric. Train it only on metric values; preserve the synthetic label exclusively for offline evaluation. Fix the random state and use a 5% expected anomaly contamination rate for reproducible baseline results.

## Consequences

The detector is unsupervised and applicable when production labels are absent. It intentionally does not model time-series seasonality, multivariate relationships, or incident context; those are future improvements after we have more realistic data.
