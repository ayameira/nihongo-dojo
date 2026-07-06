"""Grammar API router - CRUD for grammar entries."""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy import select, func, and_
from datetime import datetime

from app.db.database import get_session
from app.db.models import GrammarEntry
from app.config import get_settings
from app.core.language_profiles import get_language_profile, normalize_language_code

router = APIRouter()


class GrammarCreate(BaseModel):
    pattern: str
    meaning: str
    jlpt_level: Optional[str] = None
    notes: Optional[str] = None
    language_code: Optional[str] = None


class GrammarUpdate(BaseModel):
    pattern: Optional[str] = None
    meaning: Optional[str] = None
    jlpt_level: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class GrammarStatusUpdate(BaseModel):
    status: str


class GrammarResponse(BaseModel):
    id: int
    language_code: str
    pattern: str
    meaning: str
    jlpt_level: Optional[str]
    status: str
    source: str
    notes: Optional[str]
    times_seen: int
    times_correct: int
    last_assessed_at: Optional[datetime]
    last_seen_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


@router.get("")
async def list_grammar(
    status: Optional[str] = None,
    jlpt_level: Optional[str] = None,
    source: Optional[str] = None,
    search: Optional[str] = None,
    language_code: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=1000),
    session=Depends(get_session)
):
    """List grammar entries with filtering and pagination."""
    language_code = normalize_language_code(language_code or get_settings().target_language_code)
    stmt = select(GrammarEntry)
    stmt = stmt.where(GrammarEntry.language_code == language_code)

    if status:
        stmt = stmt.where(GrammarEntry.status == status)
    if jlpt_level:
        stmt = stmt.where(GrammarEntry.jlpt_level == jlpt_level)
    if source:
        stmt = stmt.where(GrammarEntry.source == source)
    if search:
        search_pattern = f"%{search}%"
        stmt = stmt.where(
            (GrammarEntry.pattern.like(search_pattern)) |
            (GrammarEntry.meaning.like(search_pattern))
        )

    # Count total
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = await session.scalar(count_stmt)

    # Paginate and order
    offset = (page - 1) * limit
    stmt = stmt.offset(offset).limit(limit).order_by(
        GrammarEntry.jlpt_level.asc(),
        GrammarEntry.updated_at.desc()
    )

    result = await session.execute(stmt)
    entries = result.scalars().all()

    return {
        "items": [GrammarResponse.model_validate(e) for e in entries],
        "total": total,
        "page": page,
        "limit": limit,
    }


@router.get("/learning")
async def get_learning_grammar(
    limit: int = 100,
    language_code: Optional[str] = None,
    session=Depends(get_session),
):
    """Get all grammar entries with 'Learning' status."""
    language_code = normalize_language_code(language_code or get_settings().target_language_code)
    stmt = (
        select(GrammarEntry)
        .where(GrammarEntry.status == "Learning")
        .where(GrammarEntry.language_code == language_code)
        .order_by(GrammarEntry.jlpt_level.asc(), GrammarEntry.updated_at.desc())
        .limit(limit)
    )
    result = await session.execute(stmt)
    entries = result.scalars().all()
    return [GrammarResponse.model_validate(e) for e in entries]


@router.get("/stats")
async def get_grammar_stats(language_code: Optional[str] = None, session=Depends(get_session)):
    """Get grammar statistics by status and JLPT level."""
    language_code = normalize_language_code(language_code or get_settings().target_language_code)
    profile = get_language_profile(language_code)

    # Count by status
    by_status = {}
    for status in ["New", "Learning", "Burned"]:
        stmt = select(func.count()).where(
            GrammarEntry.status == status,
            GrammarEntry.language_code == language_code,
        )
        count = await session.scalar(stmt)
        by_status[status] = count or 0

    # Total count
    total_stmt = select(func.count()).select_from(GrammarEntry).where(GrammarEntry.language_code == language_code)
    total = await session.scalar(total_stmt) or 0

    # Count custom (non-JLPT) entries
    custom_stmt = select(func.count()).where(
        GrammarEntry.jlpt_level.is_(None),
        GrammarEntry.language_code == language_code,
    )
    custom = await session.scalar(custom_stmt) or 0

    # Count by JLPT level with status breakdown
    by_level = {}
    for level in profile.grammar_level_scheme.levels:
        level_total_stmt = select(func.count()).where(
            GrammarEntry.jlpt_level == level,
            GrammarEntry.language_code == language_code,
        )
        level_total = await session.scalar(level_total_stmt) or 0

        level_stats = {"total": level_total}
        for status in ["New", "Learning", "Burned"]:
            stmt = select(func.count()).where(
                and_(
                    GrammarEntry.jlpt_level == level,
                    GrammarEntry.language_code == language_code,
                    GrammarEntry.status == status
                )
            )
            count = await session.scalar(stmt)
            level_stats[status] = count or 0

        by_level[level] = level_stats

    return {
        "by_status": by_status,
        "by_level": by_level,
        "total": total,
        "custom": custom,
        "level_scheme": {
            "name": profile.grammar_level_scheme.name,
            "levels": profile.grammar_level_scheme.levels,
            "custom_label": profile.grammar_level_scheme.custom_label,
        },
    }


@router.get("/{grammar_id}")
async def get_grammar(grammar_id: int, session=Depends(get_session)):
    """Get a single grammar entry by ID."""
    stmt = select(GrammarEntry).where(GrammarEntry.id == grammar_id)
    result = await session.execute(stmt)
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Grammar entry not found")
    return GrammarResponse.model_validate(entry)


@router.post("")
async def create_grammar(data: GrammarCreate, session=Depends(get_session)):
    """Create a new grammar entry (user-created)."""
    language_code = normalize_language_code(data.language_code or get_settings().target_language_code)
    levels = get_language_profile(language_code).grammar_level_scheme.levels
    if data.jlpt_level and data.jlpt_level not in levels:
        raise HTTPException(status_code=400, detail=f"Invalid grammar level. Must be one of: {', '.join(levels)}")

    entry = GrammarEntry(
        language_code=language_code,
        pattern=data.pattern,
        meaning=data.meaning,
        jlpt_level=data.jlpt_level,
        notes=data.notes,
        source="manual",
        status="New",
    )
    session.add(entry)
    await session.commit()
    await session.refresh(entry)
    return GrammarResponse.model_validate(entry)


@router.put("/{grammar_id}")
async def update_grammar(grammar_id: int, data: GrammarUpdate, session=Depends(get_session)):
    """Update a grammar entry."""
    stmt = select(GrammarEntry).where(GrammarEntry.id == grammar_id)
    result = await session.execute(stmt)
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Grammar entry not found")

    if data.pattern is not None:
        entry.pattern = data.pattern
    if data.meaning is not None:
        entry.meaning = data.meaning
    if data.jlpt_level is not None:
        levels = get_language_profile(entry.language_code).grammar_level_scheme.levels
        if data.jlpt_level not in [*levels, ""]:
            raise HTTPException(status_code=400, detail="Invalid JLPT level")
        entry.jlpt_level = data.jlpt_level if data.jlpt_level else None
    if data.status is not None:
        if data.status not in ["New", "Learning", "Burned"]:
            raise HTTPException(status_code=400, detail="Invalid status. Must be New, Learning, or Burned")
        entry.status = data.status
    if data.notes is not None:
        entry.notes = data.notes

    await session.commit()
    await session.refresh(entry)
    return GrammarResponse.model_validate(entry)


@router.patch("/{grammar_id}/status")
async def update_grammar_status(grammar_id: int, data: GrammarStatusUpdate, session=Depends(get_session)):
    """Quick status update for a grammar entry."""
    if data.status not in ["New", "Learning", "Burned"]:
        raise HTTPException(status_code=400, detail="Invalid status. Must be New, Learning, or Burned")

    stmt = select(GrammarEntry).where(GrammarEntry.id == grammar_id)
    result = await session.execute(stmt)
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Grammar entry not found")

    entry.status = data.status
    await session.commit()
    await session.refresh(entry)
    return GrammarResponse.model_validate(entry)


@router.delete("/{grammar_id}")
async def delete_grammar(grammar_id: int, session=Depends(get_session)):
    """Delete a grammar entry."""
    stmt = select(GrammarEntry).where(GrammarEntry.id == grammar_id)
    result = await session.execute(stmt)
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Grammar entry not found")

    await session.delete(entry)
    await session.commit()
    return {"message": "Deleted successfully"}


@router.post("/seed")
async def seed_grammar(language_code: Optional[str] = None, session=Depends(get_session)):
    """Manually seed grammar from JLPT list file."""
    from app.services.grammar_seeder import seed_grammar_from_file

    language_code = normalize_language_code(language_code or get_settings().target_language_code)
    profile = get_language_profile(language_code)

    # Clear existing JLPT entries first
    stmt = select(GrammarEntry).where(
        GrammarEntry.language_code == language_code,
        GrammarEntry.source == profile.grammar_level_scheme.source_name,
    )
    result = await session.execute(stmt)
    existing = result.scalars().all()
    for entry in existing:
        await session.delete(entry)
    await session.commit()

    # Seed fresh
    result = await seed_grammar_from_file(session, language_code=language_code)
    return result
