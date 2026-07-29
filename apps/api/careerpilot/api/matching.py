from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from careerpilot.api.ai import get_ai_provider
from careerpilot.db.session import get_db
from careerpilot.models import MatchingSettings
from careerpilot.repositories import CareerProfileRepository, JobRepository, MatchingRepository
from careerpilot.schemas.matching import (
    DEFAULT_WEIGHTS,
    JobMatchRead,
    MatchingSettingsRead,
    MatchingSettingsUpdate,
)
from careerpilot.services.ai import AIProvider
from careerpilot.services.matching import MatchingService

router = APIRouter(tags=["matching"])


def repositories(
    session: Annotated[Session, Depends(get_db)],
) -> tuple[JobRepository, CareerProfileRepository, MatchingRepository]:
    return (
        JobRepository(session),
        CareerProfileRepository(session),
        MatchingRepository(session),
    )


Repositories = Annotated[
    tuple[JobRepository, CareerProfileRepository, MatchingRepository],
    Depends(repositories),
]
Provider = Annotated[AIProvider, Depends(get_ai_provider)]


@router.get("/matching/settings", response_model=MatchingSettingsRead)
def get_settings(repos: Repositories) -> MatchingSettingsRead:
    value = repos[2].settings()
    if value is None:
        return MatchingSettingsRead(weights=DEFAULT_WEIGHTS)
    return MatchingSettingsRead.model_validate(value)


@router.put("/matching/settings", response_model=MatchingSettingsRead)
def update_settings(payload: MatchingSettingsUpdate, repos: Repositories) -> MatchingSettingsRead:
    value = repos[2].settings()
    if value is None:
        value = MatchingSettings(**payload.model_dump())
    else:
        for key, item in payload.model_dump().items():
            setattr(value, key, item)
    return MatchingSettingsRead.model_validate(repos[2].save_settings(value))


@router.post("/jobs/{job_id}/match", response_model=JobMatchRead)
def calculate_match(job_id: UUID, repos: Repositories, provider: Provider) -> JobMatchRead:
    jobs, profiles, matching = repos
    try:
        result = MatchingService(matching, provider).analyze(
            jobs.job(job_id), profiles.get_required(), matching.settings()
        )
        return JobMatchRead.model_validate(result)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.get("/jobs/{job_id}/match", response_model=JobMatchRead)
def get_match(job_id: UUID, repos: Repositories) -> JobMatchRead:
    jobs, profiles, matching = repos
    try:
        job = jobs.job(job_id)
        profile = profiles.get_required()
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    value = matching.match(job.id, profile.id)
    if value is None:
        raise HTTPException(status_code=404, detail="job match not calculated")
    return JobMatchRead.model_validate(value)
