from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy import select, delete, func
from datetime import datetime

from app.db.database import get_session
from app.db.models import ChatSession, ChatMessage
from app.config import get_settings
from app.core.language_profiles import normalize_language_code

router = APIRouter()


class SessionCreate(BaseModel):
    id: Optional[str] = None
    language_code: Optional[str] = None


class SessionUpdate(BaseModel):
    name: str


class SessionResponse(BaseModel):
    id: str
    language_code: str
    name: Optional[str]
    preview: Optional[str]
    message_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


@router.get("")
async def list_sessions(
    language_code: Optional[str] = None,
    session=Depends(get_session),
) -> list[SessionResponse]:
    """List sessions ordered by most recently updated, optionally scoped to
    one language so each language works as its own room."""
    stmt = select(ChatSession).order_by(ChatSession.updated_at.desc())
    if language_code:
        stmt = stmt.where(ChatSession.language_code == normalize_language_code(language_code))
    result = await session.execute(stmt)
    sessions = result.scalars().all()
    return [SessionResponse.model_validate(s) for s in sessions]


@router.post("")
async def create_session(
    data: SessionCreate,
    session=Depends(get_session)
) -> SessionResponse:
    """Create a new chat session."""
    import secrets

    session_id = data.id or f"session_{int(datetime.now().timestamp() * 1000)}_{secrets.token_hex(4)}"
    language_code = normalize_language_code(data.language_code or get_settings().target_language_code)

    chat_session = ChatSession(
        id=session_id,
        language_code=language_code,
        name=None,
        preview=None,
        message_count=0,
    )
    session.add(chat_session)
    await session.commit()
    await session.refresh(chat_session)

    return SessionResponse.model_validate(chat_session)


@router.get("/{session_id}")
async def get_session_by_id(
    session_id: str,
    session=Depends(get_session)
) -> SessionResponse:
    """Get a single session by ID."""
    stmt = select(ChatSession).where(ChatSession.id == session_id)
    result = await session.execute(stmt)
    chat_session = result.scalar_one_or_none()

    if not chat_session:
        raise HTTPException(status_code=404, detail="Session not found")

    return SessionResponse.model_validate(chat_session)


@router.put("/{session_id}")
async def update_session(
    session_id: str,
    data: SessionUpdate,
    session=Depends(get_session)
) -> SessionResponse:
    """Update session (rename)."""
    stmt = select(ChatSession).where(ChatSession.id == session_id)
    result = await session.execute(stmt)
    chat_session = result.scalar_one_or_none()

    if not chat_session:
        raise HTTPException(status_code=404, detail="Session not found")

    chat_session.name = data.name
    await session.commit()
    await session.refresh(chat_session)

    return SessionResponse.model_validate(chat_session)


@router.delete("/{session_id}")
async def delete_session(
    session_id: str,
    session=Depends(get_session)
):
    """Delete a session and all its messages."""
    # Delete all messages for this session
    await session.execute(
        delete(ChatMessage).where(ChatMessage.session_id == session_id)
    )

    # Delete the session
    await session.execute(
        delete(ChatSession).where(ChatSession.id == session_id)
    )

    await session.commit()

    return {"success": True}
