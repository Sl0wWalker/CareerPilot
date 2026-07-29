from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class BetaPreferenceUpdate(BaseModel):
    enrolled: bool | None = None
    diagnostics_opt_in: bool | None = None
    analytics_opt_in: bool | None = None
    release_channel: Literal["stable", "beta"] | None = None
    onboarding_completed: bool | None = None


class BetaPreferenceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    enrolled: bool
    diagnostics_opt_in: bool
    analytics_opt_in: bool
    release_channel: str
    onboarding_completed: bool


class FeedbackCreate(BaseModel):
    kind: Literal["bug", "feature", "feedback"]
    title: str = Field(min_length=3, max_length=240)
    description: str = Field(min_length=3, max_length=20000)
    severity: Literal["low", "normal", "high", "critical"] = "normal"
    page_url: str | None = Field(default=None, max_length=1000)
    diagnostics: dict[str, Any] = Field(default_factory=dict)


class FeedbackUpdate(BaseModel):
    status: Literal["new", "reviewing", "planned", "resolved", "closed"]


class FeedbackRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    kind: str
    title: str
    description: str
    severity: str
    status: str
    page_url: str | None
    diagnostics_json: dict[str, Any]
    votes: int
    created_at: datetime


class SatisfactionCreate(BaseModel):
    score: int = Field(ge=0, le=10)
    comment: str | None = Field(default=None, max_length=5000)
    context: str | None = Field(default=None, max_length=120)


class UsageEventCreate(BaseModel):
    anonymous_id: str = Field(min_length=8, max_length=64)
    event_name: str = Field(min_length=2, max_length=120)
    properties: dict[str, Any] = Field(default_factory=dict)


class FeatureFlagCreate(BaseModel):
    key: str = Field(pattern=r"^[a-z][a-z0-9_.-]{2,119}$")
    description: str = ""
    enabled: bool = False
    beta_only: bool = False
    rollout_percentage: int = Field(default=100, ge=0, le=100)
    config: dict[str, Any] = Field(default_factory=dict)


class FeatureFlagRead(FeatureFlagCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID


class FlagEvaluation(BaseModel):
    key: str
    enabled: bool
    config: dict[str, Any]


class ProductHealth(BaseModel):
    feedback_total: int
    open_bugs: int
    feature_requests: int
    satisfaction_average: float | None
    opted_in_users: int
    usage_events: int

