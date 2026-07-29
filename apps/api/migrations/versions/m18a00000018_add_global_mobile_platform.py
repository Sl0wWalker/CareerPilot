"""add global and mobile platform foundations

Revision ID: m18a00000018
Revises: m17a00000017
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "m18a00000018"
down_revision: str | None = "m17a00000017"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def entity():
    return [
        sa.Column("id", sa.Uuid(native_uuid=False), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    ]


def upgrade():
    op.create_table(
        "global_preferences",
        sa.Column("owner_id", sa.String(160), nullable=False, unique=True, index=True),
        sa.Column("locale", sa.String(20), nullable=False),
        sa.Column("region", sa.String(10), nullable=False),
        sa.Column("timezone", sa.String(80), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("measurement_system", sa.String(12), nullable=False),
        sa.Column("reduced_motion", sa.Boolean(), nullable=False),
        sa.Column("high_contrast", sa.Boolean(), nullable=False),
        sa.Column("regional_job_rules", sa.JSON(), nullable=False),
        *entity(),
    )
    op.create_table(
        "model_routing_policies",
        sa.Column("owner_id", sa.String(160), nullable=False, index=True),
        sa.Column("task_type", sa.String(80), nullable=False),
        sa.Column("local_first", sa.Boolean(), nullable=False),
        sa.Column("allow_cloud_fallback", sa.Boolean(), nullable=False),
        sa.Column("preferred_provider", sa.String(80), nullable=False),
        sa.Column("preferred_model", sa.String(160)),
        sa.Column("max_latency_ms", sa.Integer(), nullable=False),
        sa.Column("privacy_class", sa.String(30), nullable=False),
        sa.Column("constraints", sa.JSON(), nullable=False),
        *entity(),
        sa.UniqueConstraint("owner_id", "task_type"),
    )
    op.create_table(
        "mobile_endpoints",
        sa.Column("owner_id", sa.String(160), nullable=False, index=True),
        sa.Column("device_id", sa.String(160), nullable=False),
        sa.Column("platform", sa.String(30), nullable=False),
        sa.Column("push_endpoint", sa.String(2000)),
        sa.Column("locale", sa.String(20), nullable=False),
        sa.Column("timezone", sa.String(80), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("capabilities", sa.JSON(), nullable=False),
        *entity(),
        sa.UniqueConstraint("owner_id", "device_id"),
    )
    op.create_table(
        "global_notification_deliveries",
        sa.Column("owner_id", sa.String(160), nullable=False, index=True),
        sa.Column("endpoint_id", sa.String(36), index=True),
        sa.Column("category", sa.String(80), nullable=False),
        sa.Column("title", sa.String(240), nullable=False),
        sa.Column("body", sa.String(2000), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, index=True),
        sa.Column("payload", sa.JSON(), nullable=False),
        *entity(),
    )


def downgrade():
    for table in (
        "global_notification_deliveries",
        "mobile_endpoints",
        "model_routing_policies",
        "global_preferences",
    ):
        op.drop_table(table)
