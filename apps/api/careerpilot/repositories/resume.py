from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from careerpilot.models import ParsedFact, ResumeImport


class ResumeImportRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list(self) -> list[ResumeImport]:
        statement = select(ResumeImport).order_by(ResumeImport.created_at.desc())
        return list(self.session.scalars(statement))

    def get(self, import_id: UUID) -> ResumeImport | None:
        statement = (
            select(ResumeImport)
            .where(ResumeImport.id == import_id)
            .options(selectinload(ResumeImport.facts))
        )
        return self.session.scalar(statement)

    def get_by_checksum(self, checksum: str) -> ResumeImport | None:
        return self.session.scalar(select(ResumeImport).where(ResumeImport.checksum == checksum))

    def add(self, resume_import: ResumeImport) -> ResumeImport:
        self.session.add(resume_import)
        self.session.commit()
        return self.get_required(resume_import.id)

    def save(self, resume_import: ResumeImport) -> ResumeImport:
        self.session.add(resume_import)
        self.session.commit()
        return self.get_required(resume_import.id)

    def delete(self, resume_import: ResumeImport) -> None:
        self.session.delete(resume_import)
        self.session.commit()

    def get_fact(self, import_id: UUID, fact_id: UUID) -> ParsedFact | None:
        return self.session.scalar(
            select(ParsedFact).where(
                ParsedFact.import_id == import_id,
                ParsedFact.id == fact_id,
            )
        )

    def get_required(self, import_id: UUID) -> ResumeImport:
        resume_import = self.get(import_id)
        if resume_import is None:
            raise LookupError("resume import not found")
        return resume_import
