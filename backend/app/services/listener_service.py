"""Listener agent service for background fact extraction.

This service analyzes user messages in the background to extract and manage
student facts without blocking the main Tutor response.
"""

import logging
from typing import Optional, Dict

from app.config import get_settings, Settings, resolve_provider_settings
from app.core.context_builder import build_listener_context
from app.core.llm_client import get_llm_client, is_llm_configured
from app.core.tools import execute_tool_call

logger = logging.getLogger(__name__)


class ListenerService:
    """Background listener for extracting student facts from messages."""

    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or get_settings()

    async def process_message(
        self,
        session_id: str,
        user_message: str,
        tutor_message: str,
        provider: Optional[str] = None,
        model: Optional[str] = None,
    ) -> Dict:
        """Analyze user message and extract/update facts if needed.

        Args:
            session_id: The chat session ID (for logging)
            user_message: The student's message
            tutor_message: The tutor's previous response (for pronoun resolution)

        Returns:
            Dict with status, tool_calls made, and usage info
        """
        logger.info(f"Listener processing message for session {session_id}")

        try:
            llm_settings = resolve_provider_settings(self.settings, provider, model)

            if not is_llm_configured(llm_settings):
                logger.warning("Listener skipped because LLM is not configured")
                return {"status": "skipped", "reason": "llm_not_configured"}

            # Build minimal context for Listener
            context = await build_listener_context(
                user_message=user_message,
                tutor_message=tutor_message,
            )

            # Initialize configured LLM client and run with tool loop
            client = get_llm_client(llm_settings)
            result = await client.generate_with_tools(
                context=context,
                tool_executor=execute_tool_call,
            )

            tool_calls = result.get("tool_calls", [])
            usage = result.get("usage", {})

            logger.info(
                f"Listener completed for session {session_id}: "
                f"{len(tool_calls)} tool calls, "
                f"usage: {usage.get('input_tokens', 0)} in / {usage.get('output_tokens', 0)} out"
            )

            return {
                "status": "success",
                "tool_calls": tool_calls,
                "usage": usage,
            }

        except Exception as e:
            logger.error(f"Listener failed for session {session_id}: {e}")
            return {
                "status": "error",
                "error": str(e),
            }


async def run_listener(
    session_id: str,
    user_message: str,
    tutor_message: str,
    provider: Optional[str] = None,
    model: Optional[str] = None,
) -> Dict:
    """Entry point for background task integration.

    Args:
        session_id: The chat session ID
        user_message: The student's message
        tutor_message: The tutor's previous response (for pronoun resolution)

    Returns:
        Dict with status and results
    """
    service = ListenerService()
    return await service.process_message(
        session_id,
        user_message,
        tutor_message,
        provider,
        model,
    )
