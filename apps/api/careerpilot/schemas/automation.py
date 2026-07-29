from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class AutomationCreate(BaseModel):
    job_id: UUID
    resume_id: UUID
    cover_letter_id: UUID | None = None
    application_url: HttpUrl
    dry_run: bool = True
    max_attempts: int = Field(default=3, ge=1, le=5)


class AutomationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    profile_id: UUID
    job_id: UUID
    resume_id: UUID
    cover_letter_id: UUID | None
    adapter: str
    application_url: str
    status: str
    dry_run: bool
    approved: bool
    attempt_count: int
    max_attempts: int
    checkpoint: str
    field_snapshot: list[dict[str, Any]]
    validation_errors: list[str]
    last_error: str | None


class FieldInspection(BaseModel):
    label: str
    kind: str = "text"
    required: bool = False
    options: list[str] = Field(default_factory=list)


class InspectRequest(BaseModel):
    fields: list[FieldInspection]


class MappedField(BaseModel):
    label: str
    value: str | None
    source: str
    confidence: float
    sensitive: bool = False
    requires_review: bool = False


class InspectionRead(BaseModel):
    adapter: str
    fields: list[MappedField]
    validation_errors: list[str]


class ApprovalRequest(BaseModel):
    approved: bool = True


class AdapterSettingUpdate(BaseModel):
    enabled: bool | None = None
    headless: bool | None = None
    default_dry_run: bool | None = None
    timeout_ms: int | None = Field(default=None, ge=1000, le=120000)
    options: dict[str, Any] | None = None


class AdapterSettingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    adapter: str
    enabled: bool
    headless: bool
    default_dry_run: bool
    timeout_ms: int
    options: dict[str, Any]


AutomationStatus = Literal[
    "queued", "inspected", "needs_review", "ready", "running", "dry_run_complete",
    "submitted", "failed", "cancelled"
]
