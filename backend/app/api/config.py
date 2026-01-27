"""Configuration API endpoints."""
import os
import json
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

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
