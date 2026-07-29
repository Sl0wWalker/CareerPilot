from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class ApiKeyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    scopes: list[str] = Field(default_factory=lambda: ["platform:read"])


class ApiKeyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    prefix: str
    scopes: list[str]
    enabled: bool
    created_at: datetime


class ApiKeyCreated(ApiKeyRead):
    secret: str


class WebhookCreate(BaseModel):
    url: HttpUrl
    event_types: list[str] = Field(min_length=1)
    description: str = Field(default="", max_length=500)


class WebhookRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    url: str
    event_types: list[str]
    enabled: bool
    description: str
    created_at: datetime


class PluginRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    plugin_id: str
    name: str
    version: str
    plugin_type: str
    enabled: bool
    configuration: dict[str, Any]


class PluginUpdate(BaseModel):
    enabled: bool | None = None
    configuration: dict[str, Any] | None = None


class DeveloperOverview(BaseModel):
    api_version: str
    openapi_url: str
    websocket_url: str
    api_keys: int
    webhooks: int
    plugins: int
    extension_types: list[str]


class EventPublish(BaseModel):
    event_type: str = Field(pattern=r"^[a-z][a-z0-9_.-]{2,159}$")
    payload: dict[str, Any] = Field(default_factory=dict)

