from typing import Annotated, Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import text

from careerpilot.core.config import Settings, get_settings
from careerpilot.core.middleware import metrics
from careerpilot.db.session import engine

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: Literal["ok"]
    service: str


class ReadinessResponse(HealthResponse):
    database: Literal["ok"]


class DiagnosticsResponse(BaseModel):
    status: Literal["ok"]
    version: str
    environment: str
    database: Literal["ok"]
    authentication: bool


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", service="careerpilot-api")


@router.get("/ready", response_model=ReadinessResponse)
def readiness() -> ReadinessResponse:
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return ReadinessResponse(status="ok", service="careerpilot-api", database="ok")


@router.get("/diagnostics", response_model=DiagnosticsResponse)
def diagnostics(settings: Annotated[Settings, Depends(get_settings)]) -> DiagnosticsResponse:
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return DiagnosticsResponse(
        status="ok",
        version=settings.app_version,
        environment=settings.environment,
        database="ok",
        authentication=settings.auth_enabled,
    )


@router.get("/metrics")
def application_metrics() -> dict[str, int | float]:
    requests = int(metrics["requests_total"])
    return {
        **metrics,
        "average_duration_ms": (
            round(float(metrics["duration_ms_total"]) / requests, 2) if requests else 0
        ),
    }

