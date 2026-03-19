from typing import Any, Dict
import logging

logger = logging.getLogger(__name__)

# Tool definitions for Gemini
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
            }
        },
        "required": ["action"]
    }
}

MANAGE_GRAMMAR_TOOL = {
    "name": "manage_grammar",
    "description": "Manage grammar points in the student's learning list. Use this when the student asks to add or change a grammar point, or when you want to suggest a grammar point for them to study.",
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["add", "update_status", "add_notes"],
                "description": "add: Create a new grammar point. update_status: Change status of an existing grammar point. add_notes: Add study notes to a grammar point."
            },
            "pattern": {
                "type": "string",
                "description": "The Japanese grammar pattern (e.g. 'ている', 'ければ'). Required for 'add'."
            },
            "meaning": {
                "type": "string",
                "description": "English meaning/explanation. Required for 'add'."
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
                "description": "JLPT level (N5, N4, N3, N2, N1). Optional for 'add'."
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
    """Manage student facts in the database."""
    from app.db.database import async_session_maker
    from app.db.models import StudentFact
    from sqlalchemy import select

    action = args.get("action")
    content = args.get("content", "").strip()
    fact_id = args.get("fact_id")

    if not action:
        return "Error: 'action' is required"

    async with async_session_maker() as session:
        if action == "add":
            if not content:
                return "Error: 'content' is required for add action"

            # Check for duplicate (exact match)
            stmt = select(StudentFact).where(StudentFact.content == content)
            existing = (await session.execute(stmt)).scalar_one_or_none()
            if existing:
                return "Fact already exists (duplicate not added)"

            fact = StudentFact(content=content, source="listener")
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

    if not action:
        return "Error: 'action' is required"

    async with async_session_maker() as session:
        if action == "add":
            pattern = args.get("pattern", "").strip()
            meaning = args.get("meaning", "").strip()
            if not pattern or not meaning:
                return "Error: 'pattern' and 'meaning' are required for add"

            # Check for duplicate
            stmt = select(GrammarEntry).where(GrammarEntry.pattern == pattern)
            existing = (await session.execute(stmt)).scalar_one_or_none()
            if existing:
                return f"Grammar point '{pattern}' already exists (ID: {existing.id}, status: {existing.status})"

            jlpt_level = args.get("jlpt_level")
            if jlpt_level and jlpt_level not in ["N5", "N4", "N3", "N2", "N1"]:
                jlpt_level = None

            entry = GrammarEntry(
                pattern=pattern,
                meaning=meaning,
                jlpt_level=jlpt_level,
                source="tutor",
                status="Learning",  # AI-added points start as Learning
            )
            session.add(entry)
            await session.commit()
            await session.refresh(entry)
            return f"Added grammar point [#{entry.id}]: {pattern} ({meaning})"

        elif action == "update_status":
            grammar_id = args.get("grammar_id")
            new_status = args.get("status")
            if grammar_id is None or not new_status:
                return "Error: 'grammar_id' and 'status' required for update_status"

            if new_status not in ["New", "Learning", "Burned"]:
                return f"Error: Invalid status '{new_status}'. Must be New, Learning, or Burned"

            stmt = select(GrammarEntry).where(GrammarEntry.id == grammar_id)
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

            stmt = select(GrammarEntry).where(GrammarEntry.id == grammar_id)
            entry = (await session.execute(stmt)).scalar_one_or_none()
            if not entry:
                return f"Error: No grammar point found with ID {grammar_id}"

            entry.notes = notes
            await session.commit()
            return f"Added notes to grammar [#{grammar_id}] '{entry.pattern}'"

        else:
            return f"Unknown action: {action}"
