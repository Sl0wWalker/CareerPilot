from datetime import UTC, date, datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from careerpilot.db.base import Base

if TYPE_CHECKING:
    from careerpilot.models.resume import ResumeImport


def utc_now() -> datetime:
    return datetime.now(UTC)


class EntityMixin:
    id: Mapped[UUID] = mapped_column(Uuid(native_uuid=False), primary_key=True, default=uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )


class CareerProfile(EntityMixin, Base):
    __tablename__ = "career_profiles"

    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str | None] = mapped_column(String(320))
    phone: Mapped[str | None] = mapped_column(String(50))
    city: Mapped[str | None] = mapped_column(String(100))
    region: Mapped[str | None] = mapped_column(String(100))
    country: Mapped[str | None] = mapped_column(String(100))
    linkedin_url: Mapped[str | None] = mapped_column(String(2048))
    portfolio_url: Mapped[str | None] = mapped_column(String(2048))

    experiences: Mapped[list["Experience"]] = relationship(
        back_populates="profile", cascade="all, delete-orphan"
    )
    education: Mapped[list["Education"]] = relationship(
        back_populates="profile", cascade="all, delete-orphan"
    )
    projects: Mapped[list["Project"]] = relationship(
        back_populates="profile", cascade="all, delete-orphan"
    )
    skills: Mapped[list["Skill"]] = relationship(
        back_populates="profile", cascade="all, delete-orphan"
    )
    certifications: Mapped[list["Certification"]] = relationship(
        back_populates="profile", cascade="all, delete-orphan"
    )
    achievements: Mapped[list["Achievement"]] = relationship(
        back_populates="profile", cascade="all, delete-orphan"
    )
    job_preference: Mapped["JobPreference | None"] = relationship(
        back_populates="profile", cascade="all, delete-orphan", uselist=False
    )
    resume_imports: Mapped[list["ResumeImport"]] = relationship(
        back_populates="profile", cascade="all, delete-orphan"
    )


class ProfileChildMixin(EntityMixin):
    profile_id: Mapped[UUID] = mapped_column(
        Uuid(native_uuid=False), ForeignKey("career_profiles.id", ondelete="CASCADE"), index=True
    )


class Experience(ProfileChildMixin, Base):
    __tablename__ = "experiences"

    company: Mapped[str] = mapped_column(String(200))
    title: Mapped[str] = mapped_column(String(200))
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    is_current: Mapped[bool] = mapped_column(Boolean, default=False)
    location: Mapped[str | None] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)
    profile: Mapped[CareerProfile] = relationship(back_populates="experiences")


class Education(ProfileChildMixin, Base):
    __tablename__ = "education"

    institution: Mapped[str] = mapped_column(String(200))
    degree: Mapped[str] = mapped_column(String(200))
    field_of_study: Mapped[str | None] = mapped_column(String(200))
    start_year: Mapped[int | None] = mapped_column(Integer)
    end_year: Mapped[int | None] = mapped_column(Integer)
    profile: Mapped[CareerProfile] = relationship(back_populates="education")


class Project(ProfileChildMixin, Base):
    __tablename__ = "projects"

    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)
    url: Mapped[str | None] = mapped_column(String(2048))
    profile: Mapped[CareerProfile] = relationship(back_populates="projects")


class Skill(ProfileChildMixin, Base):
    __tablename__ = "skills"

    name: Mapped[str] = mapped_column(String(100))
    years_experience: Mapped[int | None] = mapped_column(Integer)
    proficiency: Mapped[str | None] = mapped_column(String(50))
    profile: Mapped[CareerProfile] = relationship(back_populates="skills")


class Certification(ProfileChildMixin, Base):
    __tablename__ = "certifications"

    name: Mapped[str] = mapped_column(String(200))
    issuer: Mapped[str | None] = mapped_column(String(200))
    issued_on: Mapped[date | None] = mapped_column(Date)
    expires_on: Mapped[date | None] = mapped_column(Date)
    credential_url: Mapped[str | None] = mapped_column(String(2048))
    profile: Mapped[CareerProfile] = relationship(back_populates="certifications")


class Achievement(ProfileChildMixin, Base):
    __tablename__ = "achievements"

    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    achieved_on: Mapped[date | None] = mapped_column(Date)
    profile: Mapped[CareerProfile] = relationship(back_populates="achievements")


class JobPreference(ProfileChildMixin, Base):
    __tablename__ = "job_preferences"

    profile_id: Mapped[UUID] = mapped_column(
        Uuid(native_uuid=False),
        ForeignKey("career_profiles.id", ondelete="CASCADE"),
        unique=True,
        index=True,
    )
    target_roles: Mapped[str | None] = mapped_column(Text)
    preferred_locations: Mapped[str | None] = mapped_column(Text)
    remote_ok: Mapped[bool] = mapped_column(Boolean, default=True)
    willing_to_relocate: Mapped[bool] = mapped_column(Boolean, default=False)
    minimum_salary: Mapped[int | None] = mapped_column(Integer)
    requires_sponsorship: Mapped[bool | None] = mapped_column(Boolean)
    profile: Mapped[CareerProfile] = relationship(back_populates="job_preference")
