from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from careerpilot.core.config import Settings, get_settings
from careerpilot.db.session import get_db
from careerpilot.repositories import AIRepository, CareerProfileRepository
from careerpilot.schemas import (
    AIHealthRead,
    AISettingsRead,
    AISettingsUpdate,
    AISuggestionRead,
    SearchRequest,
    SearchResult,
    SuggestionUpdate,
    SummaryRead,
)
from careerpilot.services.ai import AIProvider, create_provider
from careerpilot.services.ai_profile import AIProfileService

router = APIRouter(prefix="/ai", tags=["ai"])


def get_ai_provider(
    settings: Annotated[Settings, Depends(get_settings)],
    session: Annotated[Session, Depends(get_db)],
) -> AIProvider:
    saved = AIRepository(session).settings()
    if saved is not None:
        settings = settings.model_copy(
            update={
                "ai_provider": saved.provider,
                "ai_model": saved.model,
                "ai_embedding_model": saved.embedding_model,
                "ai_base_url": saved.base_url,
            }
        )
    return create_provider(settings)


def get_ai_service(
    session: Annotated[Session, Depends(get_db)],
    provider: Annotated[AIProvider, Depends(get_ai_provider)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> AIProfileService:
    return AIProfileService(
        AIRepository(session), CareerProfileRepository(session), provider, settings
    )


AIService = Annotated[AIProfileService, Depends(get_ai_service)]
Provider = Annotated[AIProvider, Depends(get_ai_provider)]


@router.get("/health", response_model=AIHealthRead)
def ai_health(provider: Provider, service: AIService) -> AIHealthRead:
    available, detail = provider.health()
    settings = service.get_settings()
    return AIHealthRead(
        provider=settings.provider,
        model=settings.model,
        available=available,
        detail=detail,
    )


@router.get("/models", response_model=list[str])
def ai_models(provider: Provider) -> list[str]:
    try:
        return provider.list_models()
    except Exception as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


@router.post("/profile/enrich", response_model=list[AISuggestionRead])
def enrich_profile(service: AIService) -> list[AISuggestionRead]:
    try:
        return [AISuggestionRead.model_validate(item) for item in service.enrich()]
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.post("/profile/normalize", response_model=list[AISuggestionRead])
def normalize_profile(service: AIService) -> list[AISuggestionRead]:
    return enrich_profile(service)


@router.post("/profile/summarize", response_model=SummaryRead)
def summarize_profile(service: AIService) -> SummaryRead:
    try:
        return SummaryRead.model_validate(service.summarize())
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.post("/profile/search", response_model=list[SearchResult])
def search_profile(payload: SearchRequest, service: AIService) -> list[SearchResult]:
    try:
        values = service.search(payload.query, payload.limit)
        return [SearchResult.model_validate(item) for item in values]
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.post("/profile/embeddings/rebuild")
def rebuild_embeddings(service: AIService) -> dict[str, int]:
    return {"count": service.rebuild_embeddings()}


@router.get("/suggestions", response_model=list[AISuggestionRead])
def list_suggestions(service: AIService) -> list[AISuggestionRead]:
    return [AISuggestionRead.model_validate(item) for item in service.repository.suggestions()]


@router.patch("/suggestions/{suggestion_id}", response_model=AISuggestionRead)
def update_suggestion(
    suggestion_id: UUID, payload: SuggestionUpdate, service: AIService
) -> AISuggestionRead:
    try:
        return AISuggestionRead.model_validate(
            service.update_suggestion(suggestion_id, payload.status, payload.proposed)
        )
    except LookupError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error


@router.get("/settings", response_model=AISettingsRead)
def read_ai_settings(service: AIService) -> AISettingsRead:
    return AISettingsRead.model_validate(service.get_settings())


@router.put("/settings", response_model=AISettingsRead)
def write_ai_settings(payload: AISettingsUpdate, service: AIService) -> AISettingsRead:
    return AISettingsRead.model_validate(service.update_settings(payload))
