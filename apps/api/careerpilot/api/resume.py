from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy.orm import Session

from careerpilot.db.session import get_db
from careerpilot.repositories import CareerProfileRepository, ResumeImportRepository
from careerpilot.schemas import (
    ApproveFactsRequest,
    ParsedFactUpdate,
    ResumeImportDetail,
    ResumeImportRead,
)
from careerpilot.services.parser.extractors.base import ResumeExtractionError
from careerpilot.services.resume import DuplicateResumeError, ResumeImportService

router = APIRouter(prefix="/resume", tags=["resume"])


def get_resume_service(session: Annotated[Session, Depends(get_db)]) -> ResumeImportService:
    return ResumeImportService(
        ResumeImportRepository(session),
        CareerProfileRepository(session),
    )


ResumeService = Annotated[ResumeImportService, Depends(get_resume_service)]


def detail_or_404(service: ResumeImportService, import_id: UUID) -> ResumeImportDetail:
    try:
        return ResumeImportDetail.model_validate(service.get(import_id))
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.post("/import", response_model=ResumeImportDetail, status_code=status.HTTP_201_CREATED)
async def import_resume(
    service: ResumeService,
    request: Request,
    filename: Annotated[str, Query(min_length=1, max_length=255)],
) -> ResumeImportDetail:
    try:
        content = await request.body()
        resume_import = service.import_resume(
            filename,
            request.headers.get("content-type", "application/octet-stream"),
            content,
        )
        return ResumeImportDetail.model_validate(resume_import)
    except DuplicateResumeError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"message": "resume already imported", "import_id": str(error)},
        ) from error
    except LookupError as error:
        raise HTTPException(status_code=404, detail="create a career profile first") from error
    except (ValueError, ResumeExtractionError) as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.get("/imports", response_model=list[ResumeImportRead])
def list_imports(service: ResumeService) -> list[ResumeImportRead]:
    return [ResumeImportRead.model_validate(item) for item in service.list()]


@router.get("/import/{import_id}", response_model=ResumeImportDetail)
def get_import(service: ResumeService, import_id: UUID) -> ResumeImportDetail:
    return detail_or_404(service, import_id)


@router.delete("/import/{import_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_import(service: ResumeService, import_id: UUID) -> Response:
    try:
        service.delete(import_id)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/import/{import_id}/review", response_model=ResumeImportDetail)
def review_import(service: ResumeService, import_id: UUID) -> ResumeImportDetail:
    return detail_or_404(service, import_id)


@router.post("/import/{import_id}/approve", response_model=ResumeImportDetail)
def approve_import(
    service: ResumeService,
    import_id: UUID,
    request: ApproveFactsRequest,
) -> ResumeImportDetail:
    try:
        return ResumeImportDetail.model_validate(service.approve(import_id, request))
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.patch("/import/{import_id}/fact/{fact_id}", response_model=ResumeImportDetail)
def update_fact(
    service: ResumeService,
    import_id: UUID,
    fact_id: UUID,
    payload: ParsedFactUpdate,
) -> ResumeImportDetail:
    try:
        return ResumeImportDetail.model_validate(service.update_fact(import_id, fact_id, payload))
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
