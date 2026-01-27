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

## Student's Current Study Notes
{class_notes_content}

## Vocabulary Currently Being Learned
{vocab_list_formatted}

## Instructions for Difficulty
- If user says something is "too hard", simplify slightly but don't overcompensate
- If user says something is "too easy", increase complexity gradually
- When teaching new words, use the save_vocab tool
- When noticing patterns in student mistakes, update the notes

## Tool Usage
- Use save_vocab when you teach or correct a word (always dictionary form)
- Use update_notes when you notice patterns worth remembering
{difficulty_instruction}
"""


async def build_context(
    session_id: str,
    difficulty_feedback: Optional[str] = None
) -> Dict:
    """Build the context for a Gemini chat request."""
    settings = get_settings()
    notes_service = NotesService()

    # Load class notes
    class_notes = await notes_service.read_notes(settings.class_notes_path)

    # Fetch learning vocabulary
    vocab_list = await fetch_learning_vocab(limit=50)

    # Format vocab list
    vocab_formatted = format_vocab_list(vocab_list)

    # Difficulty instruction
    difficulty_instruction = ""
    if difficulty_feedback == "too_hard":
        difficulty_instruction = "\n**Note:** The student indicated the previous content was too hard. Simplify your next response slightly."
    elif difficulty_feedback == "too_easy":
        difficulty_instruction = "\n**Note:** The student indicated the previous content was too easy. Increase complexity in your next response."

    # Build system prompt
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
        today=date.today().isoformat(),
        class_notes_content=class_notes or "(No notes yet)",
        vocab_list_formatted=vocab_formatted or "(No vocabulary loaded)",
        difficulty_instruction=difficulty_instruction,
    )

    # Fetch chat history
    chat_history = await get_chat_history(session_id, limit=15)

    return {
        "system_prompt": system_prompt,
        "chat_history": chat_history,
    }


async def fetch_learning_vocab(limit: int = 50) -> List[Dict]:
    """Fetch vocabulary words with 'Learning' status."""
    from app.db.database import async_session_maker
    from app.db.models import VocabEntry
    from sqlalchemy import select

    try:
        async with async_session_maker() as session:
            stmt = (
                select(VocabEntry)
                .where(VocabEntry.status == "Learning")
                .order_by(VocabEntry.updated_at.desc())
                .limit(limit)
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
