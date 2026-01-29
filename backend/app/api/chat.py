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
    from app.db.models import ChatMessage, TokenLog, ChatSession
    from app.services.request_logger import RequestLogger
    from sqlalchemy import select

    request_logger = RequestLogger(settings.ai_logs_path)

    if not settings.gemini_api_key:
        await request_logger.log_error(
            session_id=request.session_id,
            user_message=request.message,
            error="Gemini API key not configured",
        )
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
            # Get or create ChatSession
            stmt = select(ChatSession).where(ChatSession.id == request.session_id)
            result = await session.execute(stmt)
            chat_session = result.scalar_one_or_none()

            if not chat_session:
                # Create new session with preview from first message
                preview = request.message[:100] if request.message else None
                chat_session = ChatSession(
                    id=request.session_id,
                    preview=preview,
                    message_count=0,
                )
                session.add(chat_session)

            # Update session metadata
            chat_session.message_count += 2  # user + assistant
            from datetime import datetime
            chat_session.updated_at = datetime.now()

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

        # Log the complete interaction to disk
        raw_context = context.get("_raw", {})
        await request_logger.log_interaction(
            session_id=request.session_id,
            user_message=request.message,
            image_data=request.image_data,
            difficulty_feedback=request.difficulty_feedback,
            system_prompt=context.get("system_prompt", ""),
            chat_history=context.get("chat_history", []),
            class_notes_content=raw_context.get("class_notes", ""),
            student_record_content=raw_context.get("student_record", ""),
            vocab_list=raw_context.get("vocab_list", []),
            full_response=full_response,
            tool_calls=tool_calls,
            usage_data=usage_data,
            model=settings.gemini_model,
        )

        # Send done event
        yield f"data: {json.dumps({'type': 'done', 'usage': usage_data})}\n\n"

    except Exception as e:
        # Log the error
        raw_context = context.get("_raw", {}) if 'context' in dir() else {}
        await request_logger.log_interaction(
            session_id=request.session_id,
            user_message=request.message,
            image_data=request.image_data,
            difficulty_feedback=request.difficulty_feedback,
            system_prompt=context.get("system_prompt", "") if 'context' in dir() else "",
            chat_history=context.get("chat_history", []) if 'context' in dir() else [],
            class_notes_content=raw_context.get("class_notes", ""),
            student_record_content=raw_context.get("student_record", ""),
            vocab_list=raw_context.get("vocab_list", []),
            full_response=full_response if 'full_response' in dir() else "",
            tool_calls=tool_calls if 'tool_calls' in dir() else [],
            usage_data=usage_data if 'usage_data' in dir() else None,
            model=settings.gemini_model,
            error=str(e),
        )
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
