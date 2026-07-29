from datetime import date
from hashlib import sha256
from typing import Any
from uuid import UUID

from careerpilot.models import (
    Achievement,
    Certification,
    Education,
    Experience,
    ParsedFact,
    Project,
    ResumeImport,
    Skill,
)
from careerpilot.repositories import CareerProfileRepository, ResumeImportRepository
from careerpilot.schemas import ApproveFactsRequest, ParsedFactUpdate
from careerpilot.services.parser import ResumeParserPipeline

MAX_RESUME_BYTES = 10 * 1024 * 1024


class DuplicateResumeError(Exception):
    pass


class ResumeImportService:
    def __init__(
        self,
        repository: ResumeImportRepository,
        profile_repository: CareerProfileRepository,
        pipeline: ResumeParserPipeline | None = None,
    ) -> None:
        self.repository = repository
        self.profile_repository = profile_repository
        self.pipeline = pipeline or ResumeParserPipeline()

    def import_resume(self, filename: str, mime_type: str, content: bytes) -> ResumeImport:
        if not content:
            raise ValueError("resume file is empty")
        if len(content) > MAX_RESUME_BYTES:
            raise ValueError("resume file exceeds the 10 MB limit")
        checksum = sha256(content).hexdigest()
        existing = self.repository.get_by_checksum(checksum)
        if existing:
            raise DuplicateResumeError(str(existing.id))
        profile = self.profile_repository.get_required()
        result = self.pipeline.run(filename, mime_type, content)
        resume_import = ResumeImport(
            profile_id=profile.id,
            filename=filename,
            mime_type=mime_type,
            checksum=checksum,
            parser_version=self.pipeline.parser_version,
            parsing_status="review_required",
            raw_text=result.raw_text,
            warnings=result.warnings,
            facts=[
                ParsedFact(
                    entity_type=fact.entity_type,
                    payload=fact.payload,
                    confidence=fact.confidence,
                    source_reference=fact.source_reference,
                )
                for fact in result.facts
            ],
        )
        return self.repository.add(resume_import)

    def list(self) -> list[ResumeImport]:
        return self.repository.list()

    def get(self, import_id: UUID) -> ResumeImport:
        return self.repository.get_required(import_id)

    def delete(self, import_id: UUID) -> None:
        self.repository.delete(self.repository.get_required(import_id))

    def update_fact(
        self, import_id: UUID, fact_id: UUID, payload: ParsedFactUpdate
    ) -> ResumeImport:
        fact = self.repository.get_fact(import_id, fact_id)
        if fact is None:
            raise LookupError("parsed fact not found")
        changes = payload.model_dump(exclude_unset=True)
        for field, value in changes.items():
            setattr(fact, field, value)
        if payload.approved is True:
            fact.rejected = False
        if payload.rejected is True:
            fact.approved = False
        return self.repository.save(self.repository.get_required(import_id))

    def approve(self, import_id: UUID, request: ApproveFactsRequest) -> ResumeImport:
        resume_import = self.repository.get_required(import_id)
        if resume_import.parsing_status == "approved":
            return resume_import
        profile = self.profile_repository.get_required()
        selected = set(request.fact_ids) if request.fact_ids is not None else None
        for fact in resume_import.facts:
            should_apply = fact.approved if selected is None else fact.id in selected
            if fact.rejected or not should_apply:
                continue
            self._apply(profile, fact)
            fact.approved = True
            fact.rejected = False
        resume_import.parsing_status = "approved"
        self.repository.session.add(profile)
        return self.repository.save(resume_import)

    def _apply(self, profile: Any, fact: ParsedFact) -> None:
        payload = dict(fact.payload)
        if fact.entity_type == "skill":
            name = str(payload.get("name", "")).strip()
            if name and all(item.name.casefold() != name.casefold() for item in profile.skills):
                profile.skills.append(Skill(name=name))
        elif fact.entity_type == "experience":
            start_date = self._date(payload.get("start_date"))
            if start_date and payload.get("company") and payload.get("title"):
                profile.experiences.append(
                    Experience(
                        company=str(payload["company"]),
                        title=str(payload["title"]),
                        start_date=start_date,
                        end_date=self._date(payload.get("end_date")),
                        is_current=bool(payload.get("is_current", False)),
                        description=str(payload.get("description") or "") or None,
                    )
                )
        elif fact.entity_type == "education":
            if payload.get("institution") and payload.get("degree"):
                profile.education.append(
                    Education(
                        institution=str(payload["institution"]),
                        degree=str(payload["degree"]),
                        start_year=self._integer(payload.get("start_year")),
                        end_year=self._integer(payload.get("end_year")),
                    )
                )
        elif fact.entity_type == "project" and payload.get("name"):
            profile.projects.append(
                Project(
                    name=str(payload["name"]),
                    description=str(payload.get("description") or "") or None,
                )
            )
        elif fact.entity_type == "certification" and payload.get("name"):
            profile.certifications.append(Certification(name=str(payload["name"])))
        elif fact.entity_type == "achievement" and payload.get("title"):
            profile.achievements.append(
                Achievement(
                    title=str(payload["title"]),
                    description=str(payload.get("description") or payload["title"]),
                )
            )

    @staticmethod
    def _date(value: object) -> date | None:
        try:
            return date.fromisoformat(str(value)) if value else None
        except ValueError:
            return None

    @staticmethod
    def _integer(value: object) -> int | None:
        try:
            return int(str(value)) if value is not None else None
        except ValueError:
            return None
