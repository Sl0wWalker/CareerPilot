"""add application automation

Revision ID: c821ac7dd103
Revises: f53d7be23f71
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision = "c821ac7dd103"
down_revision = "f53d7be23f71"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def timestamps():
    return [
        sa.Column("id", sa.Uuid(native_uuid=False), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    ]


def upgrade() -> None:
    op.create_table(
        "automation_runs",
        sa.Column("profile_id", sa.Uuid(native_uuid=False), nullable=False),
        sa.Column("job_id", sa.Uuid(native_uuid=False), nullable=False),
        sa.Column("resume_id", sa.Uuid(native_uuid=False), nullable=False),
        sa.Column("cover_letter_id", sa.Uuid(native_uuid=False)),
        sa.Column("adapter", sa.String(32), nullable=False),
        sa.Column("application_url", sa.String(2048), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("dry_run", sa.Boolean(), nullable=False),
        sa.Column("approved", sa.Boolean(), nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False),
        sa.Column("max_attempts", sa.Integer(), nullable=False),
        sa.Column("checkpoint", sa.String(40), nullable=False),
        sa.Column("field_snapshot", sa.JSON(), nullable=False),
        sa.Column("validation_errors", sa.JSON(), nullable=False),
        sa.Column("last_error", sa.Text()),
        *timestamps(),
        sa.ForeignKeyConstraint(["profile_id"], ["career_profiles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["resume_id"], ["document_versions.id"]),
        sa.ForeignKeyConstraint(["cover_letter_id"], ["document_versions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ("profile_id", "job_id", "resume_id", "adapter", "status"):
        op.create_index(f"ix_automation_runs_{column}", "automation_runs", [column])
    op.create_table(
        "automation_steps",
        sa.Column("run_id", sa.Uuid(native_uuid=False), nullable=False),
        sa.Column("name", sa.String(64), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("details", sa.JSON(), nullable=False),
        sa.Column("screenshot_path", sa.String(1024)),
        *timestamps(),
        sa.ForeignKeyConstraint(["run_id"], ["automation_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_automation_steps_run_id", "automation_steps", ["run_id"])
    op.create_table(
        "browser_sessions",
        sa.Column("profile_id", sa.Uuid(native_uuid=False), nullable=False),
        sa.Column("adapter", sa.String(32), nullable=False),
        sa.Column("label", sa.String(120), nullable=False),
        sa.Column("storage_state_path", sa.String(1024), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        *timestamps(),
        sa.ForeignKeyConstraint(["profile_id"], ["career_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_browser_sessions_profile_id", "browser_sessions", ["profile_id"])
    op.create_index("ix_browser_sessions_adapter", "browser_sessions", ["adapter"])
    op.create_table(
        "adapter_settings",
        sa.Column("adapter", sa.String(32), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("headless", sa.Boolean(), nullable=False),
        sa.Column("default_dry_run", sa.Boolean(), nullable=False),
        sa.Column("timeout_ms", sa.Integer(), nullable=False),
        sa.Column("options", sa.JSON(), nullable=False),
        *timestamps(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("adapter"),
    )


def downgrade() -> None:
    op.drop_table("adapter_settings")
    op.drop_table("browser_sessions")
    op.drop_table("automation_steps")
    op.drop_table("automation_runs")
