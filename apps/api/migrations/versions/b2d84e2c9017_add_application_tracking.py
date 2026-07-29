"""add application tracking and analytics

Revision ID: b2d84e2c9017
Revises: c821ac7dd103
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b2d84e2c9017"
down_revision: str | None = "c821ac7dd103"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

ID = sa.Uuid(native_uuid=False)
TIMES = [
    sa.Column("id", ID, nullable=False),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
]


def create_child(name: str, *columns: sa.Column) -> None:
    op.create_table(
        name, *TIMES,
        sa.Column("application_id", ID, nullable=False),
        *columns,
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(f"ix_{name}_application_id", name, ["application_id"])


def upgrade() -> None:
    op.create_table(
        "applications", *TIMES,
        sa.Column("profile_id", ID, nullable=False),
        sa.Column("job_id", ID, nullable=False),
        sa.Column("automation_run_id", ID),
        sa.Column("status", sa.String(40), nullable=False),
        sa.Column("source", sa.String(40), nullable=False),
        sa.Column("applied_at", sa.DateTime(timezone=True)),
        sa.Column("responded_at", sa.DateTime(timezone=True)),
        sa.Column("closed_at", sa.DateTime(timezone=True)),
        sa.Column("outcome", sa.String(40)),
        sa.Column("rejection_reason", sa.Text()),
        sa.Column("offer_amount", sa.Float()),
        sa.Column("offer_currency", sa.String(3)),
        sa.Column("tags", sa.JSON(), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["profile_id"], ["career_profiles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["automation_run_id"], ["automation_runs.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ("profile_id", "job_id", "status", "applied_at", "outcome"):
        op.create_index(f"ix_applications_{column}", "applications", [column])
    create_child(
        "application_events",
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("from_status", sa.String(40)),
        sa.Column("to_status", sa.String(40)),
        sa.Column("title", sa.String(240), nullable=False),
        sa.Column("details", sa.JSON(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
    )
    create_child("application_notes", sa.Column("body", sa.Text(), nullable=False),
                 sa.Column("pinned", sa.Boolean(), nullable=False))
    create_child(
        "application_contacts", sa.Column("name", sa.String(200), nullable=False),
        sa.Column("role", sa.String(160)), sa.Column("email", sa.String(320)),
        sa.Column("phone", sa.String(50)), sa.Column("linkedin_url", sa.String(2048)),
        sa.Column("notes", sa.Text()),
    )
    create_child(
        "application_follow_ups", sa.Column("title", sa.String(240), nullable=False),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("reminder_enabled", sa.Boolean(), nullable=False),
    )
    create_child(
        "application_interviews", sa.Column("stage", sa.String(120), nullable=False),
        sa.Column("scheduled_at", sa.DateTime(timezone=True)),
        sa.Column("duration_minutes", sa.Integer()),
        sa.Column("location_or_link", sa.String(2048)), sa.Column("notes", sa.Text()),
    )


def downgrade() -> None:
    for table in (
        "application_interviews", "application_follow_ups", "application_contacts",
        "application_notes", "application_events", "applications",
    ):
        op.drop_table(table)
