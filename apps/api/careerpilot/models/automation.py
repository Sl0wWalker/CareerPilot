from typing import Any
from uuid import UUID

from sqlalchemy import JSON, Boolean, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from careerpilot.db.base import Base
from careerpilot.models.profile import EntityMixin


class AutomationRun(EntityMixin, Base):
    __tablename__ = "automation_runs"

    profile_id: Mapped[UUID] = mapped_column(
        Uuid(native_uuid=False), ForeignKey("career_profiles.id", ondelete="CASCADE"), index=True
    )
    job_id: Mapped[UUID] = mapped_column(
        Uuid(native_uuid=False), ForeignKey("jobs.id", ondelete="CASCADE"), index=True
    )
    resume_id: Mapped[UUID] = mapped_column(
        Uuid(native_uuid=False), ForeignKey("document_versions.id"), index=True
    )
    cover_letter_id: Mapped[UUID | None] = mapped_column(
        Uuid(native_uuid=False), ForeignKey("document_versions.id")
    )
    adapter: Mapped[str] = mapped_column(String(32), index=True)
    application_url: Mapped[str] = mapped_column(String(2048))
    status: Mapped[str] = mapped_column(String(32), default="queued", index=True)
    dry_run: Mapped[bool] = mapped_column(Boolean, default=True)
    approved: Mapped[bool] = mapped_column(Boolean, default=False)
    attempt_count: Mapped[int] = mapped_column(Integer, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, default=3)
    checkpoint: Mapped[str] = mapped_column(String(40), default="created")
    field_snapshot: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    validation_errors: Mapped[list[str]] = mapped_column(JSON, default=list)
    last_error: Mapped[str | None] = mapped_column(Text)


class AutomationStep(EntityMixin, Base):
    __tablename__ = "automation_steps"

    run_id: Mapped[UUID] = mapped_column(
        Uuid(native_uuid=False), ForeignKey("automation_runs.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(24))
    details: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    screenshot_path: Mapped[str | None] = mapped_column(String(1024))


class BrowserSession(EntityMixin, Base):
    __tablename__ = "browser_sessions"

    profile_id: Mapped[UUID] = mapped_column(
        Uuid(native_uuid=False), ForeignKey("career_profiles.id", ondelete="CASCADE"), index=True
    )
    adapter: Mapped[str] = mapped_column(String(32), index=True)
    label: Mapped[str] = mapped_column(String(120))
    storage_state_path: Mapped[str] = mapped_column(String(1024))
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class AdapterSetting(EntityMixin, Base):
    __tablename__ = "adapter_settings"

    adapter: Mapped[str] = mapped_column(String(32), unique=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    headless: Mapped[bool] = mapped_column(Boolean, default=False)
    default_dry_run: Mapped[bool] = mapped_column(Boolean, default=True)
    timeout_ms: Mapped[int] = mapped_column(Integer, default=30000)
    options: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
