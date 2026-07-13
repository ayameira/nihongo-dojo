from pydantic_settings import BaseSettings
from pydantic import model_validator
from functools import lru_cache
from typing import Dict, Any


# =============================================================================
# MODEL REGISTRY
# =============================================================================
# Add new models here. Set LLM_PROVIDER/LLM_MODEL in .env to switch providers.
#
# Pricing sources:
# - Gemini: https://ai.google.dev/gemini-api/docs/pricing
# - Groq: https://console.groq.com/docs/models
# =============================================================================

GEMINI_MODELS: Dict[str, Dict[str, Any]] = {
    # Gemini 3 Flash - Fast and cost-effective
    "gemini-3-flash-preview": {
        "name": "Gemini 3 Flash Preview",
        "input_cost_per_1m": 0.50,
        "output_cost_per_1m": 3.00,
    },
    # Gemini 3 Pro - Most capable
    "gemini-3-pro-preview": {
        "name": "Gemini 3 Pro Preview",
        "input_cost_per_1m": 2.00,
        "output_cost_per_1m": 12.00,
    },
}

GROQ_MODELS: Dict[str, Dict[str, Any]] = {
    "llama-3.1-8b-instant": {
        "name": "Groq Llama 3.1 8B Instant",
        "input_cost_per_1m": 0.05,
        "output_cost_per_1m": 0.08,
    },
    "llama-3.3-70b-versatile": {
        "name": "Groq Llama 3.3 70B Versatile",
        "input_cost_per_1m": 0.59,
        "output_cost_per_1m": 0.79,
    },
}

OPENROUTER_MODELS: Dict[str, Dict[str, Any]] = {
    "openrouter/free": {
        "name": "OpenRouter Free Router",
        "input_cost_per_1m": 0.0,
        "output_cost_per_1m": 0.0,
    },
}

MODEL_REGISTRY: Dict[str, Dict[str, Dict[str, Any]]] = {
    "gemini": GEMINI_MODELS,
    "groq": GROQ_MODELS,
    "openrouter": OPENROUTER_MODELS,
}

DEFAULT_MODELS: Dict[str, str] = {
    "gemini": "gemini-3-flash-preview",
    "groq": "llama-3.1-8b-instant",
    "openrouter": "openrouter/free",
}

DEFAULT_BASE_URLS: Dict[str, str] = {
    "groq": "https://api.groq.com/openai/v1",
    "openrouter": "https://openrouter.ai/api/v1",
}

DEFAULT_PROVIDER = "gemini"
DEFAULT_MODEL = DEFAULT_MODELS[DEFAULT_PROVIDER]


def normalize_provider(provider: str | None) -> str:
    """Normalize configured provider names used by the LLM factory."""
    normalized = (provider or DEFAULT_PROVIDER).strip().lower()
    if normalized in {"openai-compatible", "openai_compatible", "custom"}:
        return "openai_compatible"
    if normalized not in {"gemini", "groq", "openrouter", "openai_compatible"}:
        return DEFAULT_PROVIDER
    return normalized


class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite+aiosqlite:///./nihongo_dojo.db"

    # Gemini API
    gemini_api_key: str = ""
    gemini_model: str = DEFAULT_MODEL

    # Provider-neutral LLM configuration.
    #
    # Backwards compatibility: if LLM_PROVIDER is left as "gemini", existing
    # GEMINI_API_KEY/GEMINI_MODEL values are used automatically.
    llm_provider: str = DEFAULT_PROVIDER
    llm_api_key: str = ""
    llm_base_url: str = ""
    llm_model: str = ""

    # Optional provider-specific keys let the UI switch between providers
    # without rewriting LLM_PROVIDER.
    groq_api_key: str = ""
    openrouter_api_key: str = ""

    # Paths
    anki_collection_path: str = ""
    ai_logs_path: str = "./logs/ai_interactions"

    # Target language profile. Japanese is the default profile and preserves
    # the app's existing behavior.
    target_language_code: str = "ja"

    # TTS servers: VOICEVOX speaks Japanese, Kokoro-FastAPI speaks
    # English and French. Both are optional user-run local servers.
    voicevox_url: str = "http://127.0.0.1:50021"
    kokoro_url: str = "http://127.0.0.1:8880"
    tts_cache_dir: str = "./audio_cache"
    default_speaker_id: int = 2  # VOICEVOX: Shikoku Metan - Normal Style

    # Cost tracking (auto-set from model, but can be overridden)
    cost_limit_weekly: float = 10.0
    gemini_input_cost_per_1m: float | None = None
    gemini_output_cost_per_1m: float | None = None
    llm_input_cost_per_1m: float | None = None
    llm_output_cost_per_1m: float | None = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

    @model_validator(mode="after")
    def set_model_pricing(self) -> "Settings":
        """Resolve provider defaults and auto-set model pricing."""
        self.llm_provider = normalize_provider(self.llm_provider)

        if self.llm_provider == "gemini":
            if not self.llm_api_key:
                self.llm_api_key = self.gemini_api_key
            if not self.llm_model:
                self.llm_model = self.gemini_model
            self.gemini_model = self.llm_model
        else:
            if not self.llm_model:
                self.llm_model = DEFAULT_MODELS.get(self.llm_provider, "")
            if not self.llm_base_url:
                self.llm_base_url = DEFAULT_BASE_URLS.get(self.llm_provider, "")

        model_config = get_available_models(self.llm_provider).get(self.llm_model)
        if not model_config and self.llm_provider == "gemini":
            model_config = GEMINI_MODELS.get(self.gemini_model)

        if model_config:
            input_cost = model_config["input_cost_per_1m"]
            output_cost = model_config["output_cost_per_1m"]
        else:
            input_cost = 0.0
            output_cost = 0.0

        if self.llm_input_cost_per_1m is None:
            self.llm_input_cost_per_1m = (
                self.gemini_input_cost_per_1m
                if self.llm_provider == "gemini" and self.gemini_input_cost_per_1m is not None
                else input_cost
            )
        if self.llm_output_cost_per_1m is None:
            self.llm_output_cost_per_1m = (
                self.gemini_output_cost_per_1m
                if self.llm_provider == "gemini" and self.gemini_output_cost_per_1m is not None
                else output_cost
            )

        # Preserve the older Gemini-specific settings for existing code/tests.
        if self.gemini_input_cost_per_1m is None:
            self.gemini_input_cost_per_1m = (
                self.llm_input_cost_per_1m
                if self.llm_provider == "gemini"
                else GEMINI_MODELS.get(self.gemini_model, {}).get("input_cost_per_1m", 0.50)
            )
        if self.gemini_output_cost_per_1m is None:
            self.gemini_output_cost_per_1m = (
                self.llm_output_cost_per_1m
                if self.llm_provider == "gemini"
                else GEMINI_MODELS.get(self.gemini_model, {}).get("output_cost_per_1m", 3.00)
            )

        return self


@lru_cache()
def get_settings() -> Settings:
    return Settings()


def get_available_models(provider: str | None = None) -> Dict[str, Dict[str, Any]]:
    """Return available models for a provider."""
    return MODEL_REGISTRY.get(normalize_provider(provider), {})


def get_provider_api_key(settings: Settings, provider: str | None = None) -> str:
    """Return the best API key for a provider."""
    normalized = normalize_provider(provider or settings.llm_provider)
    if normalized == "gemini":
        return settings.gemini_api_key or (
            settings.llm_api_key if settings.llm_provider == "gemini" else ""
        )
    if normalized == "groq":
        return settings.groq_api_key or (
            settings.llm_api_key if settings.llm_provider == "groq" else ""
        )
    if normalized == "openrouter":
        return settings.openrouter_api_key or (
            settings.llm_api_key if settings.llm_provider == "openrouter" else ""
        )
    return settings.llm_api_key


def get_provider_base_url(settings: Settings, provider: str | None = None) -> str:
    """Return the base URL for a provider."""
    normalized = normalize_provider(provider or settings.llm_provider)
    if normalized == "gemini":
        return ""
    if normalized == settings.llm_provider and settings.llm_base_url:
        return settings.llm_base_url
    return DEFAULT_BASE_URLS.get(normalized, settings.llm_base_url)


def get_provider_default_model(settings: Settings, provider: str | None = None) -> str:
    """Return the configured or default model for a provider."""
    normalized = normalize_provider(provider or settings.llm_provider)
    if normalized == settings.llm_provider and settings.llm_model:
        return settings.llm_model
    if normalized == "gemini":
        return settings.gemini_model or DEFAULT_MODELS["gemini"]
    return DEFAULT_MODELS.get(normalized, "")


def resolve_provider_settings(
    settings: Settings,
    provider: str | None = None,
    model_name: str | None = None,
) -> Settings:
    """Return a copy of settings resolved for one provider/model request."""
    normalized = normalize_provider(provider or settings.llm_provider)
    resolved = settings.model_copy()
    resolved.llm_provider = normalized
    resolved.llm_api_key = get_provider_api_key(settings, normalized)
    resolved.llm_base_url = get_provider_base_url(settings, normalized)
    resolved.llm_model = model_name or get_provider_default_model(settings, normalized)

    if normalized == "gemini":
        resolved.gemini_model = resolved.llm_model

    model_config = get_available_models(normalized).get(resolved.llm_model, {})
    resolved.llm_input_cost_per_1m = model_config.get(
        "input_cost_per_1m", settings.llm_input_cost_per_1m or 0.0
    )
    resolved.llm_output_cost_per_1m = model_config.get(
        "output_cost_per_1m", settings.llm_output_cost_per_1m or 0.0
    )
    return resolved


def get_model_pricing(model_name: str, settings: Settings | None = None) -> tuple[float, float]:
    """Return input/output costs for a model.

    Per-request chat model switches should use the registry pricing without
    mutating the global settings object that background agents rely on.
    """
    if settings and model_name == settings.llm_model:
        return (
            settings.llm_input_cost_per_1m or 0.0,
            settings.llm_output_cost_per_1m or 0.0,
        )

    if settings:
        model_config = get_available_models(settings.llm_provider).get(model_name)
    else:
        model_config = None

    if not model_config:
        for provider_models in MODEL_REGISTRY.values():
            if model_name in provider_models:
                model_config = provider_models[model_name]
                break

    if model_config:
        return (
            model_config["input_cost_per_1m"],
            model_config["output_cost_per_1m"],
        )

    return 0.0, 0.0
