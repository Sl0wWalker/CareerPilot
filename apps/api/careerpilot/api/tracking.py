from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from careerpilot.db.session import get_db
from careerpilot.models.tracking import (
    ApplicationNote,
    Contact,
    FollowUp,
    InterviewPlaceholder,
)
from careerpilot.repositories import CareerProfileRepository, JobRepository
from careerpilot.repositories.tracking import TrackingRepository
from careerpilot.schemas.tracking import (
    AnalyticsRead,
    ApplicationCreate,
    ApplicationRead,
    ApplicationUpdate,
    ContactCreate,
    ContactRead,
    EventRead,
    FollowUpCreate,
    FollowUpRead,
    ImportPayload,
    InterviewCreate,
    InterviewRead,
    NoteCreate,
    NoteRead,
)
from careerpilot.services.tracking import TrackingService

router = APIRouter(prefix="/applications", tags=["application tracking"])
Db = Annotated[Session, Depends(get_db)]


def not_found(error: LookupError) -> HTTPException:
    return HTTPException(status_code=404, detail=str(error))


@router.post("", response_model=ApplicationRead)
def create_application(payload: ApplicationCreate, session: Db):
    try:
        profile = CareerProfileRepository(session).get_required()
        JobRepository(session).job(payload.job_id)
        return TrackingService(TrackingRepository(session)).create(
            profile.id, payload.model_dump()
        )
    except LookupError as error:
        raise not_found(error) from error


@router.get("", response_model=list[ApplicationRead])
def list_applications(session: Db, status: str | None = None, tag: str | None = None):
    return TrackingRepository(session).applications(status, tag)


@router.get("/export")
def export_applications(session: Db):
    return {"version": 1, "exported_at": datetime.now(UTC), "applications": [
        ApplicationRead.model_validate(item).model_dump(mode="json")
        for item in TrackingRepository(session).applications()
    ]}


@router.post("/import", response_model=list[ApplicationRead])
def import_applications(payload: ImportPayload, session: Db):
    profile = CareerProfileRepository(session).get_required()
    service = TrackingService(TrackingRepository(session))
    imported = []
    for raw in payload.applications:
        value = ApplicationCreate.model_validate({
            "job_id": raw["job_id"], "automation_run_id": raw.get("automation_run_id"),
            "status": raw.get("status", "draft"), "source": "import",
            "tags": raw.get("tags", []),
        })
        imported.append(service.create(profile.id, value.model_dump()))
    return imported


@router.get("/analytics", response_model=AnalyticsRead)
def analytics(session: Db):
    values = TrackingRepository(session).applications()
    return TrackingService(TrackingRepository(session)).analytics(values)


@router.get("/{application_id}", response_model=ApplicationRead)
def get_application(application_id: UUID, session: Db):
    try:
        return TrackingRepository(session).application(application_id)
    except LookupError as error:
        raise not_found(error) from error


@router.patch("/{application_id}", response_model=ApplicationRead)
def update_application(application_id: UUID, payload: ApplicationUpdate, session: Db):
    repository = TrackingRepository(session)
    try:
        return TrackingService(repository).update(
            repository.application(application_id), payload.model_dump(exclude_none=True)
        )
    except LookupError as error:
        raise not_found(error) from error


@router.get("/{application_id}/timeline", response_model=list[EventRead])
def timeline(application_id: UUID, session: Db):
    repository = TrackingRepository(session)
    try:
        repository.application(application_id)
        return repository.events(application_id)
    except LookupError as error:
        raise not_found(error) from error


@router.post("/{application_id}/notes", response_model=NoteRead)
def add_note(application_id: UUID, payload: NoteCreate, session: Db):
    repository = TrackingRepository(session)
    try:
        application = repository.application(application_id)
        value = repository.save(
            ApplicationNote(application_id=application_id, **payload.model_dump())
        )
        repository.event(application, "note_added", "Note added", pinned=value.pinned)
        return value
    except LookupError as error:
        raise not_found(error) from error


@router.get("/{application_id}/notes", response_model=list[NoteRead])
def notes(application_id: UUID, session: Db):
    return TrackingRepository(session).related(ApplicationNote, application_id)


@router.post("/{application_id}/contacts", response_model=ContactRead)
def add_contact(application_id: UUID, payload: ContactCreate, session: Db):
    repository = TrackingRepository(session)
    application = repository.application(application_id)
    value = repository.save(Contact(application_id=application_id, **payload.model_dump()))
    repository.event(application, "contact_added", f"Added contact {value.name}")
    return value


@router.get("/{application_id}/contacts", response_model=list[ContactRead])
def contacts(application_id: UUID, session: Db):
    return TrackingRepository(session).related(Contact, application_id)


@router.post("/{application_id}/follow-ups", response_model=FollowUpRead)
def add_follow_up(application_id: UUID, payload: FollowUpCreate, session: Db):
    repository = TrackingRepository(session)
    application = repository.application(application_id)
    value = repository.save(FollowUp(application_id=application_id, **payload.model_dump()))
    repository.event(application, "follow_up_added", value.title, due_at=value.due_at.isoformat())
    return value


@router.patch("/{application_id}/follow-ups/{follow_up_id}/complete", response_model=FollowUpRead)
def complete_follow_up(application_id: UUID, follow_up_id: UUID, session: Db):
    repository = TrackingRepository(session)
    repository.application(application_id)
    value = session.get(FollowUp, follow_up_id)
    if value is None or value.application_id != application_id:
        raise HTTPException(status_code=404, detail="follow-up not found")
    value.completed_at = datetime.now(UTC)
    return repository.save(value)


@router.get("/{application_id}/follow-ups", response_model=list[FollowUpRead])
def follow_ups(application_id: UUID, session: Db):
    return TrackingRepository(session).related(FollowUp, application_id)


@router.post("/{application_id}/interviews", response_model=InterviewRead)
def add_interview(application_id: UUID, payload: InterviewCreate, session: Db):
    repository = TrackingRepository(session)
    application = repository.application(application_id)
    value = repository.save(InterviewPlaceholder(
        application_id=application_id, **payload.model_dump()
    ))
    repository.event(application, "interview_scheduled", value.stage)
    return value


@router.get("/{application_id}/interviews", response_model=list[InterviewRead])
def interviews(application_id: UUID, session: Db):
    return TrackingRepository(session).related(InterviewPlaceholder, application_id)
