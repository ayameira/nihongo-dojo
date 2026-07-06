from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from app.db.database import get_session
from app.db.models import StudentFact
from app.core.language_profiles import normalize_language_code

router = APIRouter()


class FactCreate(BaseModel):
    content: str


class FactUpdate(BaseModel):
    content: str


def _facts_query(language_code: Optional[str]):
    """Facts for one language plus global (NULL-language) facts, matching what
    the context builder feeds the tutor. No filter returns everything."""
    stmt = select(StudentFact)
    if language_code:
        normalized = normalize_language_code(language_code)
        stmt = stmt.where(
            or_(
                StudentFact.language_code == normalized,
                StudentFact.language_code.is_(None),
            )
        )
    return stmt.order_by(StudentFact.created_at.asc())


@router.get("")
async def get_notes(
    language_code: Optional[str] = None,
    session: AsyncSession = Depends(get_session),
):
    """Get all student facts formatted as content."""
    result = await session.execute(_facts_query(language_code))
    facts = result.scalars().all()

    if not facts:
        content = "(No information recorded yet)"
    else:
        content = "\n".join(f"- {f.content}" for f in facts)

    return {"content": content}


@router.get("/facts")
async def list_facts(
    language_code: Optional[str] = None,
    session: AsyncSession = Depends(get_session),
):
    """Get all student facts as a list."""
    result = await session.execute(_facts_query(language_code))
    facts = result.scalars().all()

    return {
        "facts": [
            {
                "id": f.id,
                "content": f.content,
                "source": f.source,
                "language_code": f.language_code,
                "created_at": f.created_at.isoformat() if f.created_at else None,
            }
            for f in facts
        ]
    }


@router.post("/facts")
async def add_fact(data: FactCreate, session: AsyncSession = Depends(get_session)):
    """Add a new student fact."""
    # Check for duplicate
    stmt = select(StudentFact).where(StudentFact.content == data.content)
    existing = (await session.execute(stmt)).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Fact already exists")

    # Facts added by hand stay global (NULL language): they describe the
    # learner, and every language profile's tutor should see them.
    fact = StudentFact(content=data.content, source="manual")
    session.add(fact)
    await session.commit()
    await session.refresh(fact)

    return {
        "id": fact.id,
        "content": fact.content,
        "source": fact.source,
        "language_code": fact.language_code,
    }


@router.delete("/facts/{fact_id}")
async def delete_fact(fact_id: int, session: AsyncSession = Depends(get_session)):
    """Delete a student fact by ID."""
    stmt = select(StudentFact).where(StudentFact.id == fact_id)
    fact = (await session.execute(stmt)).scalar_one_or_none()

    if not fact:
        raise HTTPException(status_code=404, detail="Fact not found")

    await session.delete(fact)
    await session.commit()

    return {"message": f"Fact {fact_id} deleted"}


@router.put("/facts/{fact_id}")
async def update_fact(fact_id: int, data: FactUpdate, session: AsyncSession = Depends(get_session)):
    """Update a student fact by ID."""
    stmt = select(StudentFact).where(StudentFact.id == fact_id)
    fact = (await session.execute(stmt)).scalar_one_or_none()

    if not fact:
        raise HTTPException(status_code=404, detail="Fact not found")

    fact.content = data.content
    await session.commit()

    return {"message": f"Fact {fact_id} updated", "content": data.content}


@router.get("/token-count")
async def get_token_count(session: AsyncSession = Depends(get_session)):
    """Get the approximate token count of all facts."""
    stmt = select(StudentFact)
    result = await session.execute(stmt)
    facts = result.scalars().all()

    total_chars = sum(len(f.content) for f in facts)
    # Simple estimation: ~4 characters per token
    count = total_chars // 4 if total_chars else 0
    return {"token_count": count}
