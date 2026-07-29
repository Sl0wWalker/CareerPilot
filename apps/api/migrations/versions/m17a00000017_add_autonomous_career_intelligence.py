"""add autonomous career intelligence

Revision ID: m17a00000017
Revises: m16a00000016
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "m17a00000017"
down_revision: str | None = "m16a00000016"
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
        "career_strategies",
        sa.Column("owner_id", sa.String(160), nullable=False, index=True),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("horizon_months", sa.Integer(), nullable=False),
        sa.Column("target_roles", sa.JSON(), nullable=False),
        sa.Column("objectives", sa.JSON(), nullable=False),
        sa.Column("constraints", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        *entity(),
    )
    op.create_table(
        "opportunity_monitors",
        sa.Column("owner_id", sa.String(160), nullable=False, index=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("criteria", sa.JSON(), nullable=False),
        sa.Column("cadence", sa.String(30), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("last_checked_at", sa.DateTime(timezone=True)),
        sa.Column("last_result", sa.JSON(), nullable=False),
        *entity(),
    )
    op.create_table(
        "skill_forecasts",
        sa.Column("owner_id", sa.String(160), nullable=False, index=True),
        sa.Column("skill", sa.String(120), nullable=False),
        sa.Column("current_demand", sa.Float(), nullable=False),
        sa.Column("projected_demand", sa.Float(), nullable=False),
        sa.Column("trend", sa.String(30), nullable=False),
        sa.Column("evidence", sa.JSON(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        *entity(),
        sa.UniqueConstraint("owner_id", "skill"),
    )
    op.create_table(
        "market_insights",
        sa.Column("owner_id", sa.String(160), nullable=False, index=True),
        sa.Column("insight_type", sa.String(60), nullable=False, index=True),
        sa.Column("title", sa.String(240), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("metrics", sa.JSON(), nullable=False),
        sa.Column("sources", sa.JSON(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        *entity(),
    )
    op.create_table(
        "autonomous_agent_configs",
        sa.Column("owner_id", sa.String(160), nullable=False, index=True),
        sa.Column("agent_key", sa.String(120), nullable=False),
        sa.Column("display_name", sa.String(200), nullable=False),
        sa.Column("objective", sa.Text(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("autonomy_level", sa.String(30), nullable=False),
        sa.Column("approval_policy", sa.JSON(), nullable=False),
        sa.Column("capabilities", sa.JSON(), nullable=False),
        sa.Column("schedule", sa.JSON(), nullable=False),
        sa.Column("last_run", sa.JSON(), nullable=False),
        *entity(),
        sa.UniqueConstraint("owner_id", "agent_key"),
    )
    op.create_table(
        "intelligence_notification_channels",
        sa.Column("owner_id", sa.String(160), nullable=False, index=True),
        sa.Column("channel_type", sa.String(30), nullable=False),
        sa.Column("label", sa.String(120), nullable=False),
        sa.Column("endpoint", sa.String(1000)),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("preferences", sa.JSON(), nullable=False),
        *entity(),
    )


def downgrade():
    for table in (
        "intelligence_notification_channels",
        "autonomous_agent_configs",
        "market_insights",
        "skill_forecasts",
        "opportunity_monitors",
        "career_strategies",
    ):
        op.drop_table(table)

