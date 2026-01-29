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

## Current Study Focus (Recent Memory)
{class_notes_content}

## Vocabulary Currently Being Learned
{vocab_list_formatted}

## Instructions for Difficulty
- If user says something is "too hard", simplify slightly but don't overcompensate
- If user says something is "too easy", increase complexity gradually

## Tool Usage
- Use update_notes when you notice patterns in current learning worth remembering
- Use update_student_record when you learn something important about the student (goals, interests, background, preferences, or anything that helps you be a better tutor for them)

## Important: Keep Notes Updated
ALWAYS record new learnings in the class notes using update_notes. This includes:
- New grammar points introduced or practiced
- Expressions and phrases taught
- Vocabulary themes explored (e.g., "studied medical terms", "practiced food vocabulary")
- Patterns in mistakes or areas needing work
- Any significant teaching moments

Record the broader learning context and themes, not individual words.

When the class notes get too long or topics become stale, clean them up. Before removing anything, ask yourself: "Is this worth remembering long-term?" If yes, move it to the student record (e.g., "student has solid grasp of て-form", "struggles with keigo"). If it's no longer relevant, you can remove it.
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

    # Load class notes (recent memory / current focus)
    class_notes = await notes_service.read_notes(settings.class_notes_path)

    # Fetch ALL learning vocabulary (no limit)
    vocab_list = await fetch_learning_vocab()

    # Format vocab list
    vocab_formatted = format_vocab_list(vocab_list)

    # Build system prompt
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
        today=date.today().isoformat(),
        student_record_content=student_record or "(No student record yet)",
        class_notes_content=class_notes or "(No notes yet)",
        vocab_list_formatted=vocab_formatted or "(No vocabulary loaded)",
    )

    # Fetch chat history (last 30 messages)
    chat_history = await get_chat_history(session_id, limit=30)

    return {
        "system_prompt": system_prompt,
        "chat_history": chat_history,
        # Raw data for logging
        "_raw": {
            "student_record": student_record or "",
            "class_notes": class_notes or "",
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


async def get_chat_history(session_id: str, limit: int = 15) -> List[Dict]:
    """Get recent chat history for the session."""
    from app.db.database import async_session_maker
    from app.db.models import ChatMessage
    from sqlalchemy import select

    try:
        async with async_session_maker() as session:
            stmt = (
                select(ChatMessage)
                .where(ChatMessage.session_id == session_id)
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
