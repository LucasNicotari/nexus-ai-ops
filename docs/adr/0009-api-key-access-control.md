# ADR 0009: API-key access control

## Status

Accepted

## Decision

Protect operational and ML read endpoints with a fail-closed `X-NEXUS-API-Key` dependency.
Credentials are supplied only through the ignored local environment file and map to explicit roles.
`/health` is intentionally public for infrastructure probes.

## Rationale

API keys provide a small, deterministic machine-to-machine boundary without prematurely operating
an identity provider. The authorization dependency is separate from routes, allowing future OIDC
or JWT verification to replace authentication while preserving role checks.

## Consequences

Local callers must configure and send a key. This is not user identity, credential rotation, or a
complete enterprise SSO solution; those capabilities require an external identity provider.
