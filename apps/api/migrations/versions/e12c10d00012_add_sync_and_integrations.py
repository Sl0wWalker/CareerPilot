"""add cloud sync and ecosystem integrations

Revision ID: e12c10d00012
Revises: d11b3ta00011
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "e12c10d00012"
down_revision: str | None = "d11b3ta00011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def entity_columns() -> list[sa.Column]:
    return [
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    ]


def upgrade() -> None:
    op.create_table(
        "sync_devices",
        *entity_columns(),
        sa.Column("user_id", sa.String(64), nullable=False),
        sa.Column("device_key", sa.String(128), nullable=False),
        sa.Column("display_name", sa.String(120), nullable=False),
        sa.Column("platform", sa.String(60), nullable=False),
        sa.Column("last_cursor", sa.Integer(), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True)),
        sa.Column("revoked", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "device_key"),
    )
    op.create_index("ix_sync_devices_user_id", "sync_devices", ["user_id"])
    op.create_table(
        "sync_changes",
        *entity_columns(),
        sa.Column("user_id", sa.String(64), nullable=False),
        sa.Column("device_id", sa.Uuid(), sa.ForeignKey("sync_devices.id", ondelete="SET NULL")),
        sa.Column("entity_type", sa.String(60), nullable=False),
        sa.Column("entity_key", sa.String(128), nullable=False),
        sa.Column("operation", sa.String(20), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("base_revision", sa.Integer(), nullable=False),
        sa.Column("payload_json", sa.JSON(), nullable=False),
        sa.Column("checksum", sa.String(64), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "entity_type", "entity_key", "revision"),
    )
    for column in ("user_id", "device_id", "entity_type", "entity_key"):
        op.create_index(f"ix_sync_changes_{column}", "sync_changes", [column])
    op.create_table(
        "sync_conflicts",
        *entity_columns(),
        sa.Column("user_id", sa.String(64), nullable=False),
        sa.Column("entity_type", sa.String(60), nullable=False),
        sa.Column("entity_key", sa.String(128), nullable=False),
        sa.Column(
            "local_change_id",
            sa.Uuid(),
            sa.ForeignKey("sync_changes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "remote_change_id",
            sa.Uuid(),
            sa.ForeignKey("sync_changes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("resolution", sa.String(30)),
        sa.Column("resolved_payload_json", sa.JSON()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_sync_conflicts_user_id", "sync_conflicts", ["user_id"])
    op.create_index("ix_sync_conflicts_status", "sync_conflicts", ["status"])
    op.create_table(
        "connected_accounts",
        *entity_columns(),
        sa.Column("user_id", sa.String(64), nullable=False),
        sa.Column("provider", sa.String(40), nullable=False),
        sa.Column("external_account_id", sa.String(240), nullable=False),
        sa.Column("display_name", sa.String(240), nullable=False),
        sa.Column("scopes_json", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("credential_reference", sa.String(500)),
        sa.Column("last_synced_at", sa.DateTime(timezone=True)),
        sa.Column("error_message", sa.Text()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "provider", "external_account_id"),
    )
    op.create_index("ix_connected_accounts_user_id", "connected_accounts", ["user_id"])
    op.create_index("ix_connected_accounts_provider", "connected_accounts", ["provider"])
    op.create_table(
        "workspaces",
        *entity_columns(),
        sa.Column("owner_id", sa.String(64), nullable=False),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_workspaces_owner_id", "workspaces", ["owner_id"])
    op.create_table(
        "workspace_members",
        *entity_columns(),
        sa.Column(
            "workspace_id",
            sa.Uuid(),
            sa.ForeignKey("workspaces.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("user_id", sa.String(64), nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("permissions_json", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("workspace_id", "user_id"),
    )
    op.create_index("ix_workspace_members_workspace_id", "workspace_members", ["workspace_id"])
    op.create_index("ix_workspace_members_user_id", "workspace_members", ["user_id"])
    op.create_table(
        "webhook_endpoints",
        *entity_columns(),
        sa.Column("user_id", sa.String(64), nullable=False),
        sa.Column("url", sa.String(1000), nullable=False),
        sa.Column("events_json", sa.JSON(), nullable=False),
        sa.Column("secret_reference", sa.String(500)),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_webhook_endpoints_user_id", "webhook_endpoints", ["user_id"])


def downgrade() -> None:
    for table in (
        "webhook_endpoints",
        "workspace_members",
        "workspaces",
        "connected_accounts",
        "sync_conflicts",
        "sync_changes",
        "sync_devices",
    ):
        op.drop_table(table)
