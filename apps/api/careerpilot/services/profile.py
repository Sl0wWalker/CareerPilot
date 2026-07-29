from typing import Any

from pydantic import AnyUrl

from careerpilot.models import (
    Achievement,
    CareerProfile,
    Certification,
    Education,
    Experience,
    JobPreference,
    Project,
    Skill,
)
from careerpilot.repositories import CareerProfileRepository
from careerpilot.schemas import CareerProfileCreate, CareerProfileUpdate


def model_data(value: Any) -> dict[str, Any]:
    return {
        field: str(item) if isinstance(item, AnyUrl) else item
        for field, item in value.model_dump(mode="python").items()
    }


class ProfileAlreadyExistsError(Exception):
    pass


class CareerProfileService:
    def __init__(self, repository: CareerProfileRepository) -> None:
        self.repository = repository

    def get(self) -> CareerProfile:
        return self.repository.get_required()

    def create(self, payload: CareerProfileCreate) -> CareerProfile:
        if self.repository.get() is not None:
            raise ProfileAlreadyExistsError("only one local career profile is supported")

        scalar_data = payload.model_dump(
            mode="python",
            exclude={
                "experiences",
                "education",
                "projects",
                "skills",
                "certifications",
                "achievements",
                "job_preference",
            },
        )
        scalar_data = {
            field: str(value) if isinstance(value, AnyUrl) else value
            for field, value in scalar_data.items()
        }
        profile = CareerProfile(**scalar_data)
        profile.experiences = [Experience(**model_data(item)) for item in payload.experiences]
        profile.education = [Education(**model_data(item)) for item in payload.education]
        profile.projects = [Project(**model_data(item)) for item in payload.projects]
        profile.skills = [Skill(**model_data(item)) for item in payload.skills]
        profile.certifications = [
            Certification(**model_data(item)) for item in payload.certifications
        ]
        profile.achievements = [Achievement(**model_data(item)) for item in payload.achievements]
        if payload.job_preference:
            profile.job_preference = JobPreference(**model_data(payload.job_preference))
        return self.repository.add(profile)

    def update(self, payload: CareerProfileUpdate) -> CareerProfile:
        profile = self.repository.get_required()
        for field, value in payload.model_dump(mode="python", exclude_unset=True).items():
            setattr(profile, field, str(value) if isinstance(value, AnyUrl) else value)
        return self.repository.save(profile)
