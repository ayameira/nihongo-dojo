import logging
import re
from typing import Any, Dict

from app.core.language_profiles import get_language_profile, normalize_language_code

logger = logging.getLogger(__name__)


def normalize_grammar_pattern(pattern: str) -> str:
    """Normalize teaching notation so tool calls can match seeded JLPT entries."""
    pattern = pattern.strip()
    pattern = pattern.replace("＋", "+").replace("（", "(").replace("）", ")")
    # Strip common explanatory notation while preserving Japanese text and digits
    # used to disambiguate entries like "から 1" and "から 2".
    return re.sub(r"[A-Za-z\s\(\)\+\[\]\{\}/,.;:：・〜~○〇…_-]+", "", pattern)

# Provider-neutral tool definitions.
MANAGE_STUDENT_FACTS_TOOL = {
    "name": "manage_student_facts",
    "description": "Manage long-term facts about the student. Use this to remember important information that helps you be a better tutor: their goals, interests, background, learning preferences, personal details, or progress observations. Facts are stored permanently across sessions.",
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["add", "edit", "delete"],
                "description": "add: Store a new fact. edit: Update an existing fact by ID. delete: Remove a fact by ID."
            },
            "content": {
                "type": "string",
                "description": "For 'add': the new fact to store. For 'edit': the updated text. For 'delete': not required."
            },
            "fact_id": {
                "type": "integer",
                "description": "Required for 'edit' and 'delete'. The ID of the fact to modify (shown in brackets in the facts list)."
            },
            "language_code": {
                "type": "string",
                "description": "Language room the fact belongs to. Defaults to the active session language."
            }
        },
        "required": ["action"]
    }
}

MANAGE_GRAMMAR_TOOL = {
    "name": "manage_grammar",
    "description": "Manage grammar points in the student's learning list. Use this when the student asks to add or change a grammar point, or when a tutoring exchange clearly introduces a concrete grammar point the student should now practice.",
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["add", "start_learning", "update_status", "add_notes"],
                "description": "add: Create a new custom grammar point. start_learning: Mark an existing grammar point as Learning by pattern, or create a custom Learning point if absent. update_status: Change status of an existing grammar point. add_notes: Add study notes to a grammar point."
            },
            "pattern": {
                "type": "string",
                "description": "The target-language grammar pattern (e.g. Japanese 'ている', 'ければ'). Required for 'add' and 'start_learning'."
            },
            "meaning": {
                "type": "string",
                "description": "English meaning/explanation. Required for 'add' and for 'start_learning' when creating a custom point."
            },
            "grammar_id": {
                "type": "integer",
                "description": "The ID of the grammar point. Required for 'update_status' and 'add_notes'."
            },
            "status": {
                "type": "string",
                "enum": ["New", "Learning", "Burned"],
                "description": "The new status. Required for 'update_status'."
            },
            "notes": {
                "type": "string",
                "description": "Study notes to add. Required for 'add_notes'."
            },
            "jlpt_level": {
                "type": "string",
                "description": "Profile grammar level. For Japanese, this is JLPT level (N5, N4, N3, N2, N1). Optional for 'add'."
            },
            "language_code": {
                "type": "string",
                "description": "Target language code. Defaults to the active session language."
            }
        },
        "required": ["action"]
    }
}

ALL_TOOLS = [MANAGE_STUDENT_FACTS_TOOL, MANAGE_GRAMMAR_TOOL]


async def execute_tool_call(tool_name: str, args: Dict[str, Any]) -> str:
    """Execute a tool call and return the result."""
    logger.info(f"Executing tool: {tool_name} with args: {args}")

    try:
        if tool_name == "manage_student_facts":
            return await execute_manage_student_facts(args)
        elif tool_name == "manage_grammar":
            return await execute_manage_grammar(args)
        else:
            return f"Unknown tool: {tool_name}"
    except Exception as e:
        logger.error(f"Tool execution error: {e}")
        return f"Error executing {tool_name}: {str(e)}"


async def execute_manage_student_facts(args: Dict[str, Any]) -> str:
    """Manage student facts in the database. Facts always belong to one
    language room; the listener injects the session language when the model
    leaves it out."""
    from app.db.database import async_session_maker
    from app.db.models import StudentFact
    from sqlalchemy import select

    action = args.get("action")
    content = args.get("content", "").strip()
    fact_id = args.get("fact_id")
    language_code = normalize_language_code(args.get("language_code"))

    if not action:
        return "Error: 'action' is required"

    async with async_session_maker() as session:
        if action == "add":
            if not content:
                return "Error: 'content' is required for add action"

            # Check for duplicate (exact match) within the room
            stmt = select(StudentFact).where(
                StudentFact.content == content,
                StudentFact.language_code == language_code,
            )
            existing = (await session.execute(stmt)).scalar_one_or_none()
            if existing:
                return "Fact already exists (duplicate not added)"

            fact = StudentFact(content=content, source="listener", language_code=language_code)
            session.add(fact)
            await session.commit()
            await session.refresh(fact)
            return f"Added fact [#{fact.id}]: {content[:60]}{'...' if len(content) > 60 else ''}"

        elif action == "edit":
            if fact_id is None:
                return "Error: 'fact_id' is required for edit action"
            if not content:
                return "Error: 'content' is required for edit action (the new text)"

            stmt = select(StudentFact).where(StudentFact.id == fact_id)
            fact = (await session.execute(stmt)).scalar_one_or_none()
            if not fact:
                return f"Error: No fact found with ID {fact_id}"

            old_content = fact.content
            fact.content = content
            await session.commit()
            return f"Updated fact [#{fact_id}]: '{old_content[:30]}...' → '{content[:30]}...'"

        elif action == "delete":
            if fact_id is None:
                return "Error: 'fact_id' is required for delete action"

            stmt = select(StudentFact).where(StudentFact.id == fact_id)
            fact = (await session.execute(stmt)).scalar_one_or_none()
            if not fact:
                return f"Error: No fact found with ID {fact_id}"

            deleted_content = fact.content
            await session.delete(fact)
            await session.commit()
            return f"Deleted fact [#{fact_id}]: {deleted_content[:60]}{'...' if len(deleted_content) > 60 else ''}"

        else:
            return f"Unknown action: {action}"


async def execute_manage_grammar(args: Dict[str, Any]) -> str:
    """Manage grammar points in the database."""
    from app.db.database import async_session_maker
    from app.db.models import GrammarEntry
    from sqlalchemy import select

    action = args.get("action")
    language_code = normalize_language_code(args.get("language_code"))
    profile = get_language_profile(language_code)

    if not action:
        return "Error: 'action' is required"

    def normalized_jlpt_level(value: Any) -> str | None:
        if value in profile.grammar_level_scheme.levels:
            return value
        return None

    def merge_notes(existing_notes: str | None, new_notes: str) -> str:
        if not existing_notes:
            return new_notes
        if new_notes in existing_notes:
            return existing_notes
        return f"{existing_notes}\n\n{new_notes}"

    async def find_existing_grammar(pattern: str) -> GrammarEntry | None:
        stmt = select(GrammarEntry).where(
            GrammarEntry.language_code == language_code,
            GrammarEntry.pattern == pattern,
        )
        exact = (await session.execute(stmt)).scalar_one_or_none()
        if exact:
            return exact

        normalized = normalize_grammar_pattern(pattern)
        if not normalized:
            return None

        stmt = select(GrammarEntry).where(GrammarEntry.language_code == language_code)
        entries = (await session.execute(stmt)).scalars().all()
        matches = [
            entry for entry in entries
            if normalize_grammar_pattern(entry.pattern) == normalized
        ]
        if len(matches) == 1:
            return matches[0]
        return None

    async with async_session_maker() as session:
        if action == "add":
            pattern = args.get("pattern", "").strip()
            meaning = args.get("meaning", "").strip()
            notes = args.get("notes", "").strip()
            if not pattern or not meaning:
                return "Error: 'pattern' and 'meaning' are required for add"

            # Check for duplicate, allowing for teaching notation like "〜より".
            existing = await find_existing_grammar(pattern)
            if existing:
                return f"Grammar point '{pattern}' already exists (ID: {existing.id}, status: {existing.status})"

            jlpt_level = normalized_jlpt_level(args.get("jlpt_level"))

            entry = GrammarEntry(
                language_code=language_code,
                pattern=pattern,
                meaning=meaning,
                jlpt_level=jlpt_level,
                source="tutor",
                notes=notes or None,
                status="Learning",  # AI-added points start as Learning
            )
            session.add(entry)
            await session.commit()
            await session.refresh(entry)
            return f"Added grammar point [#{entry.id}]: {pattern} ({meaning})"

        elif action == "start_learning":
            pattern = args.get("pattern", "").strip()
            meaning = args.get("meaning", "").strip()
            notes = args.get("notes", "").strip()
            if not pattern:
                return "Error: 'pattern' is required for start_learning"

            entry = await find_existing_grammar(pattern)

            if entry:
                old_status = entry.status
                entry.status = "Learning"
                if notes:
                    entry.notes = merge_notes(entry.notes, notes)
                await session.commit()
                return (
                    f"Started learning grammar [#{entry.id}] '{entry.pattern}': "
                    f"{old_status} -> Learning"
                )

            if not meaning:
                return "Error: 'meaning' is required when start_learning creates a custom point"

            entry = GrammarEntry(
                language_code=language_code,
                pattern=pattern,
                meaning=meaning,
                jlpt_level=normalized_jlpt_level(args.get("jlpt_level")),
                source="tutor",
                notes=notes or None,
                status="Learning",
            )
            session.add(entry)
            await session.commit()
            await session.refresh(entry)
            return f"Added custom learning grammar [#{entry.id}]: {pattern} ({meaning})"

        elif action == "update_status":
            grammar_id = args.get("grammar_id")
            new_status = args.get("status")
            if grammar_id is None or not new_status:
                return "Error: 'grammar_id' and 'status' required for update_status"

            if new_status not in ["New", "Learning", "Burned"]:
                return f"Error: Invalid status '{new_status}'. Must be New, Learning, or Burned"

            stmt = select(GrammarEntry).where(
                GrammarEntry.id == grammar_id,
                GrammarEntry.language_code == language_code,
            )
            entry = (await session.execute(stmt)).scalar_one_or_none()
            if not entry:
                return f"Error: No grammar point found with ID {grammar_id}"

            old_status = entry.status
            entry.status = new_status
            await session.commit()
            return f"Updated grammar [#{grammar_id}] '{entry.pattern}': {old_status} -> {new_status}"

        elif action == "add_notes":
            grammar_id = args.get("grammar_id")
            notes = args.get("notes", "").strip()
            if grammar_id is None or not notes:
                return "Error: 'grammar_id' and 'notes' required for add_notes"

            stmt = select(GrammarEntry).where(
                GrammarEntry.id == grammar_id,
                GrammarEntry.language_code == language_code,
            )
            entry = (await session.execute(stmt)).scalar_one_or_none()
            if not entry:
                return f"Error: No grammar point found with ID {grammar_id}"

            entry.notes = notes
            await session.commit()
            return f"Added notes to grammar [#{grammar_id}] '{entry.pattern}'"

        else:
            return f"Unknown action: {action}"
