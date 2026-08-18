"""Fail-closed API-key authentication for machine-to-machine API access."""

from __future__ import annotations

import os
from dataclasses import dataclass
from hmac import compare_digest

from fastapi import Header, HTTPException, status

_API_KEY_HEADER = "X-NEXUS-API-Key"
_READER_ROLE = "reader"


@dataclass(frozen=True, slots=True)
class Principal:
    """Authenticated machine identity and its assigned access role."""

    role: str


def require_reader(
    api_key: str | None = Header(default=None, alias=_API_KEY_HEADER),
) -> Principal:
    """Authenticate a configured API key and require read permission.

    ``NEXUS_API_KEYS`` contains comma-separated ``api-key:role`` entries. Missing or malformed
    configuration denies every protected request rather than accidentally exposing operational data.
    """
    if api_key is None:
        raise _unauthorized()

    for configured_key, role in _configured_credentials():
        if compare_digest(api_key, configured_key):
            if role == _READER_ROLE:
                return Principal(role=role)
            raise _forbidden()
    raise _unauthorized()


def _configured_credentials() -> list[tuple[str, str]]:
    raw_credentials = os.getenv("NEXUS_API_KEYS", "")
    credentials: list[tuple[str, str]] = []
    for entry in raw_credentials.split(","):
        api_key, separator, role = entry.strip().partition(":")
        if separator and api_key and role:
            credentials.append((api_key, role))
    return credentials


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="valid API key required",
        headers={"WWW-Authenticate": "ApiKey"},
    )


def _forbidden() -> HTTPException:
    return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="insufficient API role")
