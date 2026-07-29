"""add enterprise platform and agent ecosystem

Revision ID: e15e00000015
Revises: a14c0de00014
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "e15e00000015"
down_revision: str | None = "a14c0de00014"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _entity_columns() -> list[sa.Column]:
    return [
        sa.Column("id", sa.Uuid(native_uuid=False), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    ]


def upgrade() -> None:
    op.create_table(
        "enterprise_organizations",
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("slug", sa.String(80), nullable=False),
        sa.Column("plan", sa.String(40), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("settings", sa.JSON(), nullable=False),
        *_entity_columns(),
        sa.UniqueConstraint("slug"),
    )
    op.create_index("ix_enterprise_organizations_slug", "enterprise_organizations", ["slug"])
    op.create_table(
        "enterprise_workspaces",
        sa.Column(
            "organization_id",
            sa.Uuid(native_uuid=False),
            sa.ForeignKey("enterprise_organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("slug", sa.String(80), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        *_entity_columns(),
        sa.UniqueConstraint("organization_id", "slug"),
    )
    op.create_index(
        "ix_enterprise_workspaces_organization_id",
        "enterprise_workspaces",
        ["organization_id"],
    )
    op.create_table(
        "enterprise_memberships",
        sa.Column(
            "organization_id",
            sa.Uuid(native_uuid=False),
            sa.ForeignKey("enterprise_organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("subject", sa.String(160), nullable=False),
        sa.Column("role", sa.String(40), nullable=False),
        sa.Column("permissions", sa.JSON(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        *_entity_columns(),
        sa.UniqueConstraint("organization_id", "subject"),
    )
    op.create_index(
        "ix_enterprise_memberships_organization_id",
        "enterprise_memberships",
        ["organization_id"],
    )
    op.create_index("ix_enterprise_memberships_subject", "enterprise_memberships", ["subject"])
    op.create_table(
        "enterprise_sso_connections",
        sa.Column(
            "organization_id",
            sa.Uuid(native_uuid=False),
            sa.ForeignKey("enterprise_organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("protocol", sa.String(20), nullable=False),
        sa.Column("issuer", sa.String(1000), nullable=False),
        sa.Column("client_id", sa.String(300)),
        sa.Column("metadata_url", sa.String(1000)),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        *_entity_columns(),
    )
    op.create_index(
        "ix_enterprise_sso_connections_organization_id",
        "enterprise_sso_connections",
        ["organization_id"],
    )
    op.create_table(
        "enterprise_policies",
        sa.Column(
            "organization_id",
            sa.Uuid(native_uuid=False),
            sa.ForeignKey("enterprise_organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("key", sa.String(120), nullable=False),
        sa.Column("value", sa.JSON(), nullable=False),
        sa.Column("enforcement", sa.String(20), nullable=False),
        *_entity_columns(),
        sa.UniqueConstraint("organization_id", "key"),
    )
    op.create_index(
        "ix_enterprise_policies_organization_id",
        "enterprise_policies",
        ["organization_id"],
    )
    op.create_table(
        "enterprise_usage_quotas",
        sa.Column(
            "organization_id",
            sa.Uuid(native_uuid=False),
            sa.ForeignKey("enterprise_organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("metric", sa.String(80), nullable=False),
        sa.Column("limit", sa.Integer(), nullable=False),
        sa.Column("used", sa.Integer(), nullable=False),
        *_entity_columns(),
        sa.UniqueConstraint("organization_id", "metric"),
    )
    op.create_index(
        "ix_enterprise_usage_quotas_organization_id",
        "enterprise_usage_quotas",
        ["organization_id"],
    )
    op.create_table(
        "enterprise_audit_events",
        sa.Column(
            "organization_id",
            sa.Uuid(native_uuid=False),
            sa.ForeignKey("enterprise_organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("actor", sa.String(160), nullable=False),
        sa.Column("action", sa.String(160), nullable=False),
        sa.Column("resource_type", sa.String(100), nullable=False),
        sa.Column("resource_id", sa.String(160)),
        sa.Column("details", sa.JSON(), nullable=False),
        *_entity_columns(),
    )
    for column in ("organization_id", "actor", "action"):
        op.create_index(f"ix_enterprise_audit_events_{column}", "enterprise_audit_events", [column])
    op.create_table(
        "enterprise_agent_runs",
        sa.Column(
            "organization_id",
            sa.Uuid(native_uuid=False),
            sa.ForeignKey("enterprise_organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "workspace_id",
            sa.Uuid(native_uuid=False),
            sa.ForeignKey("enterprise_workspaces.id", ondelete="SET NULL"),
        ),
        sa.Column("agent_type", sa.String(100), nullable=False),
        sa.Column("objective", sa.Text(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column(
            "parent_run_id",
            sa.Uuid(native_uuid=False),
            sa.ForeignKey("enterprise_agent_runs.id", ondelete="SET NULL"),
        ),
        sa.Column("input", sa.JSON(), nullable=False),
        sa.Column("output", sa.JSON(), nullable=False),
        sa.Column("error", sa.Text()),
        *_entity_columns(),
    )
    for column in ("organization_id", "workspace_id", "agent_type", "status"):
        op.create_index(f"ix_enterprise_agent_runs_{column}", "enterprise_agent_runs", [column])
    op.create_table(
        "enterprise_agent_memory",
        sa.Column(
            "organization_id",
            sa.Uuid(native_uuid=False),
            sa.ForeignKey("enterprise_organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("namespace", sa.String(120), nullable=False),
        sa.Column("key", sa.String(200), nullable=False),
        sa.Column("value", sa.JSON(), nullable=False),
        *_entity_columns(),
        sa.UniqueConstraint("organization_id", "namespace", "key"),
    )
    op.create_index(
        "ix_enterprise_agent_memory_organization_id",
        "enterprise_agent_memory",
        ["organization_id"],
    )
    op.create_index(
        "ix_enterprise_agent_memory_namespace", "enterprise_agent_memory", ["namespace"]
    )
    op.create_table(
        "enterprise_licenses",
        sa.Column(
            "organization_id",
            sa.Uuid(native_uuid=False),
            sa.ForeignKey("enterprise_organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("seats", sa.Integer(), nullable=False),
        sa.Column("billing_email", sa.String(320)),
        sa.Column("external_customer_id", sa.String(160)),
        *_entity_columns(),
        sa.UniqueConstraint("organization_id"),
    )
    op.create_index(
        "ix_enterprise_licenses_organization_id",
        "enterprise_licenses",
        ["organization_id"],
    )


def downgrade() -> None:
    for table in (
        "enterprise_licenses",
        "enterprise_agent_memory",
        "enterprise_agent_runs",
        "enterprise_audit_events",
        "enterprise_usage_quotas",
        "enterprise_policies",
        "enterprise_sso_connections",
        "enterprise_memberships",
        "enterprise_workspaces",
        "enterprise_organizations",
    ):
        op.drop_table(table)
