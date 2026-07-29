from careerpilot.core.config import Settings
from careerpilot.services.ai.provider import AIProvider
from careerpilot.services.ai.providers import (
    GeminiProvider,
    OllamaProvider,
    OpenAICompatibleProvider,
)


def create_provider(settings: Settings) -> AIProvider:
    if settings.ai_provider == "ollama":
        return OllamaProvider(
            settings.ai_base_url,
            settings.ai_model,
            settings.ai_embedding_model,
            settings.ai_timeout_seconds,
        )
    if not settings.ai_api_key:
        raise ValueError(f"{settings.ai_provider} requires an API key")
    if settings.ai_provider == "gemini":
        return GeminiProvider(
            settings.ai_api_key,
            settings.ai_model,
            settings.ai_embedding_model,
            settings.ai_timeout_seconds,
        )
    if settings.ai_provider == "openai_compatible":
        return OpenAICompatibleProvider(
            settings.ai_base_url,
            settings.ai_api_key,
            settings.ai_model,
            settings.ai_embedding_model,
            settings.ai_timeout_seconds,
        )
    raise ValueError(f"unsupported AI provider: {settings.ai_provider}")
