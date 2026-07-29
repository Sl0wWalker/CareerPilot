from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from careerpilot.models.tracking import (
    Application,
    ApplicationEvent,
    ApplicationNote,
    Contact,
    FollowUp,
    InterviewPlaceholder,
)


class TrackingRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def save(self, value):
        self.session.add(value)
        self.session.commit()
        self.session.refresh(value)
        return value

    def application(self, value_id: UUID) -> Application:
        value = self.session.get(Application, value_id)
        if value is None:
            raise LookupError("application not found")
        return value

    def applications(self, status: str | None = None, tag: str | None = None):
        statement = select(Application).order_by(Application.updated_at.desc())
        if status:
            statement = statement.where(Application.status == status)
        values = list(self.session.scalars(statement))
        return [item for item in values if not tag or tag in item.tags]

    def event(self, application: Application, event_type: str, title: str,
              from_status: str | None = None, to_status: str | None = None, **details):
        return self.save(ApplicationEvent(
            application_id=application.id, event_type=event_type, title=title,
            from_status=from_status, to_status=to_status, details=details,
            occurred_at=datetime.now(UTC),
        ))

    def events(self, application_id: UUID):
        statement = (
            select(ApplicationEvent)
            .where(ApplicationEvent.application_id == application_id)
            .order_by(ApplicationEvent.occurred_at.desc())
        )
        return list(self.session.scalars(statement))

    def related(self, model, application_id: UUID):
        statement = select(model).where(model.application_id == application_id)
        return list(self.session.scalars(statement))

    def delete(self, value) -> None:
        self.session.delete(value)
        self.session.commit()


TRACKING_CHILDREN = (ApplicationNote, Contact, FollowUp, InterviewPlaceholder)
