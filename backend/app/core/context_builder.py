from typing import Optional, List, Dict
from datetime import date

from app.services.notes_service import NotesService
from app.config import get_settings


SYSTEM_PROMPT_TEMPLATE = """Current Date: {today}

You are a Japanese language tutor for an intermediate learner studying through immersion.

## Core Principles
- Default to responding in Japanese
- Push the student to the edge of their ability (i+1 hypothesis)
- Only switch to English for explicit grammar explanations, then immediately provide Japanese examples
- Use vocabulary the student is currently learning when possible
- Be a warm, personable tutor who remembers and cares about the student as a person

## About This Student
{student_record_content}

## Conversation Summary (This Session)
{session_summary}

## Vocabulary Currently Being Learned
{vocab_list_formatted}

## Instructions for Difficulty
- If user says something is "too hard", simplify slightly but don't overcompensate
- If user says something is "too easy", increase complexity gradually

## Tool Usage
Use update_student_record when you learn something important about the student that helps you be a better tutor:
- Goals: language learning goals and aspirations
- Background: their context, why they're learning
- Interests: hobbies, topics they enjoy discussing
- Preferences: learning style preferences, what works for them
- Notes: other important observations (grammar strengths/weaknesses, progress milestones)
"""


async def build_context(
    session_id: str,
    difficulty_feedback: Optional[str] = None
) -> Dict:
    """Build the context for a Gemini chat request."""
    settings = get_settings()
    notes_service = NotesService()

    # Load student record (long-term memory about the student)
    student_record = await notes_service.read_notes(settings.student_record_path)

    # Load session summary (compacted conversation history)
    session_summary = await get_session_summary(session_id)

    # Fetch ALL learning vocabulary (no limit)
    vocab_list = await fetch_learning_vocab()

    # Format vocab list
    vocab_formatted = format_vocab_list(vocab_list)

    # Build system prompt
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
        today=date.today().isoformat(),
        student_record_content=student_record or "(No student record yet)",
        session_summary=session_summary or "(No previous conversation in this session)",
        vocab_list_formatted=vocab_formatted or "(No vocabulary loaded)",
    )

    # Fetch chat history (last 30 non-archived messages)
    chat_history = await get_chat_history(session_id, limit=30)

    return {
        "system_prompt": system_prompt,
        "chat_history": chat_history,
        # Raw data for logging
        "_raw": {
            "student_record": student_record or "",
            "session_summary": session_summary or "",
            "vocab_list": vocab_list,
        },
    }


async def fetch_learning_vocab() -> List[Dict]:
    """Fetch ALL vocabulary words with 'Learning' status."""
    from app.db.database import async_session_maker
    from app.db.models import VocabEntry
    from sqlalchemy import select

    try:
        async with async_session_maker() as session:
            stmt = (
                select(VocabEntry)
                .where(VocabEntry.status == "Learning")
                .order_by(VocabEntry.updated_at.desc())
            )
            result = await session.execute(stmt)
            entries = result.scalars().all()

            return [
                {
                    "kanji": e.kanji,
                    "kana": e.kana,
                    "meaning": e.meaning,
                    "pos": e.pos,
                }
                for e in entries
            ]
    except Exception:
        return []


def format_vocab_list(vocab_list: List[Dict]) -> str:
    """Format vocabulary list for the system prompt."""
    if not vocab_list:
        return ""

    lines = []
    for v in vocab_list:
        if v["kanji"]:
            lines.append(f"- {v['kanji']} ({v['kana']}): {v['meaning']} [{v['pos']}]")
        else:
            lines.append(f"- {v['kana']}: {v['meaning']} [{v['pos']}]")

    return "\n".join(lines)


async def get_session_summary(session_id: str) -> Optional[str]:
    """Get the conversation summary for a session, if any."""
    from app.db.database import async_session_maker
    from app.db.models import ChatSession
    from sqlalchemy import select

    try:
        async with async_session_maker() as session:
            stmt = select(ChatSession.summary).where(ChatSession.id == session_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
    except Exception:
        return None


async def get_chat_history(session_id: str, limit: int = 15) -> List[Dict]:
    """Get recent non-archived chat history for the session."""
    from app.db.database import async_session_maker
    from app.db.models import ChatMessage
    from sqlalchemy import select

    try:
        async with async_session_maker() as session:
            stmt = (
                select(ChatMessage)
                .where(ChatMessage.session_id == session_id)
                .where(ChatMessage.is_archived == False)  # Exclude archived messages
                .order_by(ChatMessage.created_at.desc())
                .limit(limit)
            )
            result = await session.execute(stmt)
            messages = result.scalars().all()

            # Convert to Gemini format and reverse for chronological order
            history = []
            for msg in reversed(messages):
                history.append({
                    "role": msg.role if msg.role == "user" else "model",
                    "parts": [msg.content],
                })

            return history
    except Exception:
        return []
