"""Configuration API endpoints."""
import os
import json
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.config import (
    MODEL_REGISTRY,
    get_provider_default_model,
    get_settings,
)
from app.core.language_profiles import list_language_profiles, get_language_profile
from app.core.llm_client import is_llm_configured

router = APIRouter()

CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config.json")
DEFAULT_ANKI_PATH = "~/Library/Application Support/Anki2/User 1/collection.anki2"


def load_config() -> dict:
    """Load config from file."""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {"anki_path": DEFAULT_ANKI_PATH}


def save_config(config: dict):
    """Save config to file."""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)


class AnkiPathUpdate(BaseModel):
    path: str


@router.get("/models")
async def get_models():
    """Get available chat models and the configured default."""
    settings = get_settings()
    models = []

    for provider, provider_models in MODEL_REGISTRY.items():
        configured = is_llm_configured(settings, provider)
        for model_id, model_config in provider_models.items():
            models.append({
                "id": model_id,
                "provider": provider,
                "key": f"{provider}:{model_id}",
                "name": model_config["name"],
                "provider_name": provider.title(),
                "configured": configured,
                "input_cost_per_1m": model_config["input_cost_per_1m"],
                "output_cost_per_1m": model_config["output_cost_per_1m"],
            })

    return {
        "provider": settings.llm_provider,
        "current_model": settings.llm_model,
        "current_key": f"{settings.llm_provider}:{settings.llm_model}",
        "providers": [
            {
                "id": provider,
                "name": provider.title(),
                "configured": is_llm_configured(settings, provider),
                "current_model": get_provider_default_model(settings, provider),
            }
            for provider in MODEL_REGISTRY
        ],
        "models": models,
    }


@router.get("/languages")
async def get_languages():
    """Return available target-language profiles."""
    settings = get_settings()
    active = get_language_profile(settings.target_language_code)
    profiles = []
    for profile in list_language_profiles():
        profiles.append({
            "code": profile.code,
            "display_name": profile.display_name,
            "native_name": profile.native_name,
            "speech_language": profile.speech_language,
            "supports_server_tts": profile.supports_server_tts,
            "has_secondary_script": profile.has_secondary_script,
            "grammar_level_scheme": {
                "name": profile.grammar_level_scheme.name,
                "levels": profile.grammar_level_scheme.levels,
                "source_name": profile.grammar_level_scheme.source_name,
                "custom_label": profile.grammar_level_scheme.custom_label,
            },
            "vocabulary_semantics": {
                "term_label": profile.vocabulary_semantics.term_label,
                "reading_label": profile.vocabulary_semantics.reading_label,
                "meaning_label": profile.vocabulary_semantics.meaning_label,
                "part_of_speech_label": profile.vocabulary_semantics.part_of_speech_label,
            },
        })

    return {
        "active_language_code": active.code,
        "profiles": profiles,
    }


@router.get("/anki-path")
async def get_anki_path():
    """Get the current Anki collection path."""
    config = load_config()
    path = config.get("anki_path", DEFAULT_ANKI_PATH)
    expanded = os.path.expanduser(path)
    exists = os.path.exists(expanded)
    return {
        "path": path,
        "expanded": expanded,
        "exists": exists
    }


@router.put("/anki-path")
async def set_anki_path(update: AnkiPathUpdate):
    """Set a new Anki collection path."""
    path = update.path.strip()
    if not path:
        raise HTTPException(status_code=400, detail="Path cannot be empty")

    expanded = os.path.expanduser(path)
    exists = os.path.exists(expanded)

    config = load_config()
    config["anki_path"] = path
    save_config(config)

    return {
        "path": path,
        "expanded": expanded,
        "exists": exists,
        "message": "Path updated" + ("" if exists else " (warning: file not found)")
    }


@router.post("/sync-anki")
async def sync_anki():
    """Trigger a manual Anki sync."""
    from app.services.anki_sync import export_anki_to_db
    from app.services.anki_importer import import_from_export_db
    from app.db.database import get_session

    try:
        export_path = export_anki_to_db()
        if not export_path:
            raise HTTPException(status_code=400, detail="Failed to export Anki collection")

        async for session in get_session():
            result = await import_from_export_db(export_path, session)
            return {
                "success": True,
                "imported": result["imported"],
                "updated": result["updated"],
                "skipped": result["skipped"],
                "total": result["total_processed"]
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
