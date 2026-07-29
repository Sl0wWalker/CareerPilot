from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from careerpilot.db.base import Base
from careerpilot.models.profile import EntityMixin


class CareerGoal(EntityMixin, Base):
    __tablename__ = "career_goals"

    profile_id: Mapped[UUID] = mapped_column(
        Uuid(native_uuid=False), ForeignKey("career_profiles.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(240))
    description: Mapped[str] = mapped_column(Text, default="")
    target_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(30), default="active", index=True)
    priority: Mapped[int] = mapped_column(Integer, default=3)


class InterviewQuestion(EntityMixin, Base):
    __tablename__ = "coach_interview_questions"

    profile_id: Mapped[UUID] = mapped_column(
        Uuid(native_uuid=False), ForeignKey("career_profiles.id", ondelete="CASCADE"), index=True
    )
    job_id: Mapped[UUID | None] = mapped_column(
        Uuid(native_uuid=False), ForeignKey("jobs.id", ondelete="CASCADE"), index=True
    )
    category: Mapped[str] = mapped_column(String(40), index=True)
    question: Mapped[str] = mapped_column(Text)
    rationale: Mapped[str] = mapped_column(Text, default="")
    evidence_hints: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    difficulty: Mapped[str] = mapped_column(String(20), default="medium")


class MockInterviewSession(EntityMixin, Base):
    __tablename__ = "mock_interview_sessions"

    profile_id: Mapped[UUID] = mapped_column(
        Uuid(native_uuid=False), ForeignKey("career_profiles.id", ondelete="CASCADE"), index=True
    )
    job_id: Mapped[UUID | None] = mapped_column(
        Uuid(native_uuid=False), ForeignKey("jobs.id", ondelete="SET NULL"), index=True
    )
    mode: Mapped[str] = mapped_column(String(30), default="mixed")
    status: Mapped[str] = mapped_column(String(30), default="active", index=True)
    question_ids: Mapped[list[str]] = mapped_column(JSON, default=list)
    current_index: Mapped[int] = mapped_column(Integer, default=0)
    overall_score: Mapped[float | None] = mapped_column(Float)
    feedback: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class MockInterviewResponse(EntityMixin, Base):
    __tablename__ = "mock_interview_responses"

    session_id: Mapped[UUID] = mapped_column(
        Uuid(native_uuid=False),
        ForeignKey("mock_interview_sessions.id", ondelete="CASCADE"),
        index=True,
    )
    question_id: Mapped[UUID] = mapped_column(
        Uuid(native_uuid=False),
        ForeignKey("coach_interview_questions.id", ondelete="CASCADE"),
    )
    answer: Mapped[str] = mapped_column(Text)
    star_scores: Mapped[dict[str, float]] = mapped_column(JSON, default=dict)
    strengths: Mapped[list[str]] = mapped_column(JSON, default=list)
    improvements: Mapped[list[str]] = mapped_column(JSON, default=list)
    evidence_used: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    score: Mapped[float] = mapped_column(Float, default=0)


class LearningPlan(EntityMixin, Base):
    __tablename__ = "learning_plans"

    profile_id: Mapped[UUID] = mapped_column(
        Uuid(native_uuid=False), ForeignKey("career_profiles.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(240))
    target_role: Mapped[str] = mapped_column(String(240))
    gap_analysis: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    recommendations: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(30), default="active")


class CareerRoadmap(EntityMixin, Base):
    __tablename__ = "career_roadmaps"

    profile_id: Mapped[UUID] = mapped_column(
        Uuid(native_uuid=False), ForeignKey("career_profiles.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(240))
    horizon_months: Mapped[int] = mapped_column(Integer, default=24)
    milestones: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    assumptions: Mapped[list[str]] = mapped_column(JSON, default=list)


class OfferComparison(EntityMixin, Base):
    __tablename__ = "offer_comparisons"

    profile_id: Mapped[UUID] = mapped_column(
        Uuid(native_uuid=False), ForeignKey("career_profiles.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(240))
    offers: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    weights: Mapped[dict[str, float]] = mapped_column(JSON, default=dict)
    result: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
