from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ResumeSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")


class ParsedFactRead(ResumeSchema):
    id: UUID
    import_id: UUID
    entity_type: str
    payload: dict[str, Any]
    confidence: float
    approved: bool
    rejected: bool
    source_reference: str
    created_at: datetime


class ResumeImportRead(ResumeSchema):
    id: UUID
    profile_id: UUID
    filename: str
    mime_type: str
    checksum: str
    parser_version: str
    parsing_status: str
    warnings: list[str]
    created_at: datetime
    updated_at: datetime


class ResumeImportDetail(ResumeImportRead):
    raw_text: str
    facts: list[ParsedFactRead] = Field(default_factory=list)


class ParsedFactUpdate(ResumeSchema):
    payload: dict[str, Any] | None = None
    approved: bool | None = None
    rejected: bool | None = None

    @model_validator(mode="after")
    def validate_decision(self) -> "ParsedFactUpdate":
        if self.approved is True and self.rejected is True:
            raise ValueError("a fact cannot be approved and rejected")
        return self


class ApproveFactsRequest(ResumeSchema):
    fact_ids: list[UUID] | None = None
