"""add explainable job matching

Revision ID: e743f0eaf881
Revises: d8920d571f6a
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "e743f0eaf881"
down_revision: str | None = "d8920d571f6a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "matching_settings",
        sa.Column("weights", sa.JSON(), nullable=False),
        sa.Column("hard_block_threshold", sa.Float(), nullable=False),
        sa.Column("minimum_recommendation_score", sa.Float(), nullable=False),
        sa.Column("id", sa.Uuid(native_uuid=False), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "job_matches",
        sa.Column("job_id", sa.Uuid(native_uuid=False), nullable=False),
        sa.Column("profile_id", sa.Uuid(native_uuid=False), nullable=False),
        sa.Column("overall_score", sa.Float(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("recommendation", sa.String(length=32), nullable=False),
        sa.Column("engine_version", sa.String(length=32), nullable=False),
        sa.Column("components", sa.JSON(), nullable=False),
        sa.Column("strengths", sa.JSON(), nullable=False),
        sa.Column("gaps", sa.JSON(), nullable=False),
        sa.Column("hard_blocks", sa.JSON(), nullable=False),
        sa.Column("reasons", sa.JSON(), nullable=False),
        sa.Column("evidence", sa.JSON(), nullable=False),
        sa.Column("id", sa.Uuid(native_uuid=False), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["profile_id"], ["career_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("job_id", "profile_id"),
    )
    op.create_index("ix_job_matches_job_id", "job_matches", ["job_id"])
    op.create_index("ix_job_matches_profile_id", "job_matches", ["profile_id"])
    op.create_index("ix_job_matches_recommendation", "job_matches", ["recommendation"])


def downgrade() -> None:
    op.drop_index("ix_job_matches_recommendation", table_name="job_matches")
    op.drop_index("ix_job_matches_profile_id", table_name="job_matches")
    op.drop_index("ix_job_matches_job_id", table_name="job_matches")
    op.drop_table("job_matches")
    op.drop_table("matching_settings")
