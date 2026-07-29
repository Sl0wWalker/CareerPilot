from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from careerpilot.db.base import Base
from careerpilot.models.profile import EntityMixin


class BetaPreference(EntityMixin, Base):
    __tablename__ = "beta_preferences"

    user_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    enrolled: Mapped[bool] = mapped_column(Boolean, default=False)
    diagnostics_opt_in: Mapped[bool] = mapped_column(Boolean, default=False)
    analytics_opt_in: Mapped[bool] = mapped_column(Boolean, default=False)
    release_channel: Mapped[str] = mapped_column(String(20), default="stable")
    onboarding_completed: Mapped[bool] = mapped_column(Boolean, default=False)


class FeedbackItem(EntityMixin, Base):
    __tablename__ = "feedback_items"

    user_id: Mapped[str] = mapped_column(String(64), index=True)
    kind: Mapped[str] = mapped_column(String(30), index=True)
    title: Mapped[str] = mapped_column(String(240))
    description: Mapped[str] = mapped_column(Text)
    severity: Mapped[str] = mapped_column(String(20), default="normal")
    status: Mapped[str] = mapped_column(String(30), default="new", index=True)
    page_url: Mapped[str | None] = mapped_column(String(1000))
    diagnostics_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    votes: Mapped[int] = mapped_column(Integer, default=1)


class SatisfactionResponse(EntityMixin, Base):
    __tablename__ = "satisfaction_responses"

    user_id: Mapped[str] = mapped_column(String(64), index=True)
    score: Mapped[int] = mapped_column(Integer)
    comment: Mapped[str | None] = mapped_column(Text)
    context: Mapped[str | None] = mapped_column(String(120))


class UsageEvent(EntityMixin, Base):
    __tablename__ = "usage_events"

    anonymous_id: Mapped[str] = mapped_column(String(64), index=True)
    event_name: Mapped[str] = mapped_column(String(120), index=True)
    properties_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)


class FeatureFlag(EntityMixin, Base):
    __tablename__ = "feature_flags"

    key: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    beta_only: Mapped[bool] = mapped_column(Boolean, default=False)
    rollout_percentage: Mapped[int] = mapped_column(Integer, default=100)
    config_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)


class Experiment(EntityMixin, Base):
    __tablename__ = "experiments"

    key: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    flag_id: Mapped[UUID | None] = mapped_column(
        Uuid(native_uuid=False), ForeignKey("feature_flags.id", ondelete="SET NULL")
    )
    status: Mapped[str] = mapped_column(String(20), default="draft")
    variants_json: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ExperimentAssignment(EntityMixin, Base):
    __tablename__ = "experiment_assignments"

    experiment_id: Mapped[UUID] = mapped_column(
        Uuid(native_uuid=False), ForeignKey("experiments.id", ondelete="CASCADE"), index=True
    )
    anonymous_id: Mapped[str] = mapped_column(String(64), index=True)
    variant: Mapped[str] = mapped_column(String(80))

