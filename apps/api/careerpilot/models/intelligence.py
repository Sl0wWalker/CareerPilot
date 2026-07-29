from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, Float, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from careerpilot.db.base import Base
from careerpilot.models.profile import EntityMixin


class CareerStrategy(EntityMixin, Base):
    __tablename__ = "career_strategies"

    owner_id: Mapped[str] = mapped_column(String(160), index=True)
    title: Mapped[str] = mapped_column(String(200))
    horizon_months: Mapped[int]
    target_roles: Mapped[list[str]] = mapped_column(JSON, default=list)
    objectives: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    constraints: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(30), default="active", index=True)


class OpportunityMonitor(EntityMixin, Base):
    __tablename__ = "opportunity_monitors"

    owner_id: Mapped[str] = mapped_column(String(160), index=True)
    name: Mapped[str] = mapped_column(String(200))
    criteria: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    cadence: Mapped[str] = mapped_column(String(30), default="daily")
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_result: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)


class SkillForecast(EntityMixin, Base):
    __tablename__ = "skill_forecasts"
    __table_args__ = (UniqueConstraint("owner_id", "skill"),)

    owner_id: Mapped[str] = mapped_column(String(160), index=True)
    skill: Mapped[str] = mapped_column(String(120))
    current_demand: Mapped[float] = mapped_column(Float)
    projected_demand: Mapped[float] = mapped_column(Float)
    trend: Mapped[str] = mapped_column(String(30))
    evidence: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)


class MarketInsight(EntityMixin, Base):
    __tablename__ = "market_insights"

    owner_id: Mapped[str] = mapped_column(String(160), index=True)
    insight_type: Mapped[str] = mapped_column(String(60), index=True)
    title: Mapped[str] = mapped_column(String(240))
    summary: Mapped[str] = mapped_column(Text)
    metrics: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    sources: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)


class AutonomousAgentConfig(EntityMixin, Base):
    __tablename__ = "autonomous_agent_configs"
    __table_args__ = (UniqueConstraint("owner_id", "agent_key"),)

    owner_id: Mapped[str] = mapped_column(String(160), index=True)
    agent_key: Mapped[str] = mapped_column(String(120))
    display_name: Mapped[str] = mapped_column(String(200))
    objective: Mapped[str] = mapped_column(Text)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    autonomy_level: Mapped[str] = mapped_column(String(30), default="recommend")
    approval_policy: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    capabilities: Mapped[list[str]] = mapped_column(JSON, default=list)
    schedule: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    last_run: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)


class NotificationChannel(EntityMixin, Base):
    __tablename__ = "intelligence_notification_channels"

    owner_id: Mapped[str] = mapped_column(String(160), index=True)
    channel_type: Mapped[str] = mapped_column(String(30))
    label: Mapped[str] = mapped_column(String(120))
    endpoint: Mapped[str | None] = mapped_column(String(1000))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    preferences: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

