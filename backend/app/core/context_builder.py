from typing import Optional, List, Dict
from datetime import date
import logging

from app.core.agents import TUTOR_SYSTEM_PROMPT_TEMPLATE, LISTENER_SYSTEM_PROMPT_TEMPLATE

logger = logging.getLogger(__name__)


async def build_tutor_context(
    session_id: str,
    difficulty_feedback: Optional[str] = None
) -> Dict:
    """Build the context for the Tutor agent (no tools, focused on teaching)."""
    # Load student facts (long-term memory about the student)
    student_facts = await fetch_student_facts()
    student_facts_formatted = format_student_facts(student_facts)

    # Load session summary (compacted conversation history)
    session_summary = await get_session_summary(session_id)

    # Fetch ALL learning vocabulary (no limit)
    vocab_list = await fetch_learning_vocab()

    # Format vocab list
    vocab_formatted = format_vocab_list(vocab_list)

    # Fetch learning grammar
    grammar_list = await fetch_learning_grammar()
    grammar_formatted = format_grammar_list(grammar_list)

    # Build system prompt using Tutor template (no tool instructions)
    system_prompt = TUTOR_SYSTEM_PROMPT_TEMPLATE.format(
        today=date.today().isoformat(),
        student_facts_formatted=student_facts_formatted,
        session_summary=session_summary or "(No previous conversation in this session)",
        vocab_list_formatted=vocab_formatted or "(No vocabulary loaded)",
        grammar_list_formatted=grammar_formatted or "(No grammar points loaded)",
    )

    # Fetch chat history (last 30 non-archived messages)
    chat_history = await get_chat_history(session_id, limit=30)

    return {
        "system_prompt": system_prompt,
        "chat_history": chat_history,
        # Raw data for logging
        "_raw": {
            "student_facts": student_facts,
            "session_summary": session_summary or "",
            "vocab_list": vocab_list,
            "grammar_list": grammar_list,
        },
    }


async def build_listener_context(
    user_message: str,
    tutor_message: str,
) -> Dict:
    """Build the context for the Listener agent (minimal, for fact extraction).

    Args:
        user_message: The student's message
        tutor_message: The tutor's previous response (for pronoun resolution)
    """
    # Load current facts with IDs so Listener can reference them for edit/delete
    student_facts = await fetch_student_facts()
    student_facts_formatted = format_student_facts(student_facts)

    # Load learning grammar with IDs for the Listener to reference
    learning_grammar = await fetch_learning_grammar()
    learning_grammar_formatted = format_grammar_list_with_ids(learning_grammar)

    # Build system prompt using Listener template
    system_prompt = LISTENER_SYSTEM_PROMPT_TEMPLATE.format(
        student_facts_formatted=student_facts_formatted,
        learning_grammar_formatted=learning_grammar_formatted,
        tutor_message=tutor_message,
        user_message=user_message,
    )

    return {
        "system_prompt": system_prompt,
        "user_message": user_message,
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
            lines.append(f"- {v['kanji']} ({v['kana']})")
        else:
            lines.append(f"- {v['kana']}")

    return "\n".join(lines)


async def fetch_student_facts() -> List[Dict]:
    """Fetch all student facts from the database."""
    from app.db.database import async_session_maker
    from app.db.models import StudentFact
    from sqlalchemy import select

    try:
        async with async_session_maker() as session:
            stmt = select(StudentFact).order_by(StudentFact.created_at.asc())
            result = await session.execute(stmt)
            facts = result.scalars().all()
            return [{"id": f.id, "content": f.content} for f in facts]
    except Exception:
        return []


def format_student_facts(facts: List[Dict]) -> str:
    """Format student facts as a list with IDs."""
    if not facts:
        return "(No information recorded yet)"
    return "\n".join(f"- [{f['id']}] {f['content']}" for f in facts)


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
                # User/assistant turns are committed together and can share the
                # same timestamp, so use the autoincrementing id for stable turn order.
                .order_by(ChatMessage.id.desc())
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


async def fetch_learning_grammar() -> List[Dict]:
    """Fetch ALL grammar points with 'Learning' status."""
    from app.db.database import async_session_maker
    from app.db.models import GrammarEntry
    from sqlalchemy import select

    try:
        async with async_session_maker() as session:
            stmt = (
                select(GrammarEntry)
                .where(GrammarEntry.status == "Learning")
                .order_by(GrammarEntry.jlpt_level.asc(), GrammarEntry.updated_at.desc())
            )
            result = await session.execute(stmt)
            entries = result.scalars().all()

            return [
                {
                    "id": e.id,
                    "pattern": e.pattern,
                    "meaning": e.meaning,
                    "jlpt_level": e.jlpt_level,
                }
                for e in entries
            ]
    except Exception as e:
        logger.error(f"Error fetching learning grammar: {e}")
        return []


def format_grammar_list(grammar_list: List[Dict]) -> str:
    """Format grammar list for the system prompt."""
    if not grammar_list:
        return ""

    lines = []
    for g in grammar_list:
        level_tag = f"[{g['jlpt_level']}] " if g.get('jlpt_level') else ""
        lines.append(f"- {level_tag}{g['pattern']} ({g['meaning']})")

    return "\n".join(lines)


def format_grammar_list_with_ids(grammar_list: List[Dict]) -> str:
    """Format grammar list with IDs for the Listener to reference."""
    if not grammar_list:
        return "(No grammar points being learned)"

    lines = []
    for g in grammar_list:
        level_tag = f"[{g['jlpt_level']}] " if g.get('jlpt_level') else ""
        lines.append(f"- [{g['id']}] {level_tag}{g['pattern']} ({g['meaning']})")

    return "\n".join(lines)
