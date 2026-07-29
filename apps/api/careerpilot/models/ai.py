from typing import Any
from uuid import UUID

from sqlalchemy import JSON, Float, ForeignKey, LargeBinary, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from careerpilot.db.base import Base
from careerpilot.models.profile import CareerProfile, EntityMixin


class AISettings(EntityMixin, Base):
    __tablename__ = "ai_settings"

    provider: Mapped[str] = mapped_column(String(32), default="ollama")
    model: Mapped[str] = mapped_column(String(128), default="qwen3:8b")
    embedding_model: Mapped[str] = mapped_column(String(128), default="nomic-embed-text")
    base_url: Mapped[str] = mapped_column(String(2048), default="http://localhost:11434")
    temperature: Mapped[float] = mapped_column(Float, default=0.1)
    max_tokens: Mapped[int] = mapped_column(default=2048)


class AISuggestion(EntityMixin, Base):
    __tablename__ = "ai_suggestions"

    profile_id: Mapped[UUID] = mapped_column(
        Uuid(native_uuid=False), ForeignKey("career_profiles.id", ondelete="CASCADE"), index=True
    )
    suggestion_type: Mapped[str] = mapped_column(String(64), index=True)
    status: Mapped[str] = mapped_column(String(32), default="pending", index=True)
    source_type: Mapped[str] = mapped_column(String(64))
    source_id: Mapped[str | None] = mapped_column(String(64))
    original: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    proposed: Mapped[dict[str, Any]] = mapped_column(JSON)
    rationale: Mapped[str] = mapped_column(Text)
    confidence: Mapped[float] = mapped_column(Float)
    profile: Mapped[CareerProfile] = relationship()


class ProfileEmbedding(EntityMixin, Base):
    __tablename__ = "profile_embeddings"

    profile_id: Mapped[UUID] = mapped_column(
        Uuid(native_uuid=False), ForeignKey("career_profiles.id", ondelete="CASCADE"), index=True
    )
    entity_type: Mapped[str] = mapped_column(String(64), index=True)
    entity_id: Mapped[str] = mapped_column(String(64), index=True)
    text: Mapped[str] = mapped_column(Text)
    model: Mapped[str] = mapped_column(String(128))
    content_hash: Mapped[str] = mapped_column(String(64), index=True)
    vector: Mapped[bytes] = mapped_column(LargeBinary)
