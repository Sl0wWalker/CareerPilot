from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from careerpilot.db.base import Base
from careerpilot.models.profile import EntityMixin


class Application(EntityMixin, Base):
    __tablename__ = "applications"

    profile_id: Mapped[UUID] = mapped_column(
        Uuid(native_uuid=False), ForeignKey("career_profiles.id", ondelete="CASCADE"), index=True
    )
    job_id: Mapped[UUID] = mapped_column(
        Uuid(native_uuid=False), ForeignKey("jobs.id", ondelete="CASCADE"), index=True
    )
    automation_run_id: Mapped[UUID | None] = mapped_column(
        Uuid(native_uuid=False), ForeignKey("automation_runs.id", ondelete="SET NULL")
    )
    status: Mapped[str] = mapped_column(String(40), default="draft", index=True)
    source: Mapped[str] = mapped_column(String(40), default="manual")
    applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    responded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    outcome: Mapped[str | None] = mapped_column(String(40), index=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text)
    offer_amount: Mapped[float | None] = mapped_column(Float)
    offer_currency: Mapped[str | None] = mapped_column(String(3))
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)


class ApplicationEvent(EntityMixin, Base):
    __tablename__ = "application_events"

    application_id: Mapped[UUID] = mapped_column(
        Uuid(native_uuid=False), ForeignKey("applications.id", ondelete="CASCADE"), index=True
    )
    event_type: Mapped[str] = mapped_column(String(50), index=True)
    from_status: Mapped[str | None] = mapped_column(String(40))
    to_status: Mapped[str | None] = mapped_column(String(40))
    title: Mapped[str] = mapped_column(String(240))
    details: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


class ApplicationNote(EntityMixin, Base):
    __tablename__ = "application_notes"

    application_id: Mapped[UUID] = mapped_column(
        Uuid(native_uuid=False), ForeignKey("applications.id", ondelete="CASCADE"), index=True
    )
    body: Mapped[str] = mapped_column(Text)
    pinned: Mapped[bool] = mapped_column(Boolean, default=False)


class Contact(EntityMixin, Base):
    __tablename__ = "application_contacts"

    application_id: Mapped[UUID] = mapped_column(
        Uuid(native_uuid=False), ForeignKey("applications.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(200))
    role: Mapped[str | None] = mapped_column(String(160))
    email: Mapped[str | None] = mapped_column(String(320))
    phone: Mapped[str | None] = mapped_column(String(50))
    linkedin_url: Mapped[str | None] = mapped_column(String(2048))
    notes: Mapped[str | None] = mapped_column(Text)


class FollowUp(EntityMixin, Base):
    __tablename__ = "application_follow_ups"

    application_id: Mapped[UUID] = mapped_column(
        Uuid(native_uuid=False), ForeignKey("applications.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(240))
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reminder_enabled: Mapped[bool] = mapped_column(Boolean, default=True)


class InterviewPlaceholder(EntityMixin, Base):
    __tablename__ = "application_interviews"

    application_id: Mapped[UUID] = mapped_column(
        Uuid(native_uuid=False), ForeignKey("applications.id", ondelete="CASCADE"), index=True
    )
    stage: Mapped[str] = mapped_column(String(120))
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    duration_minutes: Mapped[int | None] = mapped_column(Integer)
    location_or_link: Mapped[str | None] = mapped_column(String(2048))
    notes: Mapped[str | None] = mapped_column(Text)
