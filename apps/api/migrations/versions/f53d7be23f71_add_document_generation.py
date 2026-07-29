"""add document generation

Revision ID: f53d7be23f71
Revises: e743f0eaf881
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision = "f53d7be23f71"
down_revision = "e743f0eaf881"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "resume_templates",
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("style", sa.JSON(), nullable=False),
        sa.Column("is_default", sa.Boolean(), nullable=False),
        sa.Column("id", sa.Uuid(native_uuid=False), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("name"),
    )
    op.create_table(
        "document_versions",
        sa.Column("profile_id", sa.Uuid(native_uuid=False), nullable=False),
        sa.Column("job_id", sa.Uuid(native_uuid=False)),
        sa.Column("template_id", sa.Uuid(native_uuid=False)),
        sa.Column("document_type", sa.String(32), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("title", sa.String(240), nullable=False),
        sa.Column("content", sa.JSON(), nullable=False),
        sa.Column("evidence", sa.JSON(), nullable=False),
        sa.Column("keyword_coverage", sa.JSON(), nullable=False),
        sa.Column("model", sa.String(128)),
        sa.Column("prompt_version", sa.String(32)),
        sa.Column("id", sa.Uuid(native_uuid=False), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["profile_id"], ["career_profiles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["template_id"], ["resume_templates.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_document_versions_job_id", "document_versions", ["job_id"])
    op.create_index("ix_document_versions_profile_id", "document_versions", ["profile_id"])
    op.create_index("ix_document_versions_document_type", "document_versions", ["document_type"])
    op.create_index("ix_document_versions_status", "document_versions", ["status"])
    op.create_table(
        "document_changes",
        sa.Column("document_id", sa.Uuid(native_uuid=False), nullable=False),
        sa.Column("section", sa.String(64), nullable=False),
        sa.Column("original", sa.Text()),
        sa.Column("proposed", sa.Text(), nullable=False),
        sa.Column("evidence_ids", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("id", sa.Uuid(native_uuid=False), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["document_versions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_document_changes_document_id", "document_changes", ["document_id"])
    op.create_table(
        "screening_answers",
        sa.Column("profile_id", sa.Uuid(native_uuid=False), nullable=False),
        sa.Column("job_id", sa.Uuid(native_uuid=False), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("normalized_question", sa.String(200), nullable=False),
        sa.Column("answer", sa.Text()),
        sa.Column("evidence", sa.JSON(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("sensitive", sa.Boolean(), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("id", sa.Uuid(native_uuid=False), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["profile_id"], ["career_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_screening_answers_job_id", "screening_answers", ["job_id"])
    op.create_index("ix_screening_answers_profile_id", "screening_answers", ["profile_id"])
    op.create_index("ix_screening_answers_normalized_question", "screening_answers", ["normalized_question"])


def downgrade() -> None:
    op.drop_table("screening_answers")
    op.drop_table("document_changes")
    op.drop_table("document_versions")
    op.drop_table("resume_templates")
