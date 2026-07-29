from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from careerpilot.models import AISettings, AISuggestion, ProfileEmbedding


class AIRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def settings(self) -> AISettings | None:
        return self.session.scalar(select(AISettings))

    def save_settings(self, value: AISettings) -> AISettings:
        self.session.add(value)
        self.session.commit()
        self.session.refresh(value)
        return value

    def add_suggestions(self, values: list[AISuggestion]) -> list[AISuggestion]:
        self.session.add_all(values)
        self.session.commit()
        return values

    def suggestions(self) -> list[AISuggestion]:
        return list(
            self.session.scalars(
                select(AISuggestion).order_by(AISuggestion.created_at.desc())
            )
        )

    def suggestion(self, suggestion_id: UUID) -> AISuggestion | None:
        return self.session.get(AISuggestion, suggestion_id)

    def save_suggestion(self, value: AISuggestion) -> AISuggestion:
        self.session.add(value)
        self.session.commit()
        self.session.refresh(value)
        return value

    def embeddings(self, profile_id: UUID) -> list[ProfileEmbedding]:
        return list(
            self.session.scalars(
                select(ProfileEmbedding).where(ProfileEmbedding.profile_id == profile_id)
            )
        )

    def replace_embeddings(
        self, profile_id: UUID, values: list[ProfileEmbedding]
    ) -> list[ProfileEmbedding]:
        for existing in self.embeddings(profile_id):
            self.session.delete(existing)
        self.session.add_all(values)
        self.session.commit()
        return values
