from typing import Any, Dict
import logging

logger = logging.getLogger(__name__)

# Tool definitions for Gemini
SAVE_VOCAB_TOOL = {
    "name": "save_vocab",
    "description": "Save a vocabulary word that was taught or corrected in the conversation. Always use dictionary form.",
    "parameters": {
        "type": "object",
        "properties": {
            "kanji": {
                "type": "string",
                "description": "Kanji writing (empty string if kana-only word)"
            },
            "kana": {
                "type": "string",
                "description": "Hiragana/katakana reading"
            },
            "meaning": {
                "type": "string",
                "description": "English meaning"
            },
            "pos": {
                "type": "string",
                "enum": ["noun", "verb", "i-adj", "na-adj", "adverb", "particle", "expression", "other"],
                "description": "Part of speech"
            }
        },
        "required": ["kana", "meaning", "pos"]
    }
}

UPDATE_NOTES_TOOL = {
    "name": "update_notes",
    "description": "Update a section of the student's study notes based on the conversation.",
    "parameters": {
        "type": "object",
        "properties": {
            "section": {
                "type": "string",
                "enum": ["current_focus", "recent_corrections", "recent_vocab"],
                "description": "Which section to update"
            },
            "action": {
                "type": "string",
                "enum": ["append", "replace"],
                "description": "Whether to append to or replace the section content"
            },
            "content": {
                "type": "string",
                "description": "Markdown content to add or replace"
            }
        },
        "required": ["section", "action", "content"]
    }
}

UPDATE_STUDENT_RECORD_TOOL = {
    "name": "update_student_record",
    "description": "Update the student's long-term record with important information about them. Use this to remember things that help you be a better tutor: their goals, interests, background, learning preferences, personal details they share, or anything else worth remembering about them as a person.",
    "parameters": {
        "type": "object",
        "properties": {
            "section": {
                "type": "string",
                "enum": ["goals", "background", "interests", "preferences", "notes"],
                "description": "Which section to update: goals (language learning goals), background (their background/context), interests (hobbies, topics they enjoy), preferences (learning style preferences), notes (other important info)"
            },
            "action": {
                "type": "string",
                "enum": ["append", "replace"],
                "description": "Whether to append to or replace the section content"
            },
            "content": {
                "type": "string",
                "description": "Markdown content to add or replace"
            }
        },
        "required": ["section", "action", "content"]
    }
}

ALL_TOOLS = [SAVE_VOCAB_TOOL, UPDATE_NOTES_TOOL, UPDATE_STUDENT_RECORD_TOOL]


async def execute_tool_call(tool_name: str, args: Dict[str, Any]) -> str:
    """Execute a tool call and return the result."""
    logger.info(f"Executing tool: {tool_name} with args: {args}")

    try:
        if tool_name == "save_vocab":
            return await execute_save_vocab(args)
        elif tool_name == "update_notes":
            return await execute_update_notes(args)
        elif tool_name == "update_student_record":
            return await execute_update_student_record(args)
        else:
            return f"Unknown tool: {tool_name}"
    except Exception as e:
        logger.error(f"Tool execution error: {e}")
        return f"Error executing {tool_name}: {str(e)}"


async def execute_save_vocab(args: Dict[str, Any]) -> str:
    """Save a vocabulary word to the database."""
    from app.db.database import async_session_maker
    from app.db.models import VocabEntry
    from sqlalchemy import select

    kanji = args.get("kanji", "")
    kana = args["kana"]
    meaning = args["meaning"]
    pos = args.get("pos", "other")

    async with async_session_maker() as session:
        # Check if word already exists
        stmt = select(VocabEntry).where(VocabEntry.kana == kana)
        if kanji:
            stmt = stmt.where(VocabEntry.kanji == kanji)

        result = await session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            # Update existing entry
            existing.meaning = meaning
            existing.pos = pos
            if existing.status == "New":
                existing.status = "Learning"
            await session.commit()
            return f"Updated vocabulary: {kanji or kana} ({meaning})"
        else:
            # Create new entry
            entry = VocabEntry(
                kanji=kanji if kanji else None,
                kana=kana,
                meaning=meaning,
                pos=pos,
                source="tutor",
                status="Learning",
            )
            session.add(entry)
            await session.commit()
            return f"Saved new vocabulary: {kanji or kana} ({meaning})"


async def execute_update_notes(args: Dict[str, Any]) -> str:
    """Update a section of the class notes."""
    from app.services.notes_service import NotesService
    from app.config import get_settings

    settings = get_settings()
    notes_service = NotesService()

    section = args["section"]
    action = args["action"]
    content = args["content"]

    await notes_service.update_section(
        settings.class_notes_path,
        section,
        content,
        action
    )

    return f"Updated {section} section"


async def execute_update_student_record(args: Dict[str, Any]) -> str:
    """Update a section of the student record."""
    from app.services.notes_service import NotesService
    from app.config import get_settings

    settings = get_settings()
    notes_service = NotesService()

    section = args["section"]
    action = args["action"]
    content = args["content"]

    await notes_service.update_student_record_section(
        settings.student_record_path,
        section,
        content,
        action
    )

    return f"Updated student record: {section}"
