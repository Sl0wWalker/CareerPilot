from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import text

from careerpilot.db.session import engine

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: Literal["ok"]
    service: str


class ReadinessResponse(HealthResponse):
    database: Literal["ok"]


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", service="careerpilot-api")


@router.get("/ready", response_model=ReadinessResponse)
def readiness() -> ReadinessResponse:
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return ReadinessResponse(status="ok", service="careerpilot-api", database="ok")

