from typing import Any, Dict
import logging

logger = logging.getLogger(__name__)

# Tool definitions for Gemini
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

ALL_TOOLS = [UPDATE_STUDENT_RECORD_TOOL]


async def execute_tool_call(tool_name: str, args: Dict[str, Any]) -> str:
    """Execute a tool call and return the result."""
    logger.info(f"Executing tool: {tool_name} with args: {args}")

    try:
        if tool_name == "update_student_record":
            return await execute_update_student_record(args)
        else:
            return f"Unknown tool: {tool_name}"
    except Exception as e:
        logger.error(f"Tool execution error: {e}")
        return f"Error executing {tool_name}: {str(e)}"


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
