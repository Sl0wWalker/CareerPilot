from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class StrategyCreate(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    horizon_months: int = Field(default=12, ge=1, le=120)
    target_roles: list[str] = Field(default_factory=list, max_length=30)
    objectives: list[dict[str, Any]] = Field(default_factory=list)
    constraints: dict[str, Any] = Field(default_factory=dict)


class StrategyRead(StrategyCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    status: str
    created_at: datetime


class MonitorCreate(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    criteria: dict[str, Any] = Field(default_factory=dict)
    cadence: Literal["hourly", "daily", "weekly"] = "daily"
    enabled: bool = True


class MonitorRead(MonitorCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    last_checked_at: datetime | None
    last_result: dict[str, Any]


class AgentConfigUpsert(BaseModel):
    agent_key: str = Field(pattern=r"^[a-z0-9][a-z0-9-]{1,119}$")
    display_name: str = Field(min_length=2, max_length=200)
    objective: str = Field(min_length=5, max_length=3000)
    enabled: bool = False
    autonomy_level: Literal["observe", "recommend", "prepare", "execute"] = "recommend"
    approval_policy: dict[str, Any] = Field(
        default_factory=lambda: {
            "external_writes": "always",
            "applications": "always",
            "messages": "always",
        }
    )
    capabilities: list[str] = Field(default_factory=list)
    schedule: dict[str, Any] = Field(default_factory=dict)


class AgentConfigRead(AgentConfigUpsert):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    last_run: dict[str, Any]


class ForecastCreate(BaseModel):
    skill: str = Field(min_length=1, max_length=120)
    current_demand: float = Field(ge=0, le=1)
    projected_demand: float = Field(ge=0, le=1)
    evidence: list[dict[str, Any]] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0, le=1)


class NotificationCreate(BaseModel):
    channel_type: Literal["in_app", "desktop", "webhook", "email"]
    label: str = Field(min_length=1, max_length=120)
    endpoint: str | None = Field(default=None, max_length=1000)
    enabled: bool = True
    preferences: dict[str, Any] = Field(default_factory=dict)


class IntelligenceOverview(BaseModel):
    strategies: int
    active_monitors: int
    configured_agents: int
    enabled_agents: int
    approval_required_agents: int
    rising_skills: list[dict[str, Any]]
    market_insights: list[dict[str, Any]]
    recruiter_engagement: dict[str, Any]
    opportunity_pipeline: dict[str, int]

