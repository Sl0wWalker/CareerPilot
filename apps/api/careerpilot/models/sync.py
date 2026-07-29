from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from careerpilot.db.base import Base
from careerpilot.models.profile import EntityMixin


class SyncDevice(EntityMixin, Base):
    __tablename__ = "sync_devices"
    __table_args__ = (UniqueConstraint("user_id", "device_key"),)

    user_id: Mapped[str] = mapped_column(String(64), index=True)
    device_key: Mapped[str] = mapped_column(String(128))
    display_name: Mapped[str] = mapped_column(String(120))
    platform: Mapped[str] = mapped_column(String(60), default="unknown")
    last_cursor: Mapped[int] = mapped_column(Integer, default=0)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)


class SyncChange(EntityMixin, Base):
    __tablename__ = "sync_changes"
    __table_args__ = (UniqueConstraint("user_id", "entity_type", "entity_key", "revision"),)

    user_id: Mapped[str] = mapped_column(String(64), index=True)
    device_id: Mapped[UUID | None] = mapped_column(
        Uuid(native_uuid=False), ForeignKey("sync_devices.id", ondelete="SET NULL"), index=True
    )
    entity_type: Mapped[str] = mapped_column(String(60), index=True)
    entity_key: Mapped[str] = mapped_column(String(128), index=True)
    operation: Mapped[str] = mapped_column(String(20))
    revision: Mapped[int] = mapped_column(Integer)
    base_revision: Mapped[int] = mapped_column(Integer, default=0)
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    checksum: Mapped[str] = mapped_column(String(64))


class SyncConflict(EntityMixin, Base):
    __tablename__ = "sync_conflicts"

    user_id: Mapped[str] = mapped_column(String(64), index=True)
    entity_type: Mapped[str] = mapped_column(String(60))
    entity_key: Mapped[str] = mapped_column(String(128))
    local_change_id: Mapped[UUID] = mapped_column(
        Uuid(native_uuid=False), ForeignKey("sync_changes.id", ondelete="CASCADE")
    )
    remote_change_id: Mapped[UUID] = mapped_column(
        Uuid(native_uuid=False), ForeignKey("sync_changes.id", ondelete="CASCADE")
    )
    status: Mapped[str] = mapped_column(String(20), default="open", index=True)
    resolution: Mapped[str | None] = mapped_column(String(30))
    resolved_payload_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)


class ConnectedAccount(EntityMixin, Base):
    __tablename__ = "connected_accounts"
    __table_args__ = (UniqueConstraint("user_id", "provider", "external_account_id"),)

    user_id: Mapped[str] = mapped_column(String(64), index=True)
    provider: Mapped[str] = mapped_column(String(40), index=True)
    external_account_id: Mapped[str] = mapped_column(String(240))
    display_name: Mapped[str] = mapped_column(String(240))
    scopes_json: Mapped[list[str]] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    credential_reference: Mapped[str | None] = mapped_column(String(500))
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_message: Mapped[str | None] = mapped_column(Text)


class Workspace(EntityMixin, Base):
    __tablename__ = "workspaces"

    owner_id: Mapped[str] = mapped_column(String(64), index=True)
    name: Mapped[str] = mapped_column(String(160))
    description: Mapped[str] = mapped_column(Text, default="")


class WorkspaceMember(EntityMixin, Base):
    __tablename__ = "workspace_members"
    __table_args__ = (UniqueConstraint("workspace_id", "user_id"),)

    workspace_id: Mapped[UUID] = mapped_column(
        Uuid(native_uuid=False), ForeignKey("workspaces.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[str] = mapped_column(String(64), index=True)
    role: Mapped[str] = mapped_column(String(20), default="viewer")
    permissions_json: Mapped[list[str]] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(20), default="active")


class WebhookEndpoint(EntityMixin, Base):
    __tablename__ = "webhook_endpoints"

    user_id: Mapped[str] = mapped_column(String(64), index=True)
    url: Mapped[str] = mapped_column(String(1000))
    events_json: Mapped[list[str]] = mapped_column(JSON, default=list)
    secret_reference: Mapped[str | None] = mapped_column(String(500))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)

