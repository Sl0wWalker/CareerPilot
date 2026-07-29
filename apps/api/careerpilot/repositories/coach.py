from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from careerpilot.models.coach import (
    CareerGoal,
    CareerRoadmap,
    InterviewQuestion,
    LearningPlan,
    MockInterviewResponse,
    MockInterviewSession,
    OfferComparison,
)


class CoachRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def save(self, value):
        self.session.add(value)
        self.session.commit()
        self.session.refresh(value)
        return value

    def save_all(self, values):
        self.session.add_all(values)
        self.session.commit()
        for value in values:
            self.session.refresh(value)
        return values

    def get(self, model, value_id: UUID):
        value = self.session.get(model, value_id)
        if value is None:
            raise LookupError(f"{model.__name__} not found")
        return value

    def list(self, model, profile_id: UUID):
        return list(
            self.session.scalars(
                select(model)
                .where(model.profile_id == profile_id)
                .order_by(model.created_at.desc())
            )
        )

    def responses(self, session_id: UUID):
        return list(
            self.session.scalars(
                select(MockInterviewResponse)
                .where(MockInterviewResponse.session_id == session_id)
                .order_by(MockInterviewResponse.created_at)
            )
        )


COACH_PROFILE_MODELS = (
    CareerGoal,
    InterviewQuestion,
    MockInterviewSession,
    LearningPlan,
    CareerRoadmap,
    OfferComparison,
)
