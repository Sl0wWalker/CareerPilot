"""add innovation lab and AI research platform

Revision ID: m19a00000019
Revises: m18a00000018
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "m19a00000019"
down_revision: str | None = "m18a00000018"
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
        "research_experiments",
        sa.Column("owner_id", sa.String(160), nullable=False, index=True),
        sa.Column("slug", sa.String(100), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("hypothesis", sa.Text(), nullable=False),
        sa.Column("category", sa.String(50), nullable=False, index=True),
        sa.Column("status", sa.String(30), nullable=False, index=True),
        sa.Column("feature_flag", sa.String(120), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("production_safe", sa.Boolean(), nullable=False),
        sa.Column("config", sa.JSON(), nullable=False),
        sa.Column("success_criteria", sa.JSON(), nullable=False),
        *entity(),
        sa.UniqueConstraint("owner_id", "slug"),
    )
    op.create_table(
        "research_evaluation_datasets",
        sa.Column("owner_id", sa.String(160), nullable=False, index=True),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("version", sa.String(40), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("modality", sa.String(40), nullable=False),
        sa.Column("item_count", sa.Integer(), nullable=False),
        sa.Column("schema_definition", sa.JSON(), nullable=False),
        sa.Column("provenance", sa.JSON(), nullable=False),
        sa.Column("contains_sensitive_data", sa.Boolean(), nullable=False),
        *entity(),
        sa.UniqueConstraint("owner_id", "name", "version"),
    )
    op.create_table(
        "research_experiment_runs",
        sa.Column("owner_id", sa.String(160), nullable=False, index=True),
        sa.Column(
            "experiment_id",
            sa.String(36),
            sa.ForeignKey("research_experiments.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "dataset_id",
            sa.String(36),
            sa.ForeignKey("research_evaluation_datasets.id", ondelete="SET NULL"),
            index=True,
        ),
        sa.Column("model_provider", sa.String(80), nullable=False),
        sa.Column("model_name", sa.String(160), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, index=True),
        sa.Column("parameters", sa.JSON(), nullable=False),
        sa.Column("metrics", sa.JSON(), nullable=False),
        sa.Column("safety_results", sa.JSON(), nullable=False),
        sa.Column("latency_ms", sa.Float()),
        sa.Column("cost_estimate", sa.Float(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=False),
        *entity(),
    )
    op.create_table(
        "research_incubated_features",
        sa.Column("owner_id", sa.String(160), nullable=False, index=True),
        sa.Column("key", sa.String(120), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("stage", sa.String(30), nullable=False, index=True),
        sa.Column(
            "experiment_id",
            sa.String(36),
            sa.ForeignKey("research_experiments.id", ondelete="SET NULL"),
        ),
        sa.Column("rollout_percentage", sa.Integer(), nullable=False),
        sa.Column("safety_approved", sa.Boolean(), nullable=False),
        sa.Column("promotion_evidence", sa.JSON(), nullable=False),
        *entity(),
        sa.UniqueConstraint("owner_id", "key"),
    )


def downgrade():
    for table in (
        "research_incubated_features",
        "research_experiment_runs",
        "research_evaluation_datasets",
        "research_experiments",
    ):
        op.drop_table(table)
