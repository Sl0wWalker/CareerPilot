"""add intelligent job discovery

Revision ID: d8920d571f6a
Revises: a4f216f981c2
Create Date: 2026-07-29
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d8920d571f6a"
down_revision: str | None = "a4f216f981c2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def common_columns() -> list[sa.Column]:
    return [
        sa.Column("id", sa.Uuid(native_uuid=False), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    ]


def upgrade() -> None:
    op.create_table(
        "companies",
        sa.Column("name", sa.String(240), nullable=False),
        sa.Column("website_url", sa.String(2048)),
        sa.Column("careers_url", sa.String(2048)),
        sa.Column("description", sa.Text()),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        *common_columns(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index("ix_companies_name", "companies", ["name"])
    op.create_table(
        "job_sources",
        sa.Column("provider", sa.String(40), nullable=False),
        sa.Column("external_key", sa.String(255), nullable=False),
        sa.Column("name", sa.String(240), nullable=False),
        sa.Column("source_url", sa.String(2048)),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("configuration", sa.JSON(), nullable=False),
        sa.Column("last_synced_at", sa.DateTime(timezone=True)),
        *common_columns(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("provider", "external_key"),
    )
    op.create_index("ix_job_sources_provider", "job_sources", ["provider"])
    op.create_table(
        "jobs",
        sa.Column("company_id", sa.Uuid(native_uuid=False), nullable=False),
        sa.Column("source_provider", sa.String(40), nullable=False),
        sa.Column("external_id", sa.String(255), nullable=False),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("canonical_url", sa.String(2048), nullable=False),
        sa.Column("application_url", sa.String(2048)),
        sa.Column("location_raw", sa.String(300)),
        sa.Column("city", sa.String(120)),
        sa.Column("region", sa.String(120)),
        sa.Column("country", sa.String(120)),
        sa.Column("workplace_type", sa.String(20), nullable=False),
        sa.Column("employment_type", sa.String(40)),
        sa.Column("salary_min", sa.Integer()),
        sa.Column("salary_max", sa.Integer()),
        sa.Column("salary_currency", sa.String(3)),
        sa.Column("salary_period", sa.String(20)),
        sa.Column("posted_at", sa.DateTime(timezone=True)),
        sa.Column("fingerprint", sa.String(64), nullable=False),
        sa.Column("search_text", sa.Text(), nullable=False),
        sa.Column("raw_payload", sa.JSON(), nullable=False),
        sa.Column("is_favorite", sa.Boolean(), nullable=False),
        sa.Column("relevance_score", sa.Float()),
        sa.Column("relevance_analysis", sa.JSON()),
        *common_columns(),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("fingerprint"),
        sa.UniqueConstraint("source_provider", "external_id"),
    )
    for column in (
        "company_id", "source_provider", "title", "city", "region", "country",
        "workplace_type", "employment_type", "posted_at", "fingerprint", "is_favorite",
    ):
        op.create_index(f"ix_jobs_{column}", "jobs", [column])
    op.create_table(
        "saved_searches",
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("query", sa.String(300)),
        sa.Column("filters", sa.JSON(), nullable=False),
        *common_columns(),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "scheduled_searches",
        sa.Column("saved_search_id", sa.Uuid(native_uuid=False), nullable=False),
        sa.Column("cadence", sa.String(30), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("next_run_at", sa.DateTime(timezone=True)),
        sa.Column("last_run_at", sa.DateTime(timezone=True)),
        *common_columns(),
        sa.ForeignKeyConstraint(
            ["saved_search_id"], ["saved_searches.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_scheduled_searches_saved_search_id",
        "scheduled_searches",
        ["saved_search_id"],
    )


def downgrade() -> None:
    op.drop_table("scheduled_searches")
    op.drop_table("saved_searches")
    op.drop_table("jobs")
    op.drop_table("job_sources")
    op.drop_table("companies")
