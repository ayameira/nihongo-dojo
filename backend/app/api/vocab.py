from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy import select, func
from datetime import datetime

from app.db.database import get_session
from app.db.models import VocabEntry

router = APIRouter()


class VocabCreate(BaseModel):
    kanji: Optional[str] = None
    kana: str
    meaning: str
    pos: Optional[str] = None


class VocabUpdate(BaseModel):
    kanji: Optional[str] = None
    kana: Optional[str] = None
    meaning: Optional[str] = None
    pos: Optional[str] = None
    status: Optional[str] = None


class VocabResponse(BaseModel):
    id: int
    kanji: Optional[str]
    kana: str
    meaning: str
    pos: Optional[str]
    status: str
    source: str
    times_seen: int
    times_correct: int
    last_seen_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


@router.get("")
async def list_vocab(
    status: Optional[str] = None,
    source: Optional[str] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    session=Depends(get_session)
):
    stmt = select(VocabEntry)

    if status:
        stmt = stmt.where(VocabEntry.status == status)
    if source:
        stmt = stmt.where(VocabEntry.source == source)
    if search:
        search_pattern = f"%{search}%"
        stmt = stmt.where(
            (VocabEntry.kanji.like(search_pattern)) |
            (VocabEntry.kana.like(search_pattern)) |
            (VocabEntry.meaning.like(search_pattern))
        )

    # Count total
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = await session.scalar(count_stmt)

    # Paginate
    offset = (page - 1) * limit
    stmt = stmt.offset(offset).limit(limit).order_by(VocabEntry.updated_at.desc())

    result = await session.execute(stmt)
    entries = result.scalars().all()

    return {
        "items": [VocabResponse.model_validate(e) for e in entries],
        "total": total,
        "page": page,
        "limit": limit,
    }


@router.get("/learning")
async def get_learning_vocab(limit: int = 50, session=Depends(get_session)):
    stmt = (
        select(VocabEntry)
        .where(VocabEntry.status == "Learning")
        .order_by(VocabEntry.updated_at.desc())
        .limit(limit)
    )
    result = await session.execute(stmt)
    entries = result.scalars().all()
    return [VocabResponse.model_validate(e) for e in entries]


@router.get("/stats")
async def get_vocab_stats(session=Depends(get_session)):
    stats = {}
    for status in ["New", "Learning", "Mature"]:
        stmt = select(func.count()).where(VocabEntry.status == status)
        count = await session.scalar(stmt)
        stats[status.lower()] = count or 0

    total_stmt = select(func.count()).select_from(VocabEntry)
    stats["total"] = await session.scalar(total_stmt) or 0

    return stats


@router.get("/{vocab_id}")
async def get_vocab(vocab_id: int, session=Depends(get_session)):
    stmt = select(VocabEntry).where(VocabEntry.id == vocab_id)
    result = await session.execute(stmt)
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Vocabulary entry not found")
    return VocabResponse.model_validate(entry)


@router.post("")
async def create_vocab(data: VocabCreate, session=Depends(get_session)):
    entry = VocabEntry(
        kanji=data.kanji,
        kana=data.kana,
        meaning=data.meaning,
        pos=data.pos,
        source="manual",
        status="New",
    )
    session.add(entry)
    await session.commit()
    await session.refresh(entry)
    return VocabResponse.model_validate(entry)


@router.put("/{vocab_id}")
async def update_vocab(vocab_id: int, data: VocabUpdate, session=Depends(get_session)):
    stmt = select(VocabEntry).where(VocabEntry.id == vocab_id)
    result = await session.execute(stmt)
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Vocabulary entry not found")

    if data.kanji is not None:
        entry.kanji = data.kanji
    if data.kana is not None:
        entry.kana = data.kana
    if data.meaning is not None:
        entry.meaning = data.meaning
    if data.pos is not None:
        entry.pos = data.pos
    if data.status is not None:
        entry.status = data.status

    await session.commit()
    await session.refresh(entry)
    return VocabResponse.model_validate(entry)


@router.delete("/{vocab_id}")
async def delete_vocab(vocab_id: int, session=Depends(get_session)):
    stmt = select(VocabEntry).where(VocabEntry.id == vocab_id)
    result = await session.execute(stmt)
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Vocabulary entry not found")

    await session.delete(entry)
    await session.commit()
    return {"message": "Deleted successfully"}


@router.post("/{vocab_id}/seen")
async def mark_seen(vocab_id: int, session=Depends(get_session)):
    stmt = select(VocabEntry).where(VocabEntry.id == vocab_id)
    result = await session.execute(stmt)
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Vocabulary entry not found")

    entry.times_seen += 1
    entry.last_seen_at = datetime.utcnow()
    await session.commit()
    return {"times_seen": entry.times_seen}


@router.post("/{vocab_id}/correct")
async def mark_correct(vocab_id: int, session=Depends(get_session)):
    stmt = select(VocabEntry).where(VocabEntry.id == vocab_id)
    result = await session.execute(stmt)
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Vocabulary entry not found")

    entry.times_correct += 1
    await session.commit()
    return {"times_correct": entry.times_correct}


@router.post("/import-anki")
async def import_anki(session=Depends(get_session)):
    from app.services.anki_importer import import_anki_collection
    from app.config import get_settings

    settings = get_settings()
    if not settings.anki_collection_path:
        raise HTTPException(status_code=400, detail="ANKI_COLLECTION_PATH not configured")

    result = await import_anki_collection(settings.anki_collection_path, session)
    return result
