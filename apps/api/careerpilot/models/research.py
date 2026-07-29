from typing import Any

from sqlalchemy import JSON, Boolean, Float, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from careerpilot.db.base import Base
from careerpilot.models.profile import EntityMixin


class ResearchExperiment(EntityMixin, Base):
    __tablename__ = "research_experiments"
    __table_args__ = (UniqueConstraint("owner_id", "slug"),)

    owner_id: Mapped[str] = mapped_column(String(160), index=True)
    slug: Mapped[str] = mapped_column(String(100))
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    hypothesis: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(50), index=True)
    status: Mapped[str] = mapped_column(String(30), default="draft", index=True)
    feature_flag: Mapped[str] = mapped_column(String(120))
    enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    production_safe: Mapped[bool] = mapped_column(Boolean, default=False)
    config: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    success_criteria: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)


class EvaluationDataset(EntityMixin, Base):
    __tablename__ = "research_evaluation_datasets"
    __table_args__ = (UniqueConstraint("owner_id", "name", "version"),)

    owner_id: Mapped[str] = mapped_column(String(160), index=True)
    name: Mapped[str] = mapped_column(String(160))
    version: Mapped[str] = mapped_column(String(40), default="1.0")
    description: Mapped[str] = mapped_column(Text, default="")
    modality: Mapped[str] = mapped_column(String(40), default="text")
    item_count: Mapped[int] = mapped_column(default=0)
    schema_definition: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    provenance: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    contains_sensitive_data: Mapped[bool] = mapped_column(Boolean, default=False)


class ExperimentRun(EntityMixin, Base):
    __tablename__ = "research_experiment_runs"

    owner_id: Mapped[str] = mapped_column(String(160), index=True)
    experiment_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("research_experiments.id", ondelete="CASCADE"), index=True
    )
    dataset_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("research_evaluation_datasets.id", ondelete="SET NULL"),
        index=True,
    )
    model_provider: Mapped[str] = mapped_column(String(80))
    model_name: Mapped[str] = mapped_column(String(160))
    status: Mapped[str] = mapped_column(String(30), default="queued", index=True)
    parameters: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    metrics: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    safety_results: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    latency_ms: Mapped[float | None] = mapped_column(Float)
    cost_estimate: Mapped[float] = mapped_column(Float, default=0.0)
    notes: Mapped[str] = mapped_column(Text, default="")


class IncubatedFeature(EntityMixin, Base):
    __tablename__ = "research_incubated_features"
    __table_args__ = (UniqueConstraint("owner_id", "key"),)

    owner_id: Mapped[str] = mapped_column(String(160), index=True)
    key: Mapped[str] = mapped_column(String(120))
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    stage: Mapped[str] = mapped_column(String(30), default="idea", index=True)
    experiment_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("research_experiments.id", ondelete="SET NULL")
    )
    rollout_percentage: Mapped[int] = mapped_column(default=0)
    safety_approved: Mapped[bool] = mapped_column(Boolean, default=False)
    promotion_evidence: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
