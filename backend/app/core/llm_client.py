from typing import Any

from app.config import (
    Settings,
    get_provider_api_key,
    normalize_provider,
    resolve_provider_settings,
)
from app.core.gemini_client import GeminiClient
from app.core.openai_compatible_client import OpenAICompatibleClient


def get_llm_client(settings: Settings) -> Any:
    """Create the configured LLM client."""
    settings = resolve_provider_settings(settings)
    provider = normalize_provider(settings.llm_provider)
    if provider == "gemini":
        return GeminiClient(settings)
    return OpenAICompatibleClient(settings)


def is_llm_configured(settings: Settings, provider: str | None = None) -> bool:
    """Return whether the configured provider has enough settings to run."""
    normalized = normalize_provider(provider or settings.llm_provider)
    resolved = resolve_provider_settings(settings, normalized)
    if normalized == "gemini":
        return bool(get_provider_api_key(settings, normalized))
    return bool(resolved.llm_api_key and resolved.llm_base_url and resolved.llm_model)


def missing_llm_message(settings: Settings, provider: str | None = None) -> str:
    """Human-readable configuration error for the active provider."""
    normalized = normalize_provider(provider or settings.llm_provider)
    if normalized == "gemini":
        return "Gemini API key not configured"
    return f"{normalized} LLM configuration is incomplete"
