from typing import Any
from uuid import UUID

from sqlalchemy import JSON, Boolean, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from careerpilot.db.base import Base
from careerpilot.models.profile import EntityMixin


class ResumeTemplate(EntityMixin, Base):
    __tablename__ = "resume_templates"

    name: Mapped[str] = mapped_column(String(120), unique=True)
    description: Mapped[str] = mapped_column(Text)
    style: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)


class DocumentVersion(EntityMixin, Base):
    __tablename__ = "document_versions"

    profile_id: Mapped[UUID] = mapped_column(
        Uuid(native_uuid=False), ForeignKey("career_profiles.id", ondelete="CASCADE"), index=True
    )
    job_id: Mapped[UUID | None] = mapped_column(
        Uuid(native_uuid=False), ForeignKey("jobs.id", ondelete="SET NULL"), index=True
    )
    template_id: Mapped[UUID | None] = mapped_column(
        Uuid(native_uuid=False), ForeignKey("resume_templates.id", ondelete="SET NULL")
    )
    document_type: Mapped[str] = mapped_column(String(32), index=True)
    version: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(24), default="draft", index=True)
    title: Mapped[str] = mapped_column(String(240))
    content: Mapped[dict[str, Any]] = mapped_column(JSON)
    evidence: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    keyword_coverage: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    model: Mapped[str | None] = mapped_column(String(128))
    prompt_version: Mapped[str | None] = mapped_column(String(32))


class DocumentChange(EntityMixin, Base):
    __tablename__ = "document_changes"

    document_id: Mapped[UUID] = mapped_column(
        Uuid(native_uuid=False),
        ForeignKey("document_versions.id", ondelete="CASCADE"),
        index=True,
    )
    section: Mapped[str] = mapped_column(String(64))
    original: Mapped[str | None] = mapped_column(Text)
    proposed: Mapped[str] = mapped_column(Text)
    evidence_ids: Mapped[list[str]] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(24), default="pending")


class ScreeningAnswer(EntityMixin, Base):
    __tablename__ = "screening_answers"

    profile_id: Mapped[UUID] = mapped_column(
        Uuid(native_uuid=False), ForeignKey("career_profiles.id", ondelete="CASCADE"), index=True
    )
    job_id: Mapped[UUID] = mapped_column(
        Uuid(native_uuid=False), ForeignKey("jobs.id", ondelete="CASCADE"), index=True
    )
    question: Mapped[str] = mapped_column(Text)
    normalized_question: Mapped[str] = mapped_column(String(200), index=True)
    answer: Mapped[str | None] = mapped_column(Text)
    evidence: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    confidence: Mapped[float] = mapped_column(default=0.0)
    sensitive: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(24), default="needs_review")
