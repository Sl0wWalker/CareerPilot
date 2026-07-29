from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, HttpUrl, model_validator


class Schema(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")


class EntityRead(Schema):
    id: UUID
    created_at: datetime
    updated_at: datetime


class ExperienceCreate(Schema):
    company: str = Field(min_length=1, max_length=200)
    title: str = Field(min_length=1, max_length=200)
    start_date: date
    end_date: date | None = None
    is_current: bool = False
    location: str | None = Field(default=None, max_length=200)
    description: str | None = None

    @model_validator(mode="after")
    def validate_dates(self) -> "ExperienceCreate":
        if self.end_date and self.end_date < self.start_date:
            raise ValueError("end_date cannot precede start_date")
        if self.is_current and self.end_date:
            raise ValueError("current experience cannot have an end_date")
        return self


class ExperienceRead(ExperienceCreate, EntityRead):
    pass


class EducationCreate(Schema):
    institution: str = Field(min_length=1, max_length=200)
    degree: str = Field(min_length=1, max_length=200)
    field_of_study: str | None = Field(default=None, max_length=200)
    start_year: int | None = Field(default=None, ge=1900, le=2200)
    end_year: int | None = Field(default=None, ge=1900, le=2200)

    @model_validator(mode="after")
    def validate_years(self) -> "EducationCreate":
        if self.start_year and self.end_year and self.end_year < self.start_year:
            raise ValueError("end_year cannot precede start_year")
        return self


class EducationRead(EducationCreate, EntityRead):
    pass


class ProjectCreate(Schema):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None
    url: HttpUrl | None = None


class ProjectRead(ProjectCreate, EntityRead):
    pass


class SkillCreate(Schema):
    name: str = Field(min_length=1, max_length=100)
    years_experience: int | None = Field(default=None, ge=0, le=100)
    proficiency: str | None = Field(default=None, max_length=50)


class SkillRead(SkillCreate, EntityRead):
    pass


class CertificationCreate(Schema):
    name: str = Field(min_length=1, max_length=200)
    issuer: str | None = Field(default=None, max_length=200)
    issued_on: date | None = None
    expires_on: date | None = None
    credential_url: HttpUrl | None = None

    @model_validator(mode="after")
    def validate_dates(self) -> "CertificationCreate":
        if self.issued_on and self.expires_on and self.expires_on < self.issued_on:
            raise ValueError("expires_on cannot precede issued_on")
        return self


class CertificationRead(CertificationCreate, EntityRead):
    pass


class AchievementCreate(Schema):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1)
    achieved_on: date | None = None


class AchievementRead(AchievementCreate, EntityRead):
    pass


class JobPreferenceCreate(Schema):
    target_roles: str | None = None
    preferred_locations: str | None = None
    remote_ok: bool = True
    willing_to_relocate: bool = False
    minimum_salary: int | None = Field(default=None, ge=0)
    requires_sponsorship: bool | None = None


class JobPreferenceRead(JobPreferenceCreate, EntityRead):
    pass


class CareerProfileBase(Schema):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=50)
    city: str | None = Field(default=None, max_length=100)
    region: str | None = Field(default=None, max_length=100)
    country: str | None = Field(default=None, max_length=100)
    linkedin_url: HttpUrl | None = None
    portfolio_url: HttpUrl | None = None


class CareerProfileCreate(CareerProfileBase):
    experiences: list[ExperienceCreate] = Field(default_factory=list)
    education: list[EducationCreate] = Field(default_factory=list)
    projects: list[ProjectCreate] = Field(default_factory=list)
    skills: list[SkillCreate] = Field(default_factory=list)
    certifications: list[CertificationCreate] = Field(default_factory=list)
    achievements: list[AchievementCreate] = Field(default_factory=list)
    job_preference: JobPreferenceCreate | None = None


class CareerProfileUpdate(Schema):
    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=50)
    city: str | None = Field(default=None, max_length=100)
    region: str | None = Field(default=None, max_length=100)
    country: str | None = Field(default=None, max_length=100)
    linkedin_url: HttpUrl | None = None
    portfolio_url: HttpUrl | None = None


class CareerProfileRead(CareerProfileBase, EntityRead):
    experiences: list[ExperienceRead] = Field(default_factory=list)
    education: list[EducationRead] = Field(default_factory=list)
    projects: list[ProjectRead] = Field(default_factory=list)
    skills: list[SkillRead] = Field(default_factory=list)
    certifications: list[CertificationRead] = Field(default_factory=list)
    achievements: list[AchievementRead] = Field(default_factory=list)
    job_preference: JobPreferenceRead | None = None
