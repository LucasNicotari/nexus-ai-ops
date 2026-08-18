"""Public response schemas for the NEXUS API."""

from datetime import datetime

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str


class OperationalEventResponse(BaseModel):
    event_id: str
    occurred_at: datetime
    host: str
    service: str
    metric_name: str
    metric_value: float
    unit: str
    severity: str
    is_anomaly: bool


class MetricSummaryResponse(BaseModel):
    metric_name: str
    event_count: int
    average_value: float
    minimum_value: float
    maximum_value: float
    anomaly_count: int


class ServiceIncidentSummaryResponse(BaseModel):
    service: str
    anomalous_event_count: int
    critical_event_count: int
    last_anomaly_at: datetime
