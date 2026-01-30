from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.notes_service import NotesService
from app.config import get_settings

router = APIRouter()
notes_service = NotesService()


class NotesUpdate(BaseModel):
    content: str


class SectionUpdate(BaseModel):
    action: str  # 'append' | 'replace'
    content: str


# Valid sections for student record
VALID_SECTIONS = ["goals", "background", "interests", "preferences", "notes"]


@router.get("")
async def get_notes():
    """Get the full student record content."""
    settings = get_settings()
    content = await notes_service.read_notes(settings.student_record_path)
    return {"content": content}


@router.get("/token-count")
async def get_token_count():
    """Get the token count of the student record."""
    settings = get_settings()
    content = await notes_service.read_notes(settings.student_record_path)
    # Simple estimation: ~4 characters per token
    count = len(content) // 4 if content else 0
    return {"token_count": count}


@router.get("/{section}")
async def get_section(section: str):
    """Get a specific section of the student record."""
    settings = get_settings()
    if section not in VALID_SECTIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid section. Must be one of: {VALID_SECTIONS}"
        )

    content = await notes_service.read_student_record_section(
        settings.student_record_path, section
    )
    return {"section": section, "content": content}


@router.put("")
async def update_notes(data: NotesUpdate):
    """Update the full student record content."""
    settings = get_settings()
    await notes_service.write_notes(settings.student_record_path, data.content)
    return {"message": "Student record updated successfully"}


@router.put("/{section}")
async def update_section(section: str, data: SectionUpdate):
    """Update a specific section of the student record."""
    settings = get_settings()
    if section not in VALID_SECTIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid section. Must be one of: {VALID_SECTIONS}"
        )

    if data.action not in ["append", "replace"]:
        raise HTTPException(status_code=400, detail="Action must be 'append' or 'replace'")

    await notes_service.update_student_record_section(
        settings.student_record_path,
        section,
        data.content,
        data.action
    )
    return {"message": f"Section '{section}' updated successfully"}
