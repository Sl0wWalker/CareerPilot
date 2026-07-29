from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from careerpilot.api.ai import get_ai_provider
from careerpilot.db.session import get_db
from careerpilot.models import JobSource, SavedSearch, ScheduledSearch
from careerpilot.repositories import CareerProfileRepository, JobRepository
from careerpilot.schemas.jobs import (
    JobRead,
    JobSearchRequest,
    SavedSearchCreate,
    SavedSearchRead,
    ScheduledSearchCreate,
    ScheduledSearchRead,
    SourceCreate,
    SourceRead,
    SyncResult,
)
from careerpilot.services.ai import AIProvider
from careerpilot.services.job_relevance import JobRelevanceService
from careerpilot.services.jobs import JobIngestionService

router = APIRouter(prefix="/jobs", tags=["jobs"])


def get_job_repository(session: Annotated[Session, Depends(get_db)]) -> JobRepository:
    return JobRepository(session)


Repository = Annotated[JobRepository, Depends(get_job_repository)]
Provider = Annotated[AIProvider, Depends(get_ai_provider)]


def read_job(value: Any) -> JobRead:
    return JobRead(
        id=value.id,
        title=value.title,
        company_name=value.company.name,
        source_provider=value.source_provider,
        canonical_url=value.canonical_url,
        application_url=value.application_url,
        description=value.description,
        location_raw=value.location_raw,
        city=value.city,
        region=value.region,
        country=value.country,
        workplace_type=value.workplace_type,
        employment_type=value.employment_type,
        salary_min=value.salary_min,
        salary_max=value.salary_max,
        salary_currency=value.salary_currency,
        salary_period=value.salary_period,
        posted_at=value.posted_at,
        is_favorite=value.is_favorite,
        relevance_score=value.relevance_score,
        relevance_analysis=value.relevance_analysis,
    )


@router.post("/sources", response_model=SourceRead, status_code=status.HTTP_201_CREATED)
def create_source(payload: SourceCreate, repo: Repository) -> SourceRead:
    value = JobSource(
        provider=payload.provider,
        external_key=payload.external_key,
        name=payload.name,
        source_url=str(payload.source_url) if payload.source_url else None,
        configuration=payload.configuration,
    )
    return SourceRead.model_validate(repo.add_source(value))


@router.get("/sources", response_model=list[SourceRead])
def list_sources(repo: Repository) -> list[SourceRead]:
    return [SourceRead.model_validate(item) for item in repo.sources()]


@router.post("/sources/{source_id}/sync", response_model=SyncResult)
def sync_source(source_id: UUID, repo: Repository) -> SyncResult:
    try:
        result = JobIngestionService(repo).sync(repo.source(source_id))
        return SyncResult(source_id=source_id, **result)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.post("/search", response_model=list[JobRead])
def search_jobs(payload: JobSearchRequest, repo: Repository) -> list[JobRead]:
    return [read_job(item) for item in repo.search(payload)]


@router.post("/saved-searches", response_model=SavedSearchRead, status_code=201)
def create_saved_search(payload: SavedSearchCreate, repo: Repository) -> SavedSearchRead:
    value = repo.add_saved_search(SavedSearch(**payload.model_dump()))
    return SavedSearchRead.model_validate(value)


@router.get("/saved-searches", response_model=list[SavedSearchRead])
def list_saved_searches(repo: Repository) -> list[SavedSearchRead]:
    return [SavedSearchRead.model_validate(item) for item in repo.saved_searches()]


@router.post("/scheduled-searches", response_model=ScheduledSearchRead, status_code=201)
def create_schedule(
    payload: ScheduledSearchCreate, repo: Repository
) -> ScheduledSearchRead:
    return ScheduledSearchRead.model_validate(
        repo.add_schedule(ScheduledSearch(**payload.model_dump()))
    )


@router.get("/scheduled-searches", response_model=list[ScheduledSearchRead])
def list_schedules(repo: Repository) -> list[ScheduledSearchRead]:
    return [ScheduledSearchRead.model_validate(item) for item in repo.schedules()]


@router.get("/{job_id}", response_model=JobRead)
def get_job(job_id: UUID, repo: Repository) -> JobRead:
    try:
        return read_job(repo.job(job_id))
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.patch("/{job_id}/favorite", response_model=JobRead)
def favorite_job(job_id: UUID, repo: Repository) -> JobRead:
    try:
        job = repo.job(job_id)
        job.is_favorite = not job.is_favorite
        return read_job(repo.save_job(job))
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.post("/{job_id}/analyze", response_model=JobRead)
def analyze_job(
    job_id: UUID,
    repo: Repository,
    provider: Provider,
    session: Annotated[Session, Depends(get_db)],
) -> JobRead:
    try:
        return read_job(
            JobRelevanceService(repo, CareerProfileRepository(session), provider).analyze(
                repo.job(job_id)
            )
        )
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
