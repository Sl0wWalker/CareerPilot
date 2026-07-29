from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class SourceCreate(BaseModel):
    provider: Literal["greenhouse", "lever", "ashby", "workday", "rss", "json"]
    external_key: str = Field(min_length=1, max_length=255)
    name: str = Field(min_length=1, max_length=240)
    source_url: HttpUrl | None = None
    configuration: dict[str, Any] = Field(default_factory=dict)


class SourceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    provider: str
    external_key: str
    name: str
    source_url: str | None
    enabled: bool
    last_synced_at: datetime | None


class JobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    title: str
    company_name: str
    source_provider: str
    canonical_url: str
    application_url: str | None
    description: str
    location_raw: str | None
    city: str | None
    region: str | None
    country: str | None
    workplace_type: str
    employment_type: str | None
    salary_min: int | None
    salary_max: int | None
    salary_currency: str | None
    salary_period: str | None
    posted_at: datetime | None
    is_favorite: bool
    relevance_score: float | None
    relevance_analysis: dict[str, Any] | None


class JobSearchRequest(BaseModel):
    query: str | None = Field(default=None, max_length=300)
    company: str | None = None
    location: str | None = None
    workplace_type: Literal["remote", "hybrid", "onsite", "unknown"] | None = None
    employment_type: str | None = None
    favorite_only: bool = False
    minimum_salary: int | None = Field(default=None, ge=0)
    limit: int = Field(default=50, ge=1, le=200)
    offset: int = Field(default=0, ge=0)


class SavedSearchCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    query: str | None = None
    filters: dict[str, Any] = Field(default_factory=dict)


class SavedSearchRead(SavedSearchCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID


class ScheduledSearchCreate(BaseModel):
    saved_search_id: UUID
    cadence: Literal["hourly", "daily", "weekly"]
    enabled: bool = True


class ScheduledSearchRead(ScheduledSearchCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    next_run_at: datetime | None
    last_run_at: datetime | None


class SyncResult(BaseModel):
    source_id: UUID
    discovered: int
    created: int
    updated: int
    skipped: int

