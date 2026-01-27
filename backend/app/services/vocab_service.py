from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime

from app.db.models import VocabEntry


async def get_vocab_by_word(
    session: AsyncSession,
    kanji: Optional[str],
    kana: str
) -> Optional[VocabEntry]:
    """Find a vocabulary entry by kanji and kana."""
    stmt = select(VocabEntry).where(VocabEntry.kana == kana)
    if kanji:
        stmt = stmt.where(VocabEntry.kanji == kanji)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def create_vocab(
    session: AsyncSession,
    kanji: Optional[str],
    kana: str,
    meaning: str,
    pos: Optional[str] = None,
    source: str = "manual"
) -> VocabEntry:
    """Create a new vocabulary entry."""
    entry = VocabEntry(
        kanji=kanji,
        kana=kana,
        meaning=meaning,
        pos=pos,
        source=source,
        status="New",
    )
    session.add(entry)
    await session.commit()
    await session.refresh(entry)
    return entry


async def update_vocab_status(
    session: AsyncSession,
    vocab_id: int,
    status: str
) -> Optional[VocabEntry]:
    """Update the status of a vocabulary entry."""
    stmt = select(VocabEntry).where(VocabEntry.id == vocab_id)
    result = await session.execute(stmt)
    entry = result.scalar_one_or_none()

    if entry:
        entry.status = status
        await session.commit()
        await session.refresh(entry)

    return entry


async def increment_seen(
    session: AsyncSession,
    vocab_id: int
) -> Optional[VocabEntry]:
    """Increment the times_seen counter."""
    stmt = select(VocabEntry).where(VocabEntry.id == vocab_id)
    result = await session.execute(stmt)
    entry = result.scalar_one_or_none()

    if entry:
        entry.times_seen += 1
        entry.last_seen_at = datetime.utcnow()
        await session.commit()

    return entry


async def get_learning_vocab(
    session: AsyncSession,
    limit: int = 50
) -> List[VocabEntry]:
    """Get vocabulary entries with Learning status."""
    stmt = (
        select(VocabEntry)
        .where(VocabEntry.status == "Learning")
        .order_by(VocabEntry.updated_at.desc())
        .limit(limit)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def search_vocab(
    session: AsyncSession,
    query: str,
    limit: int = 20
) -> List[VocabEntry]:
    """Search vocabulary by kanji, kana, or meaning."""
    pattern = f"%{query}%"
    stmt = (
        select(VocabEntry)
        .where(
            (VocabEntry.kanji.like(pattern)) |
            (VocabEntry.kana.like(pattern)) |
            (VocabEntry.meaning.like(pattern))
        )
        .limit(limit)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_vocab_stats(session: AsyncSession) -> Dict[str, int]:
    """Get vocabulary statistics by status."""
    stats = {}
    for status in ["New", "Learning", "Mature"]:
        stmt = select(func.count()).where(VocabEntry.status == status)
        count = await session.scalar(stmt)
        stats[status.lower()] = count or 0

    total_stmt = select(func.count()).select_from(VocabEntry)
    stats["total"] = await session.scalar(total_stmt) or 0

    return stats
