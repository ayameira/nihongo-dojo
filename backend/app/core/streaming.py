import json
from typing import Any, Dict


def format_sse_event(data: Dict[str, Any]) -> str:
    """Format data as a Server-Sent Event."""
    return f"data: {json.dumps(data)}\n\n"


def format_sse_done(usage: Dict[str, Any] = None) -> str:
    """Format the done event."""
    event_data = {"type": "done"}
    if usage:
        event_data["usage"] = usage
    return format_sse_event(event_data)


def format_sse_error(message: str) -> str:
    """Format an error event."""
    return format_sse_event({"type": "error", "content": message})


def format_sse_text(content: str) -> str:
    """Format a text chunk event."""
    return format_sse_event({"type": "text", "content": content})


def format_sse_tool_call(name: str, args: Dict[str, Any]) -> str:
    """Format a tool call event."""
    return format_sse_event({"type": "tool_call", "name": name, "args": args})


def format_sse_tool_result(name: str, result: str) -> str:
    """Format a tool result event."""
    return format_sse_event({"type": "tool_result", "name": name, "result": result})
