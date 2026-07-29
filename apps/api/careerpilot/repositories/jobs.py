from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.orm import Session, joinedload

from careerpilot.models import Company, Job, JobSource, SavedSearch, ScheduledSearch
from careerpilot.schemas.jobs import JobSearchRequest


class JobRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add_source(self, value: JobSource) -> JobSource:
        self.session.add(value)
        self.session.commit()
        self.session.refresh(value)
        return value

    def sources(self) -> list[JobSource]:
        return list(self.session.scalars(select(JobSource).order_by(JobSource.name)))

    def source(self, source_id: UUID) -> JobSource:
        value = self.session.get(JobSource, source_id)
        if value is None:
            raise LookupError("job source not found")
        return value

    def get_or_create_company(self, value: Company) -> Company:
        existing = self.session.scalar(select(Company).where(Company.name == value.name))
        if existing:
            return existing
        self.session.add(value)
        self.session.flush()
        return value

    def by_external(self, provider: str, external_id: str) -> Job | None:
        return self.session.scalar(
            select(Job).where(Job.source_provider == provider, Job.external_id == external_id)
        )

    def by_fingerprint(self, fingerprint: str) -> Job | None:
        return self.session.scalar(select(Job).where(Job.fingerprint == fingerprint))

    def add_job(self, value: Job) -> Job:
        self.session.add(value)
        self.session.commit()
        return value

    def update_job(self, job: Job, values: dict[str, Any]) -> Job:
        for key, value in values.items():
            if key != "fingerprint":
                setattr(job, key, value)
        self.session.commit()
        return job

    def mark_synced(self, source: JobSource) -> None:
        source.last_synced_at = datetime.now(UTC)
        self.session.commit()

    def job(self, job_id: UUID) -> Job:
        value = self.session.scalar(
            select(Job).options(joinedload(Job.company)).where(Job.id == job_id)
        )
        if value is None:
            raise LookupError("job not found")
        return value

    def search(self, request: JobSearchRequest) -> list[Job]:
        statement = select(Job).options(joinedload(Job.company)).join(Company)
        if request.query:
            query = f"%{request.query.casefold()}%"
            statement = statement.where(
                or_(
                    Job.search_text.ilike(query),
                    Job.title.ilike(query),
                    Company.name.ilike(query),
                )
            )
        if request.company:
            statement = statement.where(Company.name.ilike(f"%{request.company}%"))
        if request.location:
            statement = statement.where(Job.location_raw.ilike(f"%{request.location}%"))
        if request.workplace_type:
            statement = statement.where(Job.workplace_type == request.workplace_type)
        if request.employment_type:
            statement = statement.where(Job.employment_type == request.employment_type)
        if request.favorite_only:
            statement = statement.where(Job.is_favorite.is_(True))
        if request.minimum_salary is not None:
            statement = statement.where(Job.salary_max >= request.minimum_salary)
        return list(
            self.session.scalars(
                statement.order_by(Job.posted_at.desc(), Job.created_at.desc())
                .offset(request.offset)
                .limit(request.limit)
            )
        )

    def save_job(self, job: Job) -> Job:
        self.session.add(job)
        self.session.commit()
        self.session.refresh(job)
        return job

    def add_saved_search(self, value: SavedSearch) -> SavedSearch:
        self.session.add(value)
        self.session.commit()
        self.session.refresh(value)
        return value

    def saved_searches(self) -> list[SavedSearch]:
        return list(self.session.scalars(select(SavedSearch).order_by(SavedSearch.name)))

    def add_schedule(self, value: ScheduledSearch) -> ScheduledSearch:
        self.session.add(value)
        self.session.commit()
        self.session.refresh(value)
        return value

    def schedules(self) -> list[ScheduledSearch]:
        return list(self.session.scalars(select(ScheduledSearch)))

