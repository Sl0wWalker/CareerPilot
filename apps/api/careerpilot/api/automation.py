from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from careerpilot.db.session import get_db
from careerpilot.models import ScreeningAnswer
from careerpilot.repositories import (
    AutomationRepository,
    CareerProfileRepository,
    DocumentRepository,
    JobRepository,
)
from careerpilot.schemas.automation import (
    AdapterSettingRead,
    AdapterSettingUpdate,
    ApprovalRequest,
    AutomationCreate,
    AutomationRead,
    InspectionRead,
    InspectRequest,
    MappedField,
)
from careerpilot.services.automation import AutomationService

router = APIRouter(prefix="/automation", tags=["automation"])
Db = Annotated[Session, Depends(get_db)]


def fail(error: Exception) -> HTTPException:
    status_code = 400 if isinstance(error, ValueError) else 404
    return HTTPException(status_code=status_code, detail=str(error))


@router.post("/runs", response_model=AutomationRead)
def create_run(payload: AutomationCreate, session: Db):
    try:
        profile = CareerProfileRepository(session).get_required()
        job = JobRepository(session).job(payload.job_id)
        resume = DocumentRepository(session).get(payload.resume_id)
        if resume.profile_id != profile.id or resume.job_id not in (None, job.id):
            raise ValueError("selected resume does not belong to this profile and job")
        return AutomationService(AutomationRepository(session)).create(
            profile, job.id, resume, str(payload.application_url), payload.cover_letter_id,
            payload.dry_run, payload.max_attempts,
        )
    except (LookupError, ValueError) as error:
        raise fail(error) from error


@router.get("/runs", response_model=list[AutomationRead])
def list_runs(session: Db):
    return AutomationRepository(session).runs()


@router.get("/runs/{run_id}", response_model=AutomationRead)
def get_run(run_id: UUID, session: Db):
    try:
        return AutomationRepository(session).run(run_id)
    except LookupError as error:
        raise fail(error) from error


@router.post("/runs/{run_id}/inspect", response_model=InspectionRead)
def inspect(run_id: UUID, payload: InspectRequest, session: Db):
    try:
        repository = AutomationRepository(session)
        run = repository.run(run_id)
        profile = CareerProfileRepository(session).get_required()
        answers = list(session.scalars(
            select(ScreeningAnswer).where(
                ScreeningAnswer.profile_id == profile.id,
                ScreeningAnswer.job_id == run.job_id,
            )
        ))
        run, mapped = AutomationService(repository).inspect(
            run, profile, [item.model_dump() for item in payload.fields], answers
        )
        return InspectionRead(
            adapter=run.adapter,
            fields=[MappedField(**item) for item in mapped],
            validation_errors=run.validation_errors,
        )
    except LookupError as error:
        raise fail(error) from error


@router.post("/runs/{run_id}/approve", response_model=AutomationRead)
def approve(run_id: UUID, payload: ApprovalRequest, session: Db):
    try:
        repository = AutomationRepository(session)
        return AutomationService(repository).approve(repository.run(run_id), payload.approved)
    except (LookupError, ValueError) as error:
        raise fail(error) from error


@router.post("/runs/{run_id}/execute", response_model=AutomationRead)
def execute(run_id: UUID, session: Db):
    try:
        repository = AutomationRepository(session)
        return AutomationService(repository).execute(repository.run(run_id))
    except (LookupError, ValueError) as error:
        raise fail(error) from error


@router.get("/adapters", response_model=list[AdapterSettingRead])
def adapter_settings(session: Db):
    repository = AutomationRepository(session)
    names = (
        "greenhouse", "lever", "ashby", "workday", "smartrecruiters",
        "icims", "taleo", "successfactors", "generic",
    )
    return [repository.setting(name) for name in names]


@router.patch("/adapters/{adapter}", response_model=AdapterSettingRead)
def update_adapter(adapter: str, payload: AdapterSettingUpdate, session: Db):
    if adapter not in {
        "greenhouse", "lever", "ashby", "workday", "smartrecruiters",
        "icims", "taleo", "successfactors", "generic",
    }:
        raise HTTPException(status_code=404, detail="unknown adapter")
    repository = AutomationRepository(session)
    value = repository.setting(adapter)
    for key, item in payload.model_dump(exclude_none=True).items():
        setattr(value, key, item)
    return repository.save_setting(value)
