from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

ApplicationStatus = Literal[
    "draft", "preparing", "ready", "submitted", "recruiter_screen",
    "interview", "offer", "rejected", "withdrawn", "archived",
]


class ApplicationCreate(BaseModel):
    job_id: UUID
    automation_run_id: UUID | None = None
    status: ApplicationStatus = "draft"
    source: str = "manual"
    tags: list[str] = Field(default_factory=list)


class ApplicationUpdate(BaseModel):
    status: ApplicationStatus | None = None
    outcome: str | None = None
    rejection_reason: str | None = None
    offer_amount: float | None = Field(default=None, ge=0)
    offer_currency: str | None = Field(default=None, min_length=3, max_length=3)
    tags: list[str] | None = None


class ApplicationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    profile_id: UUID
    job_id: UUID
    automation_run_id: UUID | None
    status: str
    source: str
    applied_at: datetime | None
    responded_at: datetime | None
    closed_at: datetime | None
    outcome: str | None
    rejection_reason: str | None
    offer_amount: float | None
    offer_currency: str | None
    tags: list[str]
    metadata_json: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class EventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    event_type: str
    from_status: str | None
    to_status: str | None
    title: str
    details: dict[str, Any]
    occurred_at: datetime


class NoteCreate(BaseModel):
    body: str = Field(min_length=1, max_length=10000)
    pinned: bool = False


class NoteRead(NoteCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    application_id: UUID
    created_at: datetime


class ContactCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    role: str | None = None
    email: str | None = None
    phone: str | None = None
    linkedin_url: str | None = None
    notes: str | None = None


class ContactRead(ContactCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    application_id: UUID


class FollowUpCreate(BaseModel):
    title: str = Field(min_length=1, max_length=240)
    due_at: datetime
    reminder_enabled: bool = True


class FollowUpRead(FollowUpCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    application_id: UUID
    completed_at: datetime | None


class InterviewCreate(BaseModel):
    stage: str = Field(min_length=1, max_length=120)
    scheduled_at: datetime | None = None
    duration_minutes: int | None = Field(default=None, ge=5, le=480)
    location_or_link: str | None = None
    notes: str | None = None


class InterviewRead(InterviewCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    application_id: UUID


class AnalyticsRead(BaseModel):
    total: int
    by_status: dict[str, int]
    submitted: int
    responses: int
    interviews: int
    offers: int
    rejections: int
    response_rate: float
    interview_rate: float
    offer_rate: float
    average_days_to_response: float | None


class ImportPayload(BaseModel):
    applications: list[dict[str, Any]]
