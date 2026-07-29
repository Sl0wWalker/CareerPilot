from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AISchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")


class AISettingsUpdate(AISchema):
    provider: Literal["ollama", "gemini", "openai_compatible"]
    model: str = Field(min_length=1, max_length=128)
    embedding_model: str = Field(min_length=1, max_length=128)
    base_url: str = Field(min_length=1, max_length=2048)
    temperature: float = Field(ge=0, le=2)
    max_tokens: int = Field(ge=64, le=32768)


class AISettingsRead(AISettingsUpdate):
    id: UUID


class AIHealthRead(AISchema):
    provider: str
    model: str
    available: bool
    detail: str


class AISuggestionRead(AISchema):
    id: UUID
    suggestion_type: str
    status: str
    source_type: str
    source_id: str | None
    original: dict[str, Any] | None
    proposed: dict[str, Any]
    rationale: str
    confidence: float
    created_at: datetime


class SuggestionUpdate(AISchema):
    status: Literal["approved", "rejected", "pending"]
    proposed: dict[str, Any] | None = None


class SummaryRead(AISchema):
    short: str
    medium: str
    linkedin: str


class SearchRequest(AISchema):
    query: str = Field(min_length=1, max_length=500)
    limit: int = Field(default=10, ge=1, le=50)


class SearchResult(AISchema):
    entity_type: str
    entity_id: str
    text: str
    score: float
