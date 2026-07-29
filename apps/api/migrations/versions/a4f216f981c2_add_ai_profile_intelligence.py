"""add AI profile intelligence

Revision ID: a4f216f981c2
Revises: 9e5315975690
Create Date: 2026-07-29
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a4f216f981c2"
down_revision: str | None = "9e5315975690"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "ai_settings",
        sa.Column("provider", sa.String(32), nullable=False),
        sa.Column("model", sa.String(128), nullable=False),
        sa.Column("embedding_model", sa.String(128), nullable=False),
        sa.Column("base_url", sa.String(2048), nullable=False),
        sa.Column("temperature", sa.Float(), nullable=False),
        sa.Column("max_tokens", sa.Integer(), nullable=False),
        sa.Column("id", sa.Uuid(native_uuid=False), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "ai_suggestions",
        sa.Column("profile_id", sa.Uuid(native_uuid=False), nullable=False),
        sa.Column("suggestion_type", sa.String(64), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("source_type", sa.String(64), nullable=False),
        sa.Column("source_id", sa.String(64), nullable=True),
        sa.Column("original", sa.JSON(), nullable=True),
        sa.Column("proposed", sa.JSON(), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("id", sa.Uuid(native_uuid=False), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["profile_id"], ["career_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ai_suggestions_profile_id", "ai_suggestions", ["profile_id"])
    op.create_index("ix_ai_suggestions_status", "ai_suggestions", ["status"])
    op.create_index(
        "ix_ai_suggestions_suggestion_type", "ai_suggestions", ["suggestion_type"]
    )
    op.create_table(
        "profile_embeddings",
        sa.Column("profile_id", sa.Uuid(native_uuid=False), nullable=False),
        sa.Column("entity_type", sa.String(64), nullable=False),
        sa.Column("entity_id", sa.String(64), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("model", sa.String(128), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("vector", sa.LargeBinary(), nullable=False),
        sa.Column("id", sa.Uuid(native_uuid=False), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["profile_id"], ["career_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_profile_embeddings_profile_id", "profile_embeddings", ["profile_id"])
    op.create_index("ix_profile_embeddings_entity_type", "profile_embeddings", ["entity_type"])
    op.create_index("ix_profile_embeddings_entity_id", "profile_embeddings", ["entity_id"])
    op.create_index("ix_profile_embeddings_content_hash", "profile_embeddings", ["content_hash"])


def downgrade() -> None:
    op.drop_table("profile_embeddings")
    op.drop_table("ai_suggestions")
    op.drop_table("ai_settings")
