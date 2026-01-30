from pydantic_settings import BaseSettings
from pydantic import model_validator
from functools import lru_cache
from typing import Dict, Any
import os


# =============================================================================
# MODEL REGISTRY
# =============================================================================
# Add new models here. Just set GEMINI_MODEL in .env to switch.
#
# Pricing source: https://ai.google.dev/gemini-api/docs/pricing
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

# Default model
DEFAULT_MODEL = "gemini-3-flash-preview"


class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite+aiosqlite:///./nihongo_dojo.db"

    # Gemini API
    gemini_api_key: str = ""
    gemini_model: str = DEFAULT_MODEL

    # Paths
    student_record_path: str = "./STUDENT_RECORD.md"
    anki_collection_path: str = ""
    ai_logs_path: str = "./logs/ai_interactions"

    # Cost tracking (auto-set from model, but can be overridden)
    cost_limit_weekly: float = 10.0
    gemini_input_cost_per_1m: float | None = None
    gemini_output_cost_per_1m: float | None = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

    @model_validator(mode="after")
    def set_model_pricing(self) -> "Settings":
        """Auto-set pricing based on selected model if not explicitly set."""
        model_config = GEMINI_MODELS.get(self.gemini_model)

        if model_config:
            if self.gemini_input_cost_per_1m is None:
                self.gemini_input_cost_per_1m = model_config["input_cost_per_1m"]
            if self.gemini_output_cost_per_1m is None:
                self.gemini_output_cost_per_1m = model_config["output_cost_per_1m"]
        else:
            # Unknown model - use defaults if not set
            if self.gemini_input_cost_per_1m is None:
                self.gemini_input_cost_per_1m = 0.50
            if self.gemini_output_cost_per_1m is None:
                self.gemini_output_cost_per_1m = 3.00

        return self


@lru_cache()
def get_settings() -> Settings:
    return Settings()


def get_available_models() -> Dict[str, Dict[str, Any]]:
    """Return all available models with their pricing."""
    return GEMINI_MODELS
