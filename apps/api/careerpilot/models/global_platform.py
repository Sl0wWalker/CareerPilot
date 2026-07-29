from typing import Any

from sqlalchemy import JSON, Boolean, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from careerpilot.db.base import Base
from careerpilot.models.profile import EntityMixin


class GlobalPreference(EntityMixin, Base):
    __tablename__ = "global_preferences"
    __table_args__ = (UniqueConstraint("owner_id"),)

    owner_id: Mapped[str] = mapped_column(String(160), index=True)
    locale: Mapped[str] = mapped_column(String(20), default="en-US")
    region: Mapped[str] = mapped_column(String(10), default="US")
    timezone: Mapped[str] = mapped_column(String(80), default="UTC")
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    measurement_system: Mapped[str] = mapped_column(String(12), default="imperial")
    reduced_motion: Mapped[bool] = mapped_column(Boolean, default=False)
    high_contrast: Mapped[bool] = mapped_column(Boolean, default=False)
    regional_job_rules: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)


class ModelRoutingPolicy(EntityMixin, Base):
    __tablename__ = "model_routing_policies"
    __table_args__ = (UniqueConstraint("owner_id", "task_type"),)

    owner_id: Mapped[str] = mapped_column(String(160), index=True)
    task_type: Mapped[str] = mapped_column(String(80))
    local_first: Mapped[bool] = mapped_column(Boolean, default=True)
    allow_cloud_fallback: Mapped[bool] = mapped_column(Boolean, default=False)
    preferred_provider: Mapped[str] = mapped_column(String(80), default="ollama")
    preferred_model: Mapped[str | None] = mapped_column(String(160))
    max_latency_ms: Mapped[int] = mapped_column(default=30000)
    privacy_class: Mapped[str] = mapped_column(String(30), default="sensitive")
    constraints: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)


class MobileEndpoint(EntityMixin, Base):
    __tablename__ = "mobile_endpoints"
    __table_args__ = (UniqueConstraint("owner_id", "device_id"),)

    owner_id: Mapped[str] = mapped_column(String(160), index=True)
    device_id: Mapped[str] = mapped_column(String(160))
    platform: Mapped[str] = mapped_column(String(30))
    push_endpoint: Mapped[str | None] = mapped_column(String(2000))
    locale: Mapped[str] = mapped_column(String(20), default="en-US")
    timezone: Mapped[str] = mapped_column(String(80), default="UTC")
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    capabilities: Mapped[list[str]] = mapped_column(JSON, default=list)


class NotificationDelivery(EntityMixin, Base):
    __tablename__ = "global_notification_deliveries"

    owner_id: Mapped[str] = mapped_column(String(160), index=True)
    endpoint_id: Mapped[str | None] = mapped_column(String(36), index=True)
    category: Mapped[str] = mapped_column(String(80))
    title: Mapped[str] = mapped_column(String(240))
    body: Mapped[str] = mapped_column(String(2000))
    status: Mapped[str] = mapped_column(String(30), default="queued", index=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
