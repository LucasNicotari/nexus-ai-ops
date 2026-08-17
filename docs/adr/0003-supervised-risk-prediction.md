# ADR 0003: Use a cross-validated Random Forest baseline for labeled risk prediction

## Context

The synthetic dataset has only 120 rows and four positive labels. A conventional holdout set would contain one or fewer anomalies and produce unstable metrics.

## Decision

Use a class-balanced Random Forest with metric, value, relative deviation from the configured synthetic baseline, service, and host as features. Evaluate with four-fold stratified cross-validation and out-of-fold probabilities. Use a 0.20 alert threshold because this small, imbalanced baseline is a high-recall triage mechanism. Do not use severity, event ID, or `is_anomaly` as input features.

## Consequences

The baseline reference values are valid only for this synthetic generator. Production use requires rolling historical baselines instead of fixed values. Time-aware validation also requires a larger temporal dataset.
