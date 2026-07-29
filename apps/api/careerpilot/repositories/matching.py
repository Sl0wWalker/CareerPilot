from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from careerpilot.models import JobMatch, MatchingSettings


class MatchingRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def settings(self) -> MatchingSettings | None:
        return self.session.scalar(select(MatchingSettings))

    def save_settings(self, value: MatchingSettings) -> MatchingSettings:
        self.session.add(value)
        self.session.commit()
        self.session.refresh(value)
        return value

    def match(self, job_id: UUID, profile_id: UUID) -> JobMatch | None:
        return self.session.scalar(
            select(JobMatch).where(
                JobMatch.job_id == job_id, JobMatch.profile_id == profile_id
            )
        )

    def save_match(self, value: JobMatch) -> JobMatch:
        self.session.add(value)
        self.session.commit()
        self.session.refresh(value)
        return value
