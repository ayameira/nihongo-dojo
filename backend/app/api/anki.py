"""Anki setup wizard API.

Lets users register any number of Anki deck sources, each pointing at its own
collection file with its own field mapping, and sync them into the vocabulary
database.
"""
import os
import logging
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, func, delete

from app.db.database import get_session
from app.db.models import AnkiDeckConfig, VocabEntry
from app.services import anki_introspect
from app.services.anki_importer import import_deck_config, sync_all_decks

logger = logging.getLogger(__name__)
router = APIRouter()


# --- Schemas --------------------------------------------------------------

class DeckConfigBase(BaseModel):
    name: str
    collection_path: str
    deck_name: str
    enabled: bool = True
    kanji_field: Optional[str] = None
    kana_field: str
    meaning_field: str
    pos_field: Optional[str] = None
    filter_field: Optional[str] = None
    filter_value: Optional[str] = None


class DeckConfigCreate(DeckConfigBase):
    pass


class DeckConfigUpdate(BaseModel):
    name: Optional[str] = None
    collection_path: Optional[str] = None
    deck_name: Optional[str] = None
    enabled: Optional[bool] = None
    kanji_field: Optional[str] = None
    kana_field: Optional[str] = None
    meaning_field: Optional[str] = None
    pos_field: Optional[str] = None
    filter_field: Optional[str] = None
    filter_value: Optional[str] = None


class DeckConfigResponse(DeckConfigBase):
    id: int
    last_synced_at: Optional[str] = None
    vocab_count: int = 0

    class Config:
        from_attributes = True


# --- Collection introspection (no DB writes) ------------------------------

@router.get("/default-path")
def get_default_path():
    """Best-guess Anki collection path for this machine."""
    path = anki_introspect.default_collection_path()
    return {"path": path, "exists": os.path.exists(path)}


@router.get("/decks")
def list_decks(path: str = Query(..., description="Path to a collection.anki2 file")):
    """List decks (with note counts) found in the given collection."""
    try:
        decks = anki_introspect.list_decks(path)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to read Anki collection {path}: {e}")
        raise HTTPException(status_code=400, detail=f"Could not read collection: {e}")
    return {"path": path, "decks": decks}


@router.get("/deck-fields")
def get_deck_fields(
    path: str = Query(...),
    deck: str = Query(...),
):
    """Inspect a deck's note types, fields, sample values and a suggested mapping."""
    try:
        return anki_introspect.get_deck_fields(path, deck)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to inspect deck '{deck}' in {path}: {e}")
        raise HTTPException(status_code=400, detail=f"Could not inspect deck: {e}")


# --- Deck source CRUD -----------------------------------------------------

async def _serialize(config: AnkiDeckConfig, session) -> dict:
    count = await session.scalar(
        select(func.count(VocabEntry.id)).where(VocabEntry.deck_config_id == config.id)
    )
    return {
        "id": config.id,
        "name": config.name,
        "collection_path": config.collection_path,
        "deck_name": config.deck_name,
        "enabled": config.enabled,
        "kanji_field": config.kanji_field,
        "kana_field": config.kana_field,
        "meaning_field": config.meaning_field,
        "pos_field": config.pos_field,
        "filter_field": config.filter_field,
        "filter_value": config.filter_value,
        "last_synced_at": config.last_synced_at.isoformat() if config.last_synced_at else None,
        "vocab_count": count or 0,
    }


@router.get("/configs")
async def list_configs(session=Depends(get_session)):
    """List all configured Anki deck sources."""
    configs = (await session.execute(select(AnkiDeckConfig))).scalars().all()
    return [await _serialize(c, session) for c in configs]


@router.post("/configs")
async def create_config(payload: DeckConfigCreate, session=Depends(get_session)):
    """Register a new Anki deck source."""
    config = AnkiDeckConfig(**payload.model_dump())
    session.add(config)
    await session.commit()
    await session.refresh(config)
    return await _serialize(config, session)


@router.put("/configs/{config_id}")
async def update_config(config_id: int, payload: DeckConfigUpdate, session=Depends(get_session)):
    """Update an existing Anki deck source."""
    config = await session.get(AnkiDeckConfig, config_id)
    if not config:
        raise HTTPException(status_code=404, detail="Deck source not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(config, key, value)
    await session.commit()
    await session.refresh(config)
    return await _serialize(config, session)


@router.delete("/configs/{config_id}")
async def delete_config(
    config_id: int,
    delete_vocab: bool = Query(True, description="Also remove vocab imported from this source"),
    session=Depends(get_session),
):
    """Remove an Anki deck source, optionally deleting the vocab it imported."""
    config = await session.get(AnkiDeckConfig, config_id)
    if not config:
        raise HTTPException(status_code=404, detail="Deck source not found")

    removed = 0
    if delete_vocab:
        result = await session.execute(
            delete(VocabEntry).where(VocabEntry.deck_config_id == config_id)
        )
        removed = result.rowcount or 0
    else:
        # Keep the vocab but detach it from the deleted source.
        for entry in (await session.execute(
            select(VocabEntry).where(VocabEntry.deck_config_id == config_id)
        )).scalars():
            entry.deck_config_id = None

    await session.delete(config)
    await session.commit()
    return {"deleted": True, "vocab_removed": removed}


# --- Syncing --------------------------------------------------------------

@router.post("/configs/{config_id}/sync")
async def sync_config(config_id: int, session=Depends(get_session)):
    """Sync a single Anki deck source."""
    config = await session.get(AnkiDeckConfig, config_id)
    if not config:
        raise HTTPException(status_code=404, detail="Deck source not found")
    try:
        result = await import_deck_config(config, session)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Sync failed for deck source {config_id}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    return {"name": config.name, **result}


@router.post("/sync")
async def sync_all(session=Depends(get_session)):
    """Sync every enabled Anki deck source."""
    results = await sync_all_decks(session)
    totals = {
        "imported": sum(r.get("imported", 0) for r in results),
        "updated": sum(r.get("updated", 0) for r in results),
        "skipped": sum(r.get("skipped", 0) for r in results),
    }
    return {"results": results, "totals": totals}
