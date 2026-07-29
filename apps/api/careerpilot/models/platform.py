from typing import Any
from uuid import UUID

from sqlalchemy import JSON, Boolean, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from careerpilot.db.base import Base
from careerpilot.models.profile import EntityMixin


class ApiKey(EntityMixin, Base):
    __tablename__ = "platform_api_keys"

    owner_id: Mapped[str] = mapped_column(String(64), index=True)
    name: Mapped[str] = mapped_column(String(120))
    prefix: Mapped[str] = mapped_column(String(16), unique=True, index=True)
    secret_hash: Mapped[str] = mapped_column(String(128))
    scopes: Mapped[list[str]] = mapped_column(JSON, default=list)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)


class WebhookSubscription(EntityMixin, Base):
    __tablename__ = "platform_webhook_subscriptions"

    owner_id: Mapped[str] = mapped_column(String(64), index=True)
    url: Mapped[str] = mapped_column(String(1000))
    event_types: Mapped[list[str]] = mapped_column(JSON, default=list)
    secret: Mapped[str] = mapped_column(String(128))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    description: Mapped[str] = mapped_column(Text, default="")


class WebhookDelivery(EntityMixin, Base):
    __tablename__ = "platform_webhook_deliveries"

    subscription_id: Mapped[UUID] = mapped_column(
        Uuid(native_uuid=False),
        ForeignKey("platform_webhook_subscriptions.id", ondelete="CASCADE"),
        index=True,
    )
    event_type: Mapped[str] = mapped_column(String(160), index=True)
    status: Mapped[str] = mapped_column(String(30), default="pending")
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    response_code: Mapped[str | None] = mapped_column(String(12))
    error: Mapped[str | None] = mapped_column(Text)


class PluginInstallation(EntityMixin, Base):
    __tablename__ = "platform_plugin_installations"

    owner_id: Mapped[str] = mapped_column(String(64), index=True)
    plugin_id: Mapped[str] = mapped_column(String(160), index=True)
    name: Mapped[str] = mapped_column(String(200))
    version: Mapped[str] = mapped_column(String(40))
    plugin_type: Mapped[str] = mapped_column(String(40), index=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    configuration: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

