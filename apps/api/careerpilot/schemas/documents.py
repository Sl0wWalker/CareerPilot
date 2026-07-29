from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TailorRequest(BaseModel):
    template_id: UUID | None = None
    use_ai: bool = True


class CoverLetterRequest(BaseModel):
    tone: Literal["concise", "professional", "enthusiastic"] = "professional"
    use_ai: bool = True


class ScreeningRequest(BaseModel):
    questions: list[str] = Field(min_length=1, max_length=50)
    use_ai: bool = True


class DocumentUpdate(BaseModel):
    content: dict[str, Any] | None = None
    status: Literal["draft", "approved", "rejected"] | None = None


class DocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    profile_id: UUID
    job_id: UUID | None
    template_id: UUID | None
    document_type: str
    version: int
    status: str
    title: str
    content: dict[str, Any]
    evidence: list[dict[str, Any]]
    keyword_coverage: dict[str, Any]
    model: str | None
    prompt_version: str | None


class ScreeningAnswerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    job_id: UUID
    question: str
    normalized_question: str
    answer: str | None
    evidence: list[dict[str, Any]]
    confidence: float
    sensitive: bool
    status: str


class ComparisonRead(BaseModel):
    left_id: UUID
    right_id: UUID
    added: list[str]
    removed: list[str]
    unchanged: list[str]
