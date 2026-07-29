from typing import Any
from uuid import UUID

from sqlalchemy import JSON, Boolean, Float, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from careerpilot.db.base import Base
from careerpilot.models.profile import CareerProfile, EntityMixin


class ResumeImport(EntityMixin, Base):
    __tablename__ = "resume_imports"

    profile_id: Mapped[UUID] = mapped_column(
        Uuid(native_uuid=False), ForeignKey("career_profiles.id", ondelete="CASCADE"), index=True
    )
    filename: Mapped[str] = mapped_column(String(255))
    mime_type: Mapped[str] = mapped_column(String(100))
    checksum: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    parser_version: Mapped[str] = mapped_column(String(32))
    parsing_status: Mapped[str] = mapped_column(String(32), index=True)
    raw_text: Mapped[str] = mapped_column(Text)
    warnings: Mapped[list[str]] = mapped_column(JSON, default=list)

    profile: Mapped[CareerProfile] = relationship(back_populates="resume_imports")
    facts: Mapped[list["ParsedFact"]] = relationship(
        back_populates="resume_import", cascade="all, delete-orphan"
    )


class ParsedFact(EntityMixin, Base):
    __tablename__ = "parsed_facts"

    import_id: Mapped[UUID] = mapped_column(
        Uuid(native_uuid=False), ForeignKey("resume_imports.id", ondelete="CASCADE"), index=True
    )
    entity_type: Mapped[str] = mapped_column(String(50), index=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON)
    confidence: Mapped[float] = mapped_column(Float)
    approved: Mapped[bool] = mapped_column(Boolean, default=False)
    rejected: Mapped[bool] = mapped_column(Boolean, default=False)
    source_reference: Mapped[str] = mapped_column(String(255))

    resume_import: Mapped[ResumeImport] = relationship(back_populates="facts")
