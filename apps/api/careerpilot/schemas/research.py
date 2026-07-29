from typing import Any
from typing import Literal as TypingLiteral
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

ExperimentCategory = TypingLiteral[
    "agent-workflow", "model-evaluation", "multimodal", "voice", "prompt", "research-pipeline"
]


class ExperimentCreate(BaseModel):
    slug: str = Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$", max_length=100)
    name: str = Field(min_length=2, max_length=200)
    description: str = Field(default="", max_length=4000)
    hypothesis: str = Field(min_length=5, max_length=4000)
    category: ExperimentCategory
    feature_flag: str = Field(pattern=r"^research\.[a-z0-9_.-]+$", max_length=120)
    config: dict[str, Any] = Field(default_factory=dict)
    success_criteria: dict[str, Any] = Field(default_factory=dict)


class ExperimentRead(ExperimentCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    status: str
    enabled: bool
    production_safe: bool


class ExperimentStateUpdate(BaseModel):
    enabled: bool | None = None
    status: TypingLiteral["draft", "active", "paused", "completed", "archived"] | None = None


class DatasetCreate(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    version: str = Field(default="1.0", max_length=40)
    description: str = Field(default="", max_length=4000)
    modality: TypingLiteral["text", "image", "audio", "multimodal"] = "text"
    item_count: int = Field(default=0, ge=0)
    schema_definition: dict[str, Any] = Field(default_factory=dict)
    provenance: dict[str, Any] = Field(default_factory=dict)
    contains_sensitive_data: bool = False


class ExperimentRunCreate(BaseModel):
    dataset_id: UUID | None = None
    model_provider: str = Field(min_length=1, max_length=80)
    model_name: str = Field(min_length=1, max_length=160)
    parameters: dict[str, Any] = Field(default_factory=dict)
    metrics: dict[str, float] = Field(default_factory=dict)
    safety_results: dict[str, Any] = Field(default_factory=dict)
    latency_ms: float | None = Field(default=None, ge=0)
    notes: str = Field(default="", max_length=4000)


class FeatureCreate(BaseModel):
    key: str = Field(pattern=r"^incubator\.[a-z0-9_.-]+$", max_length=120)
    name: str = Field(min_length=2, max_length=200)
    description: str = Field(default="", max_length=4000)
    experiment_id: UUID | None = None


class PromotionRequest(BaseModel):
    target_stage: TypingLiteral["prototype", "validated", "production"]
    rollout_percentage: int = Field(default=0, ge=0, le=100)
