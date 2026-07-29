"""add marketplace and automation studio

Revision ID: m16a00000016
Revises: e15e00000015
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "m16a00000016"
down_revision: str | None = "e15e00000015"
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
        "marketplace_packages",
        sa.Column("publisher_id", sa.String(160), nullable=False),
        sa.Column("slug", sa.String(160), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("package_type", sa.String(40), nullable=False),
        sa.Column("version", sa.String(40), nullable=False),
        sa.Column("channel", sa.String(24), nullable=False),
        sa.Column("manifest", sa.JSON(), nullable=False),
        sa.Column("dependencies", sa.JSON(), nullable=False),
        sa.Column("permissions", sa.JSON(), nullable=False),
        sa.Column("signature", sa.String(128), nullable=False),
        sa.Column("published", sa.Boolean(), nullable=False),
        sa.Column("rating", sa.Float(), nullable=False),
        sa.Column("rating_count", sa.Integer(), nullable=False),
        *entity(),
        sa.UniqueConstraint("slug", "version"),
    )
    op.create_table(
        "marketplace_installations",
        sa.Column("owner_id", sa.String(160), nullable=False),
        sa.Column(
            "package_id",
            sa.Uuid(native_uuid=False),
            sa.ForeignKey("marketplace_packages.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("package_slug", sa.String(160), nullable=False),
        sa.Column("installed_version", sa.String(40), nullable=False),
        sa.Column("channel", sa.String(24), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("configuration", sa.JSON(), nullable=False),
        *entity(),
        sa.UniqueConstraint("owner_id", "package_slug"),
    )
    op.create_table(
        "marketplace_reviews",
        sa.Column(
            "package_id",
            sa.Uuid(native_uuid=False),
            sa.ForeignKey("marketplace_packages.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("reviewer_id", sa.String(160), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        *entity(),
        sa.UniqueConstraint("package_id", "reviewer_id"),
    )
    op.create_table(
        "automation_workflows",
        sa.Column("owner_id", sa.String(160), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("trigger_type", sa.String(60), nullable=False),
        sa.Column("graph", sa.JSON(), nullable=False),
        *entity(),
    )
    op.create_table(
        "automation_workflow_executions",
        sa.Column(
            "workflow_id",
            sa.Uuid(native_uuid=False),
            sa.ForeignKey("automation_workflows.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("owner_id", sa.String(160), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("current_node", sa.String(120)),
        sa.Column("context", sa.JSON(), nullable=False),
        sa.Column("output", sa.JSON(), nullable=False),
        sa.Column("error", sa.Text()),
        *entity(),
    )


def downgrade():
    for table in (
        "automation_workflow_executions",
        "automation_workflows",
        "marketplace_reviews",
        "marketplace_installations",
        "marketplace_packages",
    ):
        op.drop_table(table)
