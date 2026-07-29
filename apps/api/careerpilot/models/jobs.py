from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from careerpilot.db.base import Base
from careerpilot.models.profile import EntityMixin


class Company(EntityMixin, Base):
    __tablename__ = "companies"

    name: Mapped[str] = mapped_column(String(240), unique=True, index=True)
    website_url: Mapped[str | None] = mapped_column(String(2048))
    careers_url: Mapped[str | None] = mapped_column(String(2048))
    description: Mapped[str | None] = mapped_column(Text)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    jobs: Mapped[list["Job"]] = relationship(back_populates="company")


class JobSource(EntityMixin, Base):
    __tablename__ = "job_sources"
    __table_args__ = (UniqueConstraint("provider", "external_key"),)

    provider: Mapped[str] = mapped_column(String(40), index=True)
    external_key: Mapped[str] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(240))
    source_url: Mapped[str | None] = mapped_column(String(2048))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    configuration: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Job(EntityMixin, Base):
    __tablename__ = "jobs"
    __table_args__ = (UniqueConstraint("source_provider", "external_id"),)

    company_id: Mapped[UUID] = mapped_column(
        Uuid(native_uuid=False), ForeignKey("companies.id", ondelete="CASCADE"), index=True
    )
    source_provider: Mapped[str] = mapped_column(String(40), index=True)
    external_id: Mapped[str] = mapped_column(String(255))
    title: Mapped[str] = mapped_column(String(300), index=True)
    description: Mapped[str] = mapped_column(Text)
    canonical_url: Mapped[str] = mapped_column(String(2048))
    application_url: Mapped[str | None] = mapped_column(String(2048))
    location_raw: Mapped[str | None] = mapped_column(String(300))
    city: Mapped[str | None] = mapped_column(String(120), index=True)
    region: Mapped[str | None] = mapped_column(String(120), index=True)
    country: Mapped[str | None] = mapped_column(String(120), index=True)
    workplace_type: Mapped[str] = mapped_column(String(20), default="unknown", index=True)
    employment_type: Mapped[str | None] = mapped_column(String(40), index=True)
    salary_min: Mapped[int | None] = mapped_column(Integer)
    salary_max: Mapped[int | None] = mapped_column(Integer)
    salary_currency: Mapped[str | None] = mapped_column(String(3))
    salary_period: Mapped[str | None] = mapped_column(String(20))
    posted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    fingerprint: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    search_text: Mapped[str] = mapped_column(Text)
    raw_payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    relevance_score: Mapped[float | None] = mapped_column(Float)
    relevance_analysis: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    company: Mapped[Company] = relationship(back_populates="jobs")


class SavedSearch(EntityMixin, Base):
    __tablename__ = "saved_searches"

    name: Mapped[str] = mapped_column(String(200))
    query: Mapped[str | None] = mapped_column(String(300))
    filters: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)


class ScheduledSearch(EntityMixin, Base):
    __tablename__ = "scheduled_searches"

    saved_search_id: Mapped[UUID] = mapped_column(
        Uuid(native_uuid=False), ForeignKey("saved_searches.id", ondelete="CASCADE"), index=True
    )
    cadence: Mapped[str] = mapped_column(String(30))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    next_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

