from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from careerpilot.api.ai import get_ai_provider
from careerpilot.db.session import get_db
from careerpilot.models.coach import (
    CareerGoal,
    InterviewQuestion,
    LearningPlan,
    MockInterviewSession,
)
from careerpilot.repositories import CareerProfileRepository, JobRepository
from careerpilot.repositories.coach import CoachRepository
from careerpilot.schemas.coach import (
    CoachDashboardRead,
    GoalCreate,
    GoalRead,
    LearningPlanRead,
    LearningPlanRequest,
    OfferCompareRequest,
    OfferComparisonRead,
    QuestionGenerateRequest,
    QuestionRead,
    ResponseCreate,
    ResponseRead,
    RoadmapRead,
    RoadmapRequest,
    SessionCreate,
    SessionRead,
)
from careerpilot.services.ai import AIProvider
from careerpilot.services.coach import CoachService

router = APIRouter(prefix="/coach", tags=["career coach"])
Db = Annotated[Session, Depends(get_db)]
Provider = Annotated[AIProvider, Depends(get_ai_provider)]


def service(session: Session, provider: AIProvider | None = None) -> CoachService:
    return CoachService(CoachRepository(session), provider)


def profile(session: Session):
    try:
        return CareerProfileRepository(session).get_required()
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


def job_or_none(session: Session, job_id: UUID | None):
    if job_id is None:
        return None
    try:
        return JobRepository(session).job(job_id)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.get("/dashboard", response_model=CoachDashboardRead)
def dashboard(session: Db):
    current = profile(session)
    repository = CoachRepository(session)
    goals = repository.list(CareerGoal, current.id)
    sessions = repository.list(MockInterviewSession, current.id)
    plans = repository.list(LearningPlan, current.id)
    completed = [item for item in sessions if item.status == "completed"]
    scores = [item.overall_score for item in completed if item.overall_score is not None]
    actions = []
    if not goals:
        actions.append("Add a career goal.")
    if not plans:
        actions.append("Generate a learning plan for a target role.")
    if not completed:
        actions.append("Complete a mock interview.")
    return CoachDashboardRead(
        active_goals=sum(item.status == "active" for item in goals),
        completed_sessions=len(completed),
        average_interview_score=round(sum(scores) / len(scores), 1) if scores else None,
        active_learning_plans=sum(item.status == "active" for item in plans),
        next_actions=actions,
    )


@router.post("/goals", response_model=GoalRead)
def add_goal(payload: GoalCreate, session: Db):
    current = profile(session)
    return service(session).create_goal(current.id, payload.model_dump())


@router.get("/goals", response_model=list[GoalRead])
def goals(session: Db):
    current = profile(session)
    return CoachRepository(session).list(CareerGoal, current.id)


@router.post("/interview/questions", response_model=list[QuestionRead])
def generate_questions(payload: QuestionGenerateRequest, session: Db, provider: Provider):
    current = profile(session)
    return service(session, provider).generate_questions(
        current, job_or_none(session, payload.job_id), payload.categories, payload.count
    )


@router.post("/interview/sessions", response_model=SessionRead)
def create_session(payload: SessionCreate, session: Db):
    current = profile(session)
    repository = CoachRepository(session)
    questions = repository.list(InterviewQuestion, current.id)
    return service(session).create_session(current.id, payload.model_dump(), questions)


@router.post("/interview/sessions/{session_id}/responses", response_model=ResponseRead)
def answer_question(session_id: UUID, payload: ResponseCreate, session: Db):
    current = profile(session)
    repository = CoachRepository(session)
    mock_session = repository.get(MockInterviewSession, session_id)
    question = repository.get(InterviewQuestion, payload.question_id)
    if mock_session.profile_id != current.id or question.profile_id != current.id:
        raise HTTPException(status_code=404, detail="interview session not found")
    return service(session).answer(mock_session, question, payload.answer, current)


@router.post("/learning-plans", response_model=LearningPlanRead)
def create_learning_plan(payload: LearningPlanRequest, session: Db):
    current = profile(session)
    return service(session).learning_plan(
        current, payload.target_role, job_or_none(session, payload.job_id)
    )


@router.get("/learning-plans", response_model=list[LearningPlanRead])
def learning_plans(session: Db):
    current = profile(session)
    return CoachRepository(session).list(LearningPlan, current.id)


@router.post("/roadmaps", response_model=RoadmapRead)
def create_roadmap(payload: RoadmapRequest, session: Db):
    current = profile(session)
    repository = CoachRepository(session)
    goals = [repository.get(CareerGoal, value) for value in payload.goal_ids]
    return service(session).roadmap(
        current.id, payload.title, payload.horizon_months, goals
    )


@router.post("/offers/compare", response_model=OfferComparisonRead)
def compare_offers(payload: OfferCompareRequest, session: Db):
    current = profile(session)
    return service(session).compare_offers(
        current.id, payload.title, payload.offers, payload.weights
    )
