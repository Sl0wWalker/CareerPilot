"""add platform APIs and extensibility

Revision ID: a14c0de00014
Revises: f13c0ac00013
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a14c0de00014"
down_revision: str | None = "f13c0ac00013"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "platform_api_keys",
        sa.Column("owner_id", sa.String(64), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("prefix", sa.String(16), nullable=False),
        sa.Column("secret_hash", sa.String(128), nullable=False),
        sa.Column("scopes", sa.JSON(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("id", sa.Uuid(native_uuid=False), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("prefix"),
    )
    op.create_index("ix_platform_api_keys_owner_id", "platform_api_keys", ["owner_id"])
    op.create_index("ix_platform_api_keys_prefix", "platform_api_keys", ["prefix"])
    op.create_table(
        "platform_webhook_subscriptions",
        sa.Column("owner_id", sa.String(64), nullable=False),
        sa.Column("url", sa.String(1000), nullable=False),
        sa.Column("event_types", sa.JSON(), nullable=False),
        sa.Column("secret", sa.String(128), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("id", sa.Uuid(native_uuid=False), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_platform_webhook_subscriptions_owner_id",
        "platform_webhook_subscriptions",
        ["owner_id"],
    )
    op.create_table(
        "platform_plugin_installations",
        sa.Column("owner_id", sa.String(64), nullable=False),
        sa.Column("plugin_id", sa.String(160), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("version", sa.String(40), nullable=False),
        sa.Column("plugin_type", sa.String(40), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("configuration", sa.JSON(), nullable=False),
        sa.Column("id", sa.Uuid(native_uuid=False), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_platform_plugin_installations_owner_id",
        "platform_plugin_installations",
        ["owner_id"],
    )
    op.create_index(
        "ix_platform_plugin_installations_plugin_id",
        "platform_plugin_installations",
        ["plugin_id"],
    )
    op.create_index(
        "ix_platform_plugin_installations_plugin_type",
        "platform_plugin_installations",
        ["plugin_type"],
    )
    op.create_table(
        "platform_webhook_deliveries",
        sa.Column(
            "subscription_id",
            sa.Uuid(native_uuid=False),
            sa.ForeignKey("platform_webhook_subscriptions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("event_type", sa.String(160), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("response_code", sa.String(12)),
        sa.Column("error", sa.Text()),
        sa.Column("id", sa.Uuid(native_uuid=False), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_platform_webhook_deliveries_subscription_id",
        "platform_webhook_deliveries",
        ["subscription_id"],
    )
    op.create_index(
        "ix_platform_webhook_deliveries_event_type",
        "platform_webhook_deliveries",
        ["event_type"],
    )


def downgrade() -> None:
    op.drop_table("platform_webhook_deliveries")
    op.drop_table("platform_plugin_installations")
    op.drop_table("platform_webhook_subscriptions")
    op.drop_table("platform_api_keys")
