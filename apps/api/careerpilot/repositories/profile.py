from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from careerpilot.models import CareerProfile


class CareerProfileRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self) -> CareerProfile | None:
        statement = select(CareerProfile).options(
            selectinload(CareerProfile.experiences),
            selectinload(CareerProfile.education),
            selectinload(CareerProfile.projects),
            selectinload(CareerProfile.skills),
            selectinload(CareerProfile.certifications),
            selectinload(CareerProfile.achievements),
            selectinload(CareerProfile.job_preference),
        )
        return self.session.scalar(statement)

    def add(self, profile: CareerProfile) -> CareerProfile:
        self.session.add(profile)
        self.session.commit()
        return self.get_required()

    def save(self, profile: CareerProfile) -> CareerProfile:
        self.session.add(profile)
        self.session.commit()
        return self.get_required()

    def get_required(self) -> CareerProfile:
        profile = self.get()
        if profile is None:
            raise LookupError("career profile not found")
        return profile
