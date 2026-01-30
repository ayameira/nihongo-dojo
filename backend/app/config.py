from pydantic_settings import BaseSettings
from functools import lru_cache
import os


class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite+aiosqlite:///./nihongo_dojo.db"

    # Gemini API
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3-flash-preview"

    # Paths
    class_notes_path: str = "./CLASS_NOTES.md"
    student_record_path: str = "./STUDENT_RECORD.md"
    anki_collection_path: str = ""
    ai_logs_path: str = "./logs/ai_interactions"

    # Cost tracking
    cost_limit_weekly: float = 10.0
    gemini_input_cost_per_1m: float = 0.50
    gemini_output_cost_per_1m: float = 3.00

    # Notes
    notes_token_limit: int = 1000

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
