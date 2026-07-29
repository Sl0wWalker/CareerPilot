from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CoachSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class GoalCreate(CoachSchema):
    title: str = Field(min_length=1, max_length=240)
    description: str = Field(default="", max_length=5000)
    target_date: datetime | None = None
    priority: int = Field(default=3, ge=1, le=5)


class GoalRead(GoalCreate):
    id: UUID
    profile_id: UUID
    status: str
    created_at: datetime


class QuestionGenerateRequest(CoachSchema):
    job_id: UUID | None = None
    categories: list[Literal["behavioral", "technical", "company", "resume"]] = Field(
        default_factory=lambda: ["behavioral", "technical", "company"]
    )
    count: int = Field(default=8, ge=1, le=30)


class QuestionRead(CoachSchema):
    id: UUID
    job_id: UUID | None
    category: str
    question: str
    rationale: str
    evidence_hints: list[dict[str, Any]]
    difficulty: str


class SessionCreate(CoachSchema):
    job_id: UUID | None = None
    mode: Literal["behavioral", "technical", "mixed"] = "mixed"
    question_ids: list[UUID] = Field(default_factory=list)


class SessionRead(CoachSchema):
    id: UUID
    job_id: UUID | None
    mode: str
    status: str
    question_ids: list[str]
    current_index: int
    overall_score: float | None
    feedback: dict[str, Any]
    completed_at: datetime | None


class ResponseCreate(CoachSchema):
    question_id: UUID
    answer: str = Field(min_length=1, max_length=20000)


class ResponseRead(CoachSchema):
    id: UUID
    session_id: UUID
    question_id: UUID
    answer: str
    star_scores: dict[str, float]
    strengths: list[str]
    improvements: list[str]
    evidence_used: list[dict[str, Any]]
    score: float


class LearningPlanRequest(CoachSchema):
    target_role: str = Field(min_length=1, max_length=240)
    job_id: UUID | None = None


class LearningPlanRead(CoachSchema):
    id: UUID
    title: str
    target_role: str
    gap_analysis: list[dict[str, Any]]
    recommendations: list[dict[str, Any]]
    status: str


class RoadmapRequest(CoachSchema):
    title: str = Field(min_length=1, max_length=240)
    horizon_months: int = Field(default=24, ge=3, le=120)
    goal_ids: list[UUID] = Field(default_factory=list)


class RoadmapRead(CoachSchema):
    id: UUID
    title: str
    horizon_months: int
    milestones: list[dict[str, Any]]
    assumptions: list[str]


class OfferCompareRequest(CoachSchema):
    title: str = Field(min_length=1, max_length=240)
    offers: list[dict[str, Any]] = Field(min_length=2, max_length=10)
    weights: dict[str, float] = Field(default_factory=dict)


class OfferComparisonRead(CoachSchema):
    id: UUID
    title: str
    offers: list[dict[str, Any]]
    weights: dict[str, float]
    result: dict[str, Any]


class CoachDashboardRead(CoachSchema):
    active_goals: int
    completed_sessions: int
    average_interview_score: float | None
    active_learning_plans: int
    next_actions: list[str]
