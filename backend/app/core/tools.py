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

ALL_TOOLS = [MANAGE_STUDENT_FACTS_TOOL]


async def execute_tool_call(tool_name: str, args: Dict[str, Any]) -> str:
    """Execute a tool call and return the result."""
    logger.info(f"Executing tool: {tool_name} with args: {args}")

    try:
        if tool_name == "manage_student_facts":
            return await execute_manage_student_facts(args)
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
