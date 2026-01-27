from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
import json
import asyncio

from app.db.database import get_session
from app.config import get_settings

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    image_data: Optional[str] = None
    session_id: str
    difficulty_feedback: Optional[str] = None  # 'too_hard' | 'too_easy'


async def generate_stream(request: ChatRequest, settings):
    """Generate SSE stream for chat response."""
    from app.core.gemini_client import GeminiClient
    from app.core.context_builder import build_context
    from app.core.tools import execute_tool_call
    from app.db.database import async_session_maker
    from app.db.models import ChatMessage, TokenLog

    if not settings.gemini_api_key:
        yield f"data: {json.dumps({'type': 'error', 'content': 'Gemini API key not configured'})}\n\n"
        return

    try:
        client = GeminiClient(settings)

        # Build context
        context = await build_context(request.session_id, request.difficulty_feedback)

        # Prepare message parts
        parts = [request.message]
        if request.image_data:
            parts.append({"mime_type": "image/jpeg", "data": request.image_data})

        # Stream response
        full_response = ""
        tool_calls = []
        usage_data = None

        async for chunk in client.stream_chat(context, parts):
            if chunk["type"] == "text":
                full_response += chunk["content"]
                yield f"data: {json.dumps(chunk)}\n\n"
            elif chunk["type"] == "tool_call":
                tool_calls.append(chunk)
                # Execute tool call
                result = await execute_tool_call(chunk["name"], chunk["args"])
                yield f"data: {json.dumps({'type': 'tool_result', 'name': chunk['name'], 'result': result})}\n\n"
            elif chunk["type"] == "usage":
                usage_data = chunk

        # Save to database
        async with async_session_maker() as session:
            # Save user message
            user_msg = ChatMessage(
                session_id=request.session_id,
                role="user",
                content=request.message,
                image_data=request.image_data,
            )
            session.add(user_msg)

            # Save assistant message
            assistant_msg = ChatMessage(
                session_id=request.session_id,
                role="assistant",
                content=full_response,
                token_count=usage_data.get("output_tokens", 0) if usage_data else 0,
            )
            session.add(assistant_msg)

            # Log token usage
            if usage_data:
                token_log = TokenLog(
                    session_id=request.session_id,
                    model=settings.gemini_model,
                    input_tokens=usage_data.get("input_tokens", 0),
                    output_tokens=usage_data.get("output_tokens", 0),
                    image_count=1 if request.image_data else 0,
                    cost_usd=usage_data.get("cost_usd", 0),
                )
                session.add(token_log)

            await session.commit()

        # Send done event
        yield f"data: {json.dumps({'type': 'done', 'usage': usage_data})}\n\n"

    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"


@router.post("/stream")
async def stream_chat(request: ChatRequest):
    settings = get_settings()
    return StreamingResponse(
        generate_stream(request, settings),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@router.get("/history/{session_id}")
async def get_chat_history(session_id: str, limit: int = 50, session=Depends(get_session)):
    from sqlalchemy import select
    from app.db.models import ChatMessage

    stmt = (
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.id.desc())
        .limit(limit)
    )
    result = await session.execute(stmt)
    messages = result.scalars().all()

    return [
        {
            "id": msg.id,
            "role": msg.role,
            "content": msg.content,
            "has_image": bool(msg.image_data),
            "created_at": msg.created_at.isoformat(),
        }
        for msg in reversed(messages)
    ]
