from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.services.notes_service import NotesService
from app.config import get_settings

router = APIRouter()
notes_service = NotesService()


class NotesUpdate(BaseModel):
    content: str


class SectionUpdate(BaseModel):
    action: str  # 'append' | 'replace'
    content: str


@router.get("")
async def get_notes():
    settings = get_settings()
    content = await notes_service.read_notes(settings.class_notes_path)
    return {"content": content}


@router.get("/{section}")
async def get_section(section: str):
    settings = get_settings()
    valid_sections = ["current_focus", "recent_corrections", "recent_vocab"]
    if section not in valid_sections:
        raise HTTPException(status_code=400, detail=f"Invalid section. Must be one of: {valid_sections}")

    content = await notes_service.read_section(settings.class_notes_path, section)
    return {"section": section, "content": content}


@router.put("")
async def update_notes(data: NotesUpdate):
    settings = get_settings()
    await notes_service.write_notes(settings.class_notes_path, data.content)
    return {"message": "Notes updated successfully"}


@router.put("/{section}")
async def update_section(section: str, data: SectionUpdate):
    settings = get_settings()
    valid_sections = ["current_focus", "recent_corrections", "recent_vocab"]
    if section not in valid_sections:
        raise HTTPException(status_code=400, detail=f"Invalid section. Must be one of: {valid_sections}")

    if data.action not in ["append", "replace"]:
        raise HTTPException(status_code=400, detail="Action must be 'append' or 'replace'")

    await notes_service.update_section(
        settings.class_notes_path,
        section,
        data.content,
        data.action
    )
    return {"message": f"Section '{section}' updated successfully"}


@router.post("/archive")
async def archive_notes():
    settings = get_settings()
    archived = await notes_service.archive_old_notes(
        settings.class_notes_path,
        settings.notes_token_limit
    )
    return {"archived": archived}


@router.get("/token-count")
async def get_token_count():
    settings = get_settings()
    count = await notes_service.get_token_count(settings.class_notes_path)
    return {"token_count": count}
