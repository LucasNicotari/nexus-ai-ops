"""Minimal request observability without external vendor coupling."""

from __future__ import annotations

import logging
from time import perf_counter
from uuid import uuid4

from fastapi import Request, Response
from prometheus_client import Counter, Histogram

logger = logging.getLogger("nexus.api")
REQUEST_COUNT = Counter(
    "nexus_api_requests_total",
    "Completed NEXUS API requests.",
    ("method", "path", "status_code"),
)
REQUEST_DURATION_SECONDS = Histogram(
    "nexus_api_request_duration_seconds",
    "NEXUS API request duration in seconds.",
    ("method", "path"),
)


async def request_observability(request: Request, call_next: object) -> Response:
    """Attach a request identifier and emit one structured completion log entry."""
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    started_at = perf_counter()
    response = await call_next(request)  # type: ignore[operator]
    duration_ms = round((perf_counter() - started_at) * 1_000, 2)
    response.headers["X-Request-ID"] = request_id
    labels = {"method": request.method, "path": request.url.path}
    REQUEST_COUNT.labels(**labels, status_code=str(response.status_code)).inc()
    REQUEST_DURATION_SECONDS.labels(**labels).observe(duration_ms / 1_000)
    logger.info(
        "request_completed request_id=%s method=%s path=%s status_code=%s duration_ms=%s",
        request_id,
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response
