from typing import Any
from uuid import UUID

from sqlalchemy import JSON, Boolean, ForeignKey, Integer, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from careerpilot.db.base import Base
from careerpilot.models.profile import EntityMixin


class Organization(EntityMixin, Base):
    __tablename__ = "enterprise_organizations"

    name: Mapped[str] = mapped_column(String(200))
    slug: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    plan: Mapped[str] = mapped_column(String(40), default="enterprise")
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    settings: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)


class Workspace(EntityMixin, Base):
    __tablename__ = "enterprise_workspaces"
    __table_args__ = (UniqueConstraint("organization_id", "slug"),)

    organization_id: Mapped[UUID] = mapped_column(
        Uuid(native_uuid=False),
        ForeignKey("enterprise_organizations.id", ondelete="CASCADE"),
        index=True,
    )
    name: Mapped[str] = mapped_column(String(200))
    slug: Mapped[str] = mapped_column(String(80))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)


class Membership(EntityMixin, Base):
    __tablename__ = "enterprise_memberships"
    __table_args__ = (UniqueConstraint("organization_id", "subject"),)

    organization_id: Mapped[UUID] = mapped_column(
        Uuid(native_uuid=False),
        ForeignKey("enterprise_organizations.id", ondelete="CASCADE"),
        index=True,
    )
    subject: Mapped[str] = mapped_column(String(160), index=True)
    role: Mapped[str] = mapped_column(String(40), default="member")
    permissions: Mapped[list[str]] = mapped_column(JSON, default=list)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)


class SSOConnection(EntityMixin, Base):
    __tablename__ = "enterprise_sso_connections"

    organization_id: Mapped[UUID] = mapped_column(
        Uuid(native_uuid=False),
        ForeignKey("enterprise_organizations.id", ondelete="CASCADE"),
        index=True,
    )
    protocol: Mapped[str] = mapped_column(String(20))
    issuer: Mapped[str] = mapped_column(String(1000))
    client_id: Mapped[str | None] = mapped_column(String(300))
    metadata_url: Mapped[str | None] = mapped_column(String(1000))
    enabled: Mapped[bool] = mapped_column(Boolean, default=False)


class EnterprisePolicy(EntityMixin, Base):
    __tablename__ = "enterprise_policies"
    __table_args__ = (UniqueConstraint("organization_id", "key"),)

    organization_id: Mapped[UUID] = mapped_column(
        Uuid(native_uuid=False),
        ForeignKey("enterprise_organizations.id", ondelete="CASCADE"),
        index=True,
    )
    key: Mapped[str] = mapped_column(String(120))
    value: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    enforcement: Mapped[str] = mapped_column(String(20), default="enforce")


class UsageQuota(EntityMixin, Base):
    __tablename__ = "enterprise_usage_quotas"
    __table_args__ = (UniqueConstraint("organization_id", "metric"),)

    organization_id: Mapped[UUID] = mapped_column(
        Uuid(native_uuid=False),
        ForeignKey("enterprise_organizations.id", ondelete="CASCADE"),
        index=True,
    )
    metric: Mapped[str] = mapped_column(String(80))
    limit: Mapped[int] = mapped_column(Integer)
    used: Mapped[int] = mapped_column(Integer, default=0)


class AuditEvent(EntityMixin, Base):
    __tablename__ = "enterprise_audit_events"

    organization_id: Mapped[UUID] = mapped_column(
        Uuid(native_uuid=False),
        ForeignKey("enterprise_organizations.id", ondelete="CASCADE"),
        index=True,
    )
    actor: Mapped[str] = mapped_column(String(160), index=True)
    action: Mapped[str] = mapped_column(String(160), index=True)
    resource_type: Mapped[str] = mapped_column(String(100))
    resource_id: Mapped[str | None] = mapped_column(String(160))
    details: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)


class AgentRun(EntityMixin, Base):
    __tablename__ = "enterprise_agent_runs"

    organization_id: Mapped[UUID] = mapped_column(
        Uuid(native_uuid=False),
        ForeignKey("enterprise_organizations.id", ondelete="CASCADE"),
        index=True,
    )
    workspace_id: Mapped[UUID | None] = mapped_column(
        Uuid(native_uuid=False),
        ForeignKey("enterprise_workspaces.id", ondelete="SET NULL"),
        index=True,
    )
    agent_type: Mapped[str] = mapped_column(String(100), index=True)
    objective: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default="queued", index=True)
    parent_run_id: Mapped[UUID | None] = mapped_column(
        Uuid(native_uuid=False), ForeignKey("enterprise_agent_runs.id", ondelete="SET NULL")
    )
    input: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    output: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    error: Mapped[str | None] = mapped_column(Text)


class AgentMemory(EntityMixin, Base):
    __tablename__ = "enterprise_agent_memory"
    __table_args__ = (UniqueConstraint("organization_id", "namespace", "key"),)

    organization_id: Mapped[UUID] = mapped_column(
        Uuid(native_uuid=False),
        ForeignKey("enterprise_organizations.id", ondelete="CASCADE"),
        index=True,
    )
    namespace: Mapped[str] = mapped_column(String(120), index=True)
    key: Mapped[str] = mapped_column(String(200))
    value: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)


class License(EntityMixin, Base):
    __tablename__ = "enterprise_licenses"

    organization_id: Mapped[UUID] = mapped_column(
        Uuid(native_uuid=False),
        ForeignKey("enterprise_organizations.id", ondelete="CASCADE"),
        unique=True,
        index=True,
    )
    status: Mapped[str] = mapped_column(String(30), default="trial")
    seats: Mapped[int] = mapped_column(Integer, default=5)
    billing_email: Mapped[str | None] = mapped_column(String(320))
    external_customer_id: Mapped[str | None] = mapped_column(String(160))
