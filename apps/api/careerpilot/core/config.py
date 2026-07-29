from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../../.env"),
        env_prefix="CAREERPILOT_",
        extra="ignore",
    )

    app_name: str = "CareerPilot API"
    environment: str = "development"
    log_level: str = "INFO"
    database_url: str = "sqlite:///./data/careerpilot.db"
    cors_origins: list[str] = ["http://localhost:5173"]
    ai_provider: str = "ollama"
    ai_model: str = "qwen3:8b"
    ai_embedding_model: str = "nomic-embed-text"
    ai_base_url: str = "http://localhost:11434"
    ai_api_key: str | None = None
    ai_timeout_seconds: float = 60.0

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: object) -> object:
        if isinstance(value, str) and not value.startswith("["):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()

