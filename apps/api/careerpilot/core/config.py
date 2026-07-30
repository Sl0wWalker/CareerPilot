from functools import lru_cache

from pydantic import field_validator, model_validator
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
    cors_origins: list[str] = ["http://localhost:4725"]
    ai_provider: str = "ollama"
    ai_model: str = "qwen3:8b"
    ai_embedding_model: str = "nomic-embed-text"
    ai_base_url: str = "http://localhost:11434"
    ai_api_key: str | None = None
    ai_timeout_seconds: float = 60.0
    app_version: str = "1.0.0"
    secret_key: str = "development-only-change-me"
    auth_enabled: bool = False
    access_token_minutes: int = 60
    rate_limit_requests: int = 120
    rate_limit_window_seconds: int = 60
    backup_directory: str = "./data/backups"
    trusted_hosts: list[str] = ["localhost", "127.0.0.1", "testserver"]
    metrics_enabled: bool = True

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: object) -> object:
        if isinstance(value, str) and not value.startswith("["):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @field_validator("trusted_hosts", mode="before")
    @classmethod
    def parse_trusted_hosts(cls, value: object) -> object:
        if isinstance(value, str) and not value.startswith("["):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @model_validator(mode="after")
    def validate_production_security(self) -> "Settings":
        if self.environment == "production":
            if self.secret_key == "development-only-change-me" or len(self.secret_key) < 32:
                raise ValueError(
                    "Production CAREERPILOT_SECRET_KEY must contain at least 32 characters"
                )
            if not self.auth_enabled:
                raise ValueError("Authentication must be enabled in production")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
