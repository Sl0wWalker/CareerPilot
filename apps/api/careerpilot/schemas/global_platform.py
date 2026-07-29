from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class GlobalPreferenceUpsert(BaseModel):
    locale: str = Field(default="en-US", pattern=r"^[a-z]{2,3}(?:-[A-Z]{2})?$")
    region: str = Field(default="US", pattern=r"^[A-Z]{2}$")
    timezone: str = Field(default="UTC", min_length=1, max_length=80)
    currency: str = Field(default="USD", pattern=r"^[A-Z]{3}$")
    measurement_system: Literal["metric", "imperial"] = "imperial"
    reduced_motion: bool = False
    high_contrast: bool = False
    regional_job_rules: dict[str, Any] = Field(default_factory=dict)


class GlobalPreferenceRead(GlobalPreferenceUpsert):
    model_config = ConfigDict(from_attributes=True)
    id: UUID


class RoutingPolicyUpsert(BaseModel):
    task_type: str = Field(min_length=2, max_length=80)
    local_first: bool = True
    allow_cloud_fallback: bool = False
    preferred_provider: str = Field(default="ollama", max_length=80)
    preferred_model: str | None = Field(default=None, max_length=160)
    max_latency_ms: int = Field(default=30000, ge=250, le=300000)
    privacy_class: Literal["public", "internal", "sensitive", "restricted"] = "sensitive"
    constraints: dict[str, Any] = Field(default_factory=dict)


class MobileEndpointCreate(BaseModel):
    device_id: str = Field(min_length=4, max_length=160)
    platform: Literal["pwa", "ios", "android"]
    push_endpoint: str | None = Field(default=None, max_length=2000)
    locale: str = Field(default="en-US", max_length=20)
    timezone: str = Field(default="UTC", max_length=80)
    enabled: bool = True
    capabilities: list[str] = Field(default_factory=list, max_length=20)


class NotificationCreate(BaseModel):
    endpoint_id: UUID | None = None
    category: str = Field(min_length=2, max_length=80)
    title: str = Field(min_length=1, max_length=240)
    body: str = Field(min_length=1, max_length=2000)
    payload: dict[str, Any] = Field(default_factory=dict)
