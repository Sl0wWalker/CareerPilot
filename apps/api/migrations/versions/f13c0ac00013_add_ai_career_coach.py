"""add AI career coach and interview intelligence

Revision ID: f13c0ac00013
Revises: e12c10d00012
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "f13c0ac00013"
down_revision: str | None = "e12c10d00012"
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
        "career_goals",
        *entity_columns(),
        sa.Column("profile_id", sa.Uuid(), sa.ForeignKey("career_profiles.id", ondelete="CASCADE")),
        sa.Column("title", sa.String(240), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("target_date", sa.DateTime(timezone=True)),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_career_goals_profile_id", "career_goals", ["profile_id"])
    op.create_index("ix_career_goals_status", "career_goals", ["status"])
    op.create_table(
        "coach_interview_questions",
        *entity_columns(),
        sa.Column("profile_id", sa.Uuid(), sa.ForeignKey("career_profiles.id", ondelete="CASCADE")),
        sa.Column("job_id", sa.Uuid(), sa.ForeignKey("jobs.id", ondelete="CASCADE")),
        sa.Column("category", sa.String(40), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("evidence_hints", sa.JSON(), nullable=False),
        sa.Column("difficulty", sa.String(20), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_coach_interview_questions_profile_id",
        "coach_interview_questions",
        ["profile_id"],
    )
    op.create_index("ix_coach_interview_questions_job_id", "coach_interview_questions", ["job_id"])
    op.create_index(
        "ix_coach_interview_questions_category",
        "coach_interview_questions",
        ["category"],
    )
    op.create_table(
        "mock_interview_sessions",
        *entity_columns(),
        sa.Column("profile_id", sa.Uuid(), sa.ForeignKey("career_profiles.id", ondelete="CASCADE")),
        sa.Column("job_id", sa.Uuid(), sa.ForeignKey("jobs.id", ondelete="SET NULL")),
        sa.Column("mode", sa.String(30), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("question_ids", sa.JSON(), nullable=False),
        sa.Column("current_index", sa.Integer(), nullable=False),
        sa.Column("overall_score", sa.Float()),
        sa.Column("feedback", sa.JSON(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_mock_interview_sessions_profile_id",
        "mock_interview_sessions",
        ["profile_id"],
    )
    op.create_index("ix_mock_interview_sessions_job_id", "mock_interview_sessions", ["job_id"])
    op.create_index("ix_mock_interview_sessions_status", "mock_interview_sessions", ["status"])
    op.create_table(
        "mock_interview_responses",
        *entity_columns(),
        sa.Column(
            "session_id",
            sa.Uuid(),
            sa.ForeignKey("mock_interview_sessions.id", ondelete="CASCADE"),
        ),
        sa.Column(
            "question_id",
            sa.Uuid(),
            sa.ForeignKey("coach_interview_questions.id", ondelete="CASCADE"),
        ),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column("star_scores", sa.JSON(), nullable=False),
        sa.Column("strengths", sa.JSON(), nullable=False),
        sa.Column("improvements", sa.JSON(), nullable=False),
        sa.Column("evidence_used", sa.JSON(), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_mock_interview_responses_session_id",
        "mock_interview_responses",
        ["session_id"],
    )
    op.create_table(
        "learning_plans",
        *entity_columns(),
        sa.Column("profile_id", sa.Uuid(), sa.ForeignKey("career_profiles.id", ondelete="CASCADE")),
        sa.Column("title", sa.String(240), nullable=False),
        sa.Column("target_role", sa.String(240), nullable=False),
        sa.Column("gap_analysis", sa.JSON(), nullable=False),
        sa.Column("recommendations", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_learning_plans_profile_id", "learning_plans", ["profile_id"])
    op.create_table(
        "career_roadmaps",
        *entity_columns(),
        sa.Column("profile_id", sa.Uuid(), sa.ForeignKey("career_profiles.id", ondelete="CASCADE")),
        sa.Column("title", sa.String(240), nullable=False),
        sa.Column("horizon_months", sa.Integer(), nullable=False),
        sa.Column("milestones", sa.JSON(), nullable=False),
        sa.Column("assumptions", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_career_roadmaps_profile_id", "career_roadmaps", ["profile_id"])
    op.create_table(
        "offer_comparisons",
        *entity_columns(),
        sa.Column("profile_id", sa.Uuid(), sa.ForeignKey("career_profiles.id", ondelete="CASCADE")),
        sa.Column("title", sa.String(240), nullable=False),
        sa.Column("offers", sa.JSON(), nullable=False),
        sa.Column("weights", sa.JSON(), nullable=False),
        sa.Column("result", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_offer_comparisons_profile_id", "offer_comparisons", ["profile_id"])


def downgrade() -> None:
    for table in (
        "offer_comparisons",
        "career_roadmaps",
        "learning_plans",
        "mock_interview_responses",
        "mock_interview_sessions",
        "coach_interview_questions",
        "career_goals",
    ):
        op.drop_table(table)
