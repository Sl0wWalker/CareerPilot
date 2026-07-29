import json
import math
from array import array
from hashlib import sha256
from typing import Any
from uuid import UUID

from careerpilot.core.config import Settings
from careerpilot.models import Achievement, AISettings, AISuggestion, ProfileEmbedding, Skill
from careerpilot.repositories import AIRepository, CareerProfileRepository
from careerpilot.schemas import AISettingsUpdate
from careerpilot.services.ai import AIProvider
from careerpilot.services.ai.prompts import render_prompt

SUMMARY_SCHEMA = {
    "type": "object",
    "properties": {
        "short": {"type": "string"},
        "medium": {"type": "string"},
        "linkedin": {"type": "string"},
    },
    "required": ["short", "medium", "linkedin"],
}
ENRICH_SCHEMA = {
    "type": "object",
    "properties": {
        "suggestions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "type": {"type": "string"},
                    "source_type": {"type": "string"},
                    "source_id": {"type": ["string", "null"]},
                    "original": {"type": ["object", "null"]},
                    "proposed": {"type": "object"},
                    "rationale": {"type": "string"},
                    "confidence": {"type": "number"},
                },
                "required": [
                    "type",
                    "source_type",
                    "source_id",
                    "original",
                    "proposed",
                    "rationale",
                    "confidence",
                ],
            },
        }
    },
    "required": ["suggestions"],
}


class AIProfileService:
    def __init__(
        self,
        repository: AIRepository,
        profiles: CareerProfileRepository,
        provider: AIProvider,
        defaults: Settings,
    ) -> None:
        self.repository = repository
        self.profiles = profiles
        self.provider = provider
        self.defaults = defaults

    def profile_context(self) -> str:
        profile = self.profiles.get_required()
        value = {
            "identity": {
                "first_name": profile.first_name,
                "last_name": profile.last_name,
            },
            "skills": [
                {"id": str(item.id), "name": item.name, "years": item.years_experience}
                for item in profile.skills
            ],
            "experiences": [
                {
                    "id": str(item.id),
                    "company": item.company,
                    "title": item.title,
                    "description": item.description,
                }
                for item in profile.experiences
            ],
            "projects": [
                {"id": str(item.id), "name": item.name, "description": item.description}
                for item in profile.projects
            ],
            "achievements": [
                {"id": str(item.id), "title": item.title, "description": item.description}
                for item in profile.achievements
            ],
            "education": [
                {
                    "id": str(item.id),
                    "institution": item.institution,
                    "degree": item.degree,
                }
                for item in profile.education
            ],
        }
        return json.dumps(value, indent=2)

    def summarize(self) -> dict[str, str]:
        value = self.provider.generate_json(
            render_prompt("summarize", self.profile_context()), SUMMARY_SCHEMA
        )
        return {key: str(value[key]) for key in ("short", "medium", "linkedin")}

    def enrich(self) -> list[AISuggestion]:
        profile = self.profiles.get_required()
        result = self.provider.generate_json(
            render_prompt("enrich", self.profile_context()), ENRICH_SCHEMA
        )
        suggestions = [
            AISuggestion(
                profile_id=profile.id,
                suggestion_type=str(item["type"]),
                source_type=str(item["source_type"]),
                source_id=str(item["source_id"]) if item.get("source_id") else None,
                original=item.get("original"),
                proposed=dict(item["proposed"]),
                rationale=str(item["rationale"]),
                confidence=max(0, min(1, float(item["confidence"]))),
            )
            for item in result["suggestions"]
        ]
        return self.repository.add_suggestions(suggestions)

    def update_suggestion(
        self, suggestion_id: UUID, status: str, proposed: dict[str, Any] | None
    ) -> AISuggestion:
        suggestion = self.repository.suggestion(suggestion_id)
        if suggestion is None:
            raise LookupError("AI suggestion not found")
        if proposed is not None:
            suggestion.proposed = proposed
        suggestion.status = status
        if status == "approved":
            self._apply(suggestion)
        return self.repository.save_suggestion(suggestion)

    def _apply(self, suggestion: AISuggestion) -> None:
        profile = self.profiles.get_required()
        if suggestion.suggestion_type in {"add_skill", "normalize_skill"}:
            name = str(suggestion.proposed.get("name", "")).strip()
            if name and all(skill.name.casefold() != name.casefold() for skill in profile.skills):
                profile.skills.append(Skill(name=name))
        elif suggestion.suggestion_type == "extract_achievement":
            title = str(suggestion.proposed.get("title", "")).strip()
            description = str(suggestion.proposed.get("description", title)).strip()
            if title and description:
                profile.achievements.append(Achievement(title=title, description=description))
        self.profiles.save(profile)

    def rebuild_embeddings(self) -> int:
        profile = self.profiles.get_required()
        records = self._searchable_records(profile)
        vectors = self.provider.embed([record[2] for record in records])
        values = [
            ProfileEmbedding(
                profile_id=profile.id,
                entity_type=entity_type,
                entity_id=entity_id,
                text=text,
                model="configured",
                content_hash=sha256(text.encode()).hexdigest(),
                vector=array("f", vector).tobytes(),
            )
            for (entity_type, entity_id, text), vector in zip(records, vectors, strict=True)
        ]
        self.repository.replace_embeddings(profile.id, values)
        return len(values)

    def search(self, query: str, limit: int) -> list[dict[str, Any]]:
        profile = self.profiles.get_required()
        stored = self.repository.embeddings(profile.id)
        if not stored:
            self.rebuild_embeddings()
            stored = self.repository.embeddings(profile.id)
        query_vector = self.provider.embed([query])[0]
        results = [
            {
                "entity_type": item.entity_type,
                "entity_id": item.entity_id,
                "text": item.text,
                "score": self._cosine(query_vector, list(array("f", item.vector))),
            }
            for item in stored
        ]
        return sorted(results, key=lambda item: item["score"], reverse=True)[:limit]

    def get_settings(self) -> AISettings:
        value = self.repository.settings()
        if value is None:
            value = self.repository.save_settings(
                AISettings(
                    provider=self.defaults.ai_provider,
                    model=self.defaults.ai_model,
                    embedding_model=self.defaults.ai_embedding_model,
                    base_url=self.defaults.ai_base_url,
                )
            )
        return value

    def update_settings(self, payload: AISettingsUpdate) -> AISettings:
        value = self.get_settings()
        for field, item in payload.model_dump().items():
            setattr(value, field, item)
        return self.repository.save_settings(value)

    @staticmethod
    def _searchable_records(profile: Any) -> list[tuple[str, str, str]]:
        records = [
            ("skill", str(item.id), item.name)
            for item in profile.skills
        ]
        records.extend(
            (
                "experience",
                str(item.id),
                f"{item.title} at {item.company}. {item.description or ''}".strip(),
            )
            for item in profile.experiences
        )
        records.extend(
            ("project", str(item.id), f"{item.name}. {item.description or ''}".strip())
            for item in profile.projects
        )
        records.extend(
            ("achievement", str(item.id), f"{item.title}. {item.description}".strip())
            for item in profile.achievements
        )
        return records

    @staticmethod
    def _cosine(left: list[float], right: list[float]) -> float:
        if len(left) != len(right) or not left:
            return 0
        denominator = math.sqrt(sum(x * x for x in left)) * math.sqrt(
            sum(x * x for x in right)
        )
        numerator = sum(x * y for x, y in zip(left, right, strict=True))
        return numerator / denominator if denominator else 0
