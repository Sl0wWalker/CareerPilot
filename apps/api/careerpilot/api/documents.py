from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from careerpilot.api.ai import get_ai_provider
from careerpilot.db.session import get_db
from careerpilot.repositories import (
    CareerProfileRepository,
    DocumentRepository,
    JobRepository,
    MatchingRepository,
)
from careerpilot.schemas import (
    ComparisonRead,
    CoverLetterRequest,
    DocumentRead,
    DocumentUpdate,
    ScreeningAnswerRead,
    ScreeningRequest,
    TailorRequest,
)
from careerpilot.services.ai import AIProvider
from careerpilot.services.documents import DocumentService

router = APIRouter(prefix="/documents", tags=["documents"])


def dependencies(session: Annotated[Session, Depends(get_db)]):
    return (
        DocumentRepository(session),
        CareerProfileRepository(session),
        JobRepository(session),
        MatchingRepository(session),
    )


Dependencies = Annotated[tuple, Depends(dependencies)]
Provider = Annotated[AIProvider, Depends(get_ai_provider)]


def context(job_id: UUID, deps: tuple):
    documents, profiles, jobs, matching = deps
    profile = profiles.get_required()
    job = jobs.job(job_id)
    match = matching.match(job.id, profile.id)
    if match is None:
        raise LookupError("calculate the job match before generating documents")
    return documents, profile, job, match


@router.post("/jobs/{job_id}/resume", response_model=DocumentRead)
def tailor(job_id: UUID, payload: TailorRequest, deps: Dependencies, provider: Provider):
    try:
        repository, profile, job, match = context(job_id, deps)
        return DocumentRead.model_validate(
            DocumentService(repository, provider).tailor_resume(
                profile, job, match, payload.template_id, payload.use_ai
            )
        )
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.post("/jobs/{job_id}/cover-letter", response_model=DocumentRead)
def cover_letter(
    job_id: UUID, payload: CoverLetterRequest, deps: Dependencies, provider: Provider
):
    try:
        repository, profile, job, match = context(job_id, deps)
        return DocumentRead.model_validate(
            DocumentService(repository, provider).cover_letter(
                profile, job, match, payload.tone, payload.use_ai
            )
        )
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.post("/jobs/{job_id}/screening-answers", response_model=list[ScreeningAnswerRead])
def screening(
    job_id: UUID, payload: ScreeningRequest, deps: Dependencies, provider: Provider
):
    try:
        repository, profile, job, _ = context(job_id, deps)
        values = DocumentService(repository, provider).screening(
            profile, job, payload.questions, payload.use_ai
        )
        return [ScreeningAnswerRead.model_validate(value) for value in values]
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.get("", response_model=list[DocumentRead])
def list_documents(deps: Dependencies, job_id: UUID | None = None):
    return [DocumentRead.model_validate(value) for value in deps[0].list_documents(job_id)]


@router.patch("/{document_id}", response_model=DocumentRead)
def update_document(document_id: UUID, payload: DocumentUpdate, deps: Dependencies):
    try:
        value = deps[0].get(document_id)
        for key, item in payload.model_dump(exclude_none=True).items():
            setattr(value, key, item)
        return DocumentRead.model_validate(deps[0].save(value))
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.get("/{document_id}/export")
def export_document(document_id: UUID, format: str, deps: Dependencies):
    try:
        value = deps[0].get(document_id)
        data = DocumentService(deps[0]).export(value, format)
        media_type = (
            "application/pdf"
            if format == "pdf"
            else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        return Response(data, media_type=media_type)
    except (LookupError, ValueError) as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.get("/compare/{left_id}/{right_id}", response_model=ComparisonRead)
def compare(left_id: UUID, right_id: UUID, deps: Dependencies):
    try:
        result = DocumentService.compare(deps[0].get(left_id), deps[0].get(right_id))
        return ComparisonRead(left_id=left_id, right_id=right_id, **result)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
