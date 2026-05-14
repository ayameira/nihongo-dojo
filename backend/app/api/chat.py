from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
import json
import asyncio
import logging

from app.db.database import get_session
from app.config import get_available_models, get_settings, resolve_provider_settings
from app.core.llm_client import get_llm_client, is_llm_configured, missing_llm_message

router = APIRouter()
logger = logging.getLogger(__name__)


async def generate_session_title(
    session_id: str,
    first_message: str,
    provider: Optional[str] = None,
    model: Optional[str] = None,
):
    """Generate a short title for the chat session based on the first message.

    Runs as a background task after the first message in a session.
    """
    from app.db.database import async_session_maker
    from app.db.models import ChatSession
    from sqlalchemy import select

    settings = get_settings()

    title_settings = resolve_provider_settings(settings, provider, model)

    if not is_llm_configured(title_settings):
        logger.warning("No LLM API key, skipping title generation")
        return

    try:
        client = get_llm_client(title_settings)

        # Truncate message for prompt efficiency
        message_preview = first_message[:500] if len(first_message) > 500 else first_message

        prompt = f"""Generate a very short title (3-6 words) for a Japanese learning chat session that starts with this message:

"{message_preview}"

The title should:
- Be in English
- Capture the main topic or question
- Be concise and descriptive
- Not include quotes or punctuation at the end

Return JSON: {{"title": "your title here"}}"""

        result = await client.generate_json(prompt)
        title = result.get("result", {}).get("title", "").strip()

        if not title:
            logger.warning(f"Empty title generated for session {session_id}")
            return

        # Update the session with the generated title
        async with async_session_maker() as session:
            stmt = select(ChatSession).where(ChatSession.id == session_id)
            db_result = await session.execute(stmt)
            chat_session = db_result.scalar_one_or_none()

            if chat_session and not chat_session.name:
                chat_session.name = title[:200]  # Respect max length
                await session.commit()
                logger.info(f"Generated title for session {session_id}: {title}")

    except Exception as e:
        logger.error(f"Failed to generate title for session {session_id}: {e}")


class ChatRequest(BaseModel):
    message: str
    image_data: Optional[str] = None
    session_id: str
    difficulty_feedback: Optional[str] = None  # 'too_hard' | 'too_easy'
    model: Optional[str] = None
    provider: Optional[str] = None


async def generate_stream(request: ChatRequest, settings, background_tasks: BackgroundTasks):
    """Generate SSE stream for chat response."""
    from app.core.context_builder import build_tutor_context
    from app.db.database import async_session_maker
    from app.db.models import ChatMessage, TokenLog, ChatSession
    from app.services.request_logger import RequestLogger
    from app.services.memory_service import run_compaction_if_needed
    from app.services.listener_service import run_listener
    from app.services.grammar_assessor import run_grammar_assessment
    from sqlalchemy import select

    request_logger = RequestLogger(settings.ai_logs_path)
    chat_settings = resolve_provider_settings(settings, request.provider, request.model)

    if not is_llm_configured(chat_settings):
        error_message = missing_llm_message(chat_settings)
        await request_logger.log_error(
            session_id=request.session_id,
            user_message=request.message,
            error=error_message,
        )
        yield f"data: {json.dumps({'type': 'error', 'content': error_message})}\n\n"
        return

    try:
        client = get_llm_client(chat_settings)
        chat_model = chat_settings.llm_model

        # Build context for Tutor agent (no tool instructions)
        context = await build_tutor_context(request.session_id, request.difficulty_feedback)

        # Prepare message parts
        parts = [request.message]
        if request.image_data:
            parts.append({"mime_type": "image/jpeg", "data": request.image_data})

        # Stream response from Tutor agent (no tools)
        full_response = ""
        usage_data = None

        # Create callback to log exact LLM payloads
        async def log_payload(payload):
            await request_logger.log_llm_payload(request.session_id, payload)

        async for chunk in client.stream_chat(
            context, parts,
            tool_executor=None,
            request_logger=log_payload,
            use_tools=False,  # Tutor agent has no tools
            model_name=chat_model,
        ):
            if chunk["type"] == "text":
                full_response += chunk["content"]
                yield f"data: {json.dumps(chunk)}\n\n"
            elif chunk["type"] == "usage":
                usage_data = chunk

        # Save to database
        async with async_session_maker() as session:
            # Get or create ChatSession
            stmt = select(ChatSession).where(ChatSession.id == request.session_id)
            result = await session.execute(stmt)
            chat_session = result.scalar_one_or_none()

            is_first_message = False
            if not chat_session:
                # Create new session with preview from first message
                preview = request.message[:100] if request.message else None
                chat_session = ChatSession(
                    id=request.session_id,
                    preview=preview,
                    message_count=0,
                )
                session.add(chat_session)
                is_first_message = True
            elif not chat_session.preview and request.message:
                # Set preview if this is the first message in an existing session
                chat_session.preview = request.message[:100]
                is_first_message = True

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
                    model=chat_model,
                    input_tokens=usage_data.get("input_tokens", 0),
                    output_tokens=usage_data.get("output_tokens", 0),
                    image_count=1 if request.image_data else 0,
                    cost_usd=usage_data.get("cost_usd", 0),
                )
                session.add(token_log)

            await session.commit()

            # Schedule Listener agent to extract facts in background
            background_tasks.add_task(
                run_listener,
                request.session_id,
                request.message,  # user message
                full_response,    # tutor's response (for pronoun resolution)
                chat_settings.llm_provider,
                chat_model,
            )

            # Schedule memory compaction check as background task (non-blocking)
            background_tasks.add_task(
                run_compaction_if_needed,
                request.session_id,
                chat_settings.llm_provider,
                chat_model,
            )

            # Schedule grammar assessment every 20 messages
            if chat_session.message_count % 20 == 0:
                background_tasks.add_task(
                    run_grammar_assessment,
                    chat_settings.llm_provider,
                    chat_model,
                )

            # Generate title for new sessions
            if is_first_message:
                background_tasks.add_task(
                    generate_session_title,
                    request.session_id,
                    request.message,
                    chat_settings.llm_provider,
                    chat_model,
                )

        # Log the complete interaction to disk
        raw_context = context.get("_raw", {})
        await request_logger.log_interaction(
            session_id=request.session_id,
            user_message=request.message,
            image_data=request.image_data,
            difficulty_feedback=request.difficulty_feedback,
            system_prompt=context.get("system_prompt", ""),
            chat_history=context.get("chat_history", []),
            student_record_content=raw_context.get("student_record", ""),
            vocab_list=raw_context.get("vocab_list", []),
            full_response=full_response,
            tool_calls=[],  # Tutor agent has no tools
            usage_data=usage_data,
            model=chat_model,
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
            student_record_content=raw_context.get("student_record", ""),
            vocab_list=raw_context.get("vocab_list", []),
            full_response=full_response if 'full_response' in dir() else "",
            tool_calls=[],  # Tutor agent has no tools
            usage_data=usage_data if 'usage_data' in dir() else None,
            model=chat_model if 'chat_model' in dir() else chat_settings.llm_model,
            error=str(e),
        )
        yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"


@router.post("/stream")
async def stream_chat(
    request: ChatRequest,
    background_tasks: BackgroundTasks,
    settings=Depends(get_settings),
):
    provider = request.provider or settings.llm_provider
    available_models = get_available_models(provider)
    if (
        request.model
        and request.model not in available_models
        and request.model != resolve_provider_settings(settings, provider).llm_model
    ):
        raise HTTPException(status_code=400, detail="Unknown chat model")

    return StreamingResponse(
        generate_stream(request, settings, background_tasks),
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
