"""add beta feedback platform

Revision ID: d11b3ta00011
Revises: ca91d9a22e10
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d11b3ta00011"
down_revision: str | None = "ca91d9a22e10"
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
        "beta_preferences",
        *entity_columns(),
        sa.Column("user_id", sa.String(64), nullable=False),
        sa.Column("enrolled", sa.Boolean(), nullable=False),
        sa.Column("diagnostics_opt_in", sa.Boolean(), nullable=False),
        sa.Column("analytics_opt_in", sa.Boolean(), nullable=False),
        sa.Column("release_channel", sa.String(20), nullable=False),
        sa.Column("onboarding_completed", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index("ix_beta_preferences_user_id", "beta_preferences", ["user_id"])
    op.create_table(
        "feedback_items",
        *entity_columns(),
        sa.Column("user_id", sa.String(64), nullable=False),
        sa.Column("kind", sa.String(30), nullable=False),
        sa.Column("title", sa.String(240), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("page_url", sa.String(1000)),
        sa.Column("diagnostics_json", sa.JSON(), nullable=False),
        sa.Column("votes", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_feedback_items_user_id", "feedback_items", ["user_id"])
    op.create_index("ix_feedback_items_kind", "feedback_items", ["kind"])
    op.create_index("ix_feedback_items_status", "feedback_items", ["status"])
    op.create_table(
        "satisfaction_responses",
        *entity_columns(),
        sa.Column("user_id", sa.String(64), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("comment", sa.Text()),
        sa.Column("context", sa.String(120)),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_satisfaction_responses_user_id", "satisfaction_responses", ["user_id"])
    op.create_table(
        "usage_events",
        *entity_columns(),
        sa.Column("anonymous_id", sa.String(64), nullable=False),
        sa.Column("event_name", sa.String(120), nullable=False),
        sa.Column("properties_json", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_usage_events_anonymous_id", "usage_events", ["anonymous_id"])
    op.create_index("ix_usage_events_event_name", "usage_events", ["event_name"])
    op.create_table(
        "feature_flags",
        *entity_columns(),
        sa.Column("key", sa.String(120), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("beta_only", sa.Boolean(), nullable=False),
        sa.Column("rollout_percentage", sa.Integer(), nullable=False),
        sa.Column("config_json", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("key"),
    )
    op.create_index("ix_feature_flags_key", "feature_flags", ["key"])
    op.create_table(
        "experiments",
        *entity_columns(),
        sa.Column("key", sa.String(120), nullable=False),
        sa.Column("flag_id", sa.Uuid(), sa.ForeignKey("feature_flags.id", ondelete="SET NULL")),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("variants_json", sa.JSON(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("ended_at", sa.DateTime(timezone=True)),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("key"),
    )
    op.create_index("ix_experiments_key", "experiments", ["key"])
    op.create_table(
        "experiment_assignments",
        *entity_columns(),
        sa.Column(
            "experiment_id",
            sa.Uuid(),
            sa.ForeignKey("experiments.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("anonymous_id", sa.String(64), nullable=False),
        sa.Column("variant", sa.String(80), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_experiment_assignments_experiment_id",
        "experiment_assignments",
        ["experiment_id"],
    )
    op.create_index(
        "ix_experiment_assignments_anonymous_id",
        "experiment_assignments",
        ["anonymous_id"],
    )


def downgrade() -> None:
    for table in (
        "experiment_assignments",
        "experiments",
        "feature_flags",
        "usage_events",
        "satisfaction_responses",
        "feedback_items",
        "beta_preferences",
    ):
        op.drop_table(table)

