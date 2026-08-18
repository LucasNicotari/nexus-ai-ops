# ADR 0005: Use causal rolling features and chronological model evaluation

## Context

Randomly splitting time-series events allows future patterns into training and produces overly optimistic metrics. The temporal synthetic dataset now has enough span for isolated train, validation, and test periods.

## Decision

Build rolling features from values preceding each event, split by timestamp into 60% train, 20% validation, and 20% test, select the alert threshold only on validation, then report final metrics on the untouched test partition.

## Consequences

This creates a reusable evaluation boundary for future models and prevents basic temporal leakage. It remains a simulation: three days and recurring scenarios are insufficient for production claims.
