from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from careerpilot.models import DocumentVersion, ResumeTemplate, ScreeningAnswer


class DocumentRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def next_version(self, profile_id: UUID, document_type: str, job_id: UUID | None) -> int:
        value = self.session.scalar(
            select(func.max(DocumentVersion.version)).where(
                DocumentVersion.profile_id == profile_id,
                DocumentVersion.document_type == document_type,
                DocumentVersion.job_id == job_id,
            )
        )
        return (value or 0) + 1

    def save(self, value: DocumentVersion) -> DocumentVersion:
        self.session.add(value)
        self.session.commit()
        self.session.refresh(value)
        return value

    def get(self, document_id: UUID) -> DocumentVersion:
        value = self.session.get(DocumentVersion, document_id)
        if value is None:
            raise LookupError("document not found")
        return value

    def list_documents(self, job_id: UUID | None = None) -> list[DocumentVersion]:
        statement = select(DocumentVersion)
        if job_id:
            statement = statement.where(DocumentVersion.job_id == job_id)
        return list(self.session.scalars(statement.order_by(DocumentVersion.created_at.desc())))

    def templates(self) -> list[ResumeTemplate]:
        return list(self.session.scalars(select(ResumeTemplate).order_by(ResumeTemplate.name)))

    def save_answers(self, values: list[ScreeningAnswer]) -> list[ScreeningAnswer]:
        self.session.add_all(values)
        self.session.commit()
        for value in values:
            self.session.refresh(value)
        return values
