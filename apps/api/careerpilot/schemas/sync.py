from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class DeviceRegister(BaseModel):
    device_key: str = Field(min_length=3, max_length=128)
    display_name: str = Field(min_length=1, max_length=120)
    platform: str = Field(default="unknown", max_length=60)


class DeviceRead(ORMModel):
    id: UUID
    device_key: str
    display_name: str
    platform: str
    last_cursor: int
    last_seen_at: datetime | None
    revoked: bool


class ChangeInput(BaseModel):
    entity_type: Literal["profile", "resume", "settings", "application"]
    entity_key: str = Field(min_length=1, max_length=128)
    operation: Literal["upsert", "delete"] = "upsert"
    base_revision: int = Field(default=0, ge=0)
    payload: dict[str, Any] = Field(default_factory=dict)


class ChangeRead(ORMModel):
    id: UUID
    entity_type: str
    entity_key: str
    operation: str
    revision: int
    base_revision: int
    payload_json: dict[str, Any]
    checksum: str
    created_at: datetime


class PushRequest(BaseModel):
    device_id: UUID
    changes: list[ChangeInput] = Field(max_length=500)


class SyncBatch(BaseModel):
    cursor: int
    accepted: list[ChangeRead]
    conflicts: list[UUID]


class ConflictRead(ORMModel):
    id: UUID
    entity_type: str
    entity_key: str
    local_change_id: UUID
    remote_change_id: UUID
    status: str
    resolution: str | None
    resolved_payload_json: dict[str, Any] | None


class ConflictResolve(BaseModel):
    resolution: Literal["keep_local", "keep_remote", "merge"]
    merged_payload: dict[str, Any] | None = None


class AccountCreate(BaseModel):
    provider: Literal[
        "gmail", "google_calendar", "google_drive", "onedrive", "dropbox", "linkedin"
    ]
    external_account_id: str = Field(min_length=1, max_length=240)
    display_name: str = Field(min_length=1, max_length=240)
    scopes: list[str] = Field(default_factory=list, max_length=30)
    credential_reference: str | None = Field(default=None, max_length=500)


class AccountRead(ORMModel):
    id: UUID
    provider: str
    external_account_id: str
    display_name: str
    scopes_json: list[str]
    status: str
    last_synced_at: datetime | None
    error_message: str | None


class IntegrationDescriptor(BaseModel):
    provider: str
    category: str
    capabilities: list[str]
    permitted_use: str
    connected: bool


class WorkspaceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    description: str = Field(default="", max_length=2000)


class WorkspaceRead(ORMModel):
    id: UUID
    owner_id: str
    name: str
    description: str
    created_at: datetime


class MemberCreate(BaseModel):
    user_id: str = Field(min_length=1, max_length=64)
    role: Literal["admin", "editor", "viewer"] = "viewer"
    permissions: list[
        Literal[
            "profile.read",
            "resume.read",
            "application.read",
            "application.write",
            "settings.read",
        ]
    ] = Field(default_factory=lambda: ["application.read"])


class MemberRead(ORMModel):
    id: UUID
    workspace_id: UUID
    user_id: str
    role: str
    permissions_json: list[str]
    status: str


class WebhookCreate(BaseModel):
    url: HttpUrl
    events: list[
        Literal["sync.completed", "application.updated", "resume.created", "integration.error"]
    ] = Field(min_length=1, max_length=10)
    secret_reference: str | None = Field(default=None, max_length=500)


class WebhookRead(ORMModel):
    id: UUID
    url: str
    events_json: list[str]
    enabled: bool
