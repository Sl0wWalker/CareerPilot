from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

DEFAULT_WEIGHTS = {
    "skills": 0.25,
    "experience": 0.18,
    "seniority": 0.10,
    "education": 0.08,
    "location": 0.10,
    "work_authorization": 0.12,
    "keywords": 0.07,
    "semantic_similarity": 0.10,
}


class MatchingSettingsUpdate(BaseModel):
    weights: dict[str, float] = Field(default_factory=lambda: DEFAULT_WEIGHTS.copy())
    hard_block_threshold: float = Field(default=0.35, ge=0, le=1)
    minimum_recommendation_score: float = Field(default=65, ge=0, le=100)

    @model_validator(mode="after")
    def validate_weights(self) -> "MatchingSettingsUpdate":
        if set(self.weights) != set(DEFAULT_WEIGHTS):
            raise ValueError("weights must contain every supported matching component")
        if any(value < 0 for value in self.weights.values()):
            raise ValueError("weights cannot be negative")
        if abs(sum(self.weights.values()) - 1.0) > 0.001:
            raise ValueError("weights must sum to 1")
        return self


class MatchingSettingsRead(MatchingSettingsUpdate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID | None = None


class MatchComponent(BaseModel):
    score: float = Field(ge=0, le=100)
    weight: float = Field(ge=0, le=1)
    weighted_score: float = Field(ge=0, le=100)
    confidence: float = Field(ge=0, le=1)
    explanation: str
    matched: list[str] = Field(default_factory=list)
    missing: list[str] = Field(default_factory=list)


class JobMatchRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    job_id: UUID
    profile_id: UUID
    overall_score: float
    confidence: float
    recommendation: Literal["strong_match", "consider", "low_match", "blocked"]
    engine_version: str
    components: dict[str, MatchComponent]
    strengths: list[str]
    gaps: list[str]
    hard_blocks: list[str]
    reasons: list[str]
    evidence: list[dict[str, Any]]
