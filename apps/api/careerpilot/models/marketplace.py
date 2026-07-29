from typing import Any
from uuid import UUID

from sqlalchemy import (
    JSON,
    Boolean,
    Float,
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


class MarketplacePackage(EntityMixin, Base):
    __tablename__ = "marketplace_packages"
    __table_args__ = (UniqueConstraint("slug", "version"),)

    publisher_id: Mapped[str] = mapped_column(String(160), index=True)
    slug: Mapped[str] = mapped_column(String(160), index=True)
    name: Mapped[str] = mapped_column(String(200))
    summary: Mapped[str] = mapped_column(Text)
    package_type: Mapped[str] = mapped_column(String(40), index=True)
    version: Mapped[str] = mapped_column(String(40))
    channel: Mapped[str] = mapped_column(String(24), default="stable", index=True)
    manifest: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    dependencies: Mapped[list[dict[str, str]]] = mapped_column(JSON, default=list)
    permissions: Mapped[list[str]] = mapped_column(JSON, default=list)
    signature: Mapped[str] = mapped_column(String(128))
    published: Mapped[bool] = mapped_column(Boolean, default=False)
    rating: Mapped[float] = mapped_column(Float, default=0)
    rating_count: Mapped[int] = mapped_column(Integer, default=0)


class PackageInstallation(EntityMixin, Base):
    __tablename__ = "marketplace_installations"
    __table_args__ = (UniqueConstraint("owner_id", "package_slug"),)

    owner_id: Mapped[str] = mapped_column(String(160), index=True)
    package_id: Mapped[UUID] = mapped_column(
        Uuid(native_uuid=False),
        ForeignKey("marketplace_packages.id", ondelete="CASCADE"),
        index=True,
    )
    package_slug: Mapped[str] = mapped_column(String(160), index=True)
    installed_version: Mapped[str] = mapped_column(String(40))
    channel: Mapped[str] = mapped_column(String(24), default="stable")
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    configuration: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)


class PackageReview(EntityMixin, Base):
    __tablename__ = "marketplace_reviews"
    __table_args__ = (UniqueConstraint("package_id", "reviewer_id"),)

    package_id: Mapped[UUID] = mapped_column(
        Uuid(native_uuid=False),
        ForeignKey("marketplace_packages.id", ondelete="CASCADE"),
        index=True,
    )
    reviewer_id: Mapped[str] = mapped_column(String(160), index=True)
    rating: Mapped[int] = mapped_column(Integer)
    body: Mapped[str] = mapped_column(Text, default="")


class WorkflowDefinition(EntityMixin, Base):
    __tablename__ = "automation_workflows"

    owner_id: Mapped[str] = mapped_column(String(160), index=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    version: Mapped[int] = mapped_column(Integer, default=1)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    trigger_type: Mapped[str] = mapped_column(String(60), default="manual")
    graph: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)


class WorkflowExecution(EntityMixin, Base):
    __tablename__ = "automation_workflow_executions"

    workflow_id: Mapped[UUID] = mapped_column(
        Uuid(native_uuid=False),
        ForeignKey("automation_workflows.id", ondelete="CASCADE"),
        index=True,
    )
    owner_id: Mapped[str] = mapped_column(String(160), index=True)
    status: Mapped[str] = mapped_column(String(30), default="pending", index=True)
    current_node: Mapped[str | None] = mapped_column(String(120))
    context: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    output: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    error: Mapped[str | None] = mapped_column(Text)
