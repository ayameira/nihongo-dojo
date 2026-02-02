"""Memory compaction service for chat sessions.

This service handles background compaction of chat history by:
1. Summarizing old messages into a session summary
2. Extracting permanent student facts for the student record
3. Archiving processed messages to reduce context window usage
"""

import logging
from typing import Optional, Dict, List
from datetime import datetime
from pydantic import BaseModel
from sqlalchemy import select, func, update

from app.db.database import async_session_maker
from app.db.models import ChatMessage, ChatSession, StudentFact
from app.config import get_settings, Settings
from app.core.gemini_client import GeminiClient

logger = logging.getLogger(__name__)


class CompactionResult(BaseModel):
    """Pydantic model for compaction output from Gemini."""

    new_summary: str
    new_student_facts: Optional[str] = None


COMPACTION_PROMPT_TEMPLATE = """You are the Memory Manager for Nihongo Dojo, a Japanese language tutoring application.

I will provide you with:
1. A 'Current Conversation Summary' (may be empty if this is the first compaction)
2. A 'Recent Chunk' of 10 messages from the conversation

## Task 1: Recursive Summarization
Update the 'Current Conversation Summary' to include the key events and topics from the 'Recent Chunk'.
- Keep it concise but specific
- Include details like grammar points practiced, vocabulary themes, corrections made
- Example: "User practiced Te-form verbs (tabete, nonde). Discussed travel plans to Tokyo. Corrected wa vs ga usage."

## Task 2: Fact Extraction
Did the user reveal any NEW permanent information about themselves in this chunk?
This includes:
- Biography (job, location, family)
- Language learning goals
- Interests and hobbies
- Dislikes or preferences
- Background context

If yes, extract it clearly. If no new facts, return null.

## Current Conversation Summary
{current_summary}

## Recent Chunk (10 messages)
{messages_chunk}

## Output Format
Return ONLY valid JSON:
{{"new_summary": "Updated comprehensive summary...", "new_student_facts": "New facts about the student..." or null}}"""


class MemoryService:
    """Handles background memory compaction for chat sessions."""

    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or get_settings()

    async def get_active_message_count(self, session_id: str) -> int:
        """Get the count of non-archived messages for a session."""
        async with async_session_maker() as session:
            stmt = (
                select(func.count(ChatMessage.id))
                .where(ChatMessage.session_id == session_id)
                .where(ChatMessage.is_archived == False)
            )
            result = await session.execute(stmt)
            return result.scalar_one()

    async def should_compact(self, session_id: str) -> bool:
        """Check if a session needs compaction (30+ active messages)."""
        count = await self.get_active_message_count(session_id)
        return count >= 30

    async def run_compaction(self, session_id: str) -> Dict:
        """
        Run the compaction process for a session.

        Returns a dict with compaction results or error info.
        """
        logger.info(f"Starting compaction for session {session_id}")

        try:
            # Step 1: Get oldest 10 non-archived messages
            messages = await self._get_oldest_active_messages(session_id, limit=10)

            if len(messages) < 10:
                logger.info(f"Not enough messages to compact ({len(messages)} found)")
                return {"status": "skipped", "reason": "insufficient_messages"}

            # Step 2: Get current session summary
            current_summary = await self._get_session_summary(session_id)

            # Step 3: Format messages for prompt
            messages_chunk = self._format_messages_for_prompt(messages)

            # Step 4: Call Gemini for compaction
            compaction_result = await self._call_gemini_for_compaction(
                current_summary, messages_chunk
            )

            # Step 5: Save new summary to ChatSession
            await self._save_session_summary(session_id, compaction_result.new_summary)

            # Step 6: If new student facts, add them to the database
            if compaction_result.new_student_facts:
                await self._add_student_facts(compaction_result.new_student_facts)

            # Step 7: Mark messages as archived (only after successful save)
            message_ids = [m.id for m in messages]
            await self._archive_messages(message_ids)

            logger.info(
                f"Compaction complete for session {session_id}: "
                f"archived {len(messages)} messages"
            )

            return {
                "status": "success",
                "archived_count": len(messages),
                "new_facts_extracted": compaction_result.new_student_facts is not None,
            }

        except Exception as e:
            logger.error(f"Compaction failed for session {session_id}: {e}")
            return {"status": "error", "error": str(e)}

    async def _get_oldest_active_messages(
        self, session_id: str, limit: int = 10
    ) -> List[ChatMessage]:
        """Get the oldest non-archived messages for a session."""
        async with async_session_maker() as session:
            stmt = (
                select(ChatMessage)
                .where(ChatMessage.session_id == session_id)
                .where(ChatMessage.is_archived == False)
                .order_by(ChatMessage.created_at.asc())
                .limit(limit)
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def _get_session_summary(self, session_id: str) -> str:
        """Get the current summary for a session, or empty string if none."""
        async with async_session_maker() as session:
            stmt = select(ChatSession.summary).where(ChatSession.id == session_id)
            result = await session.execute(stmt)
            summary = result.scalar_one_or_none()
            return summary or ""

    def _format_messages_for_prompt(self, messages: List[ChatMessage]) -> str:
        """Format messages into readable text for the prompt."""
        lines = []
        for msg in messages:
            role_label = "Student" if msg.role == "user" else "Tutor"
            # Truncate very long messages to avoid prompt bloat
            content = (
                msg.content[:500] + "..." if len(msg.content) > 500 else msg.content
            )
            lines.append(f"[{role_label}]: {content}")
        return "\n\n".join(lines)

    async def _call_gemini_for_compaction(
        self, current_summary: str, messages_chunk: str
    ) -> CompactionResult:
        """Call Gemini to generate compaction result."""
        client = GeminiClient(self.settings)

        prompt = COMPACTION_PROMPT_TEMPLATE.format(
            current_summary=current_summary
            or "(No previous summary - this is the first compaction)",
            messages_chunk=messages_chunk,
        )

        response = await client.generate_json(prompt)
        result_data = response["result"]

        # Validate with Pydantic
        return CompactionResult(**result_data)

    async def _save_session_summary(self, session_id: str, summary: str) -> None:
        """Save the new summary to the ChatSession."""
        async with async_session_maker() as session:
            stmt = (
                update(ChatSession)
                .where(ChatSession.id == session_id)
                .values(summary=summary, updated_at=datetime.now())
            )
            await session.execute(stmt)
            await session.commit()

    async def _add_student_facts(self, new_facts: str) -> None:
        """Add extracted facts to the student_facts table."""
        try:
            # Parse facts (expect newline or bullet-separated list)
            fact_lines = [
                line.strip().lstrip("- ").lstrip("* ").strip()
                for line in new_facts.split("\n")
                if line.strip() and not line.strip().startswith("#")
            ]

            added_count = 0
            async with async_session_maker() as session:
                for fact_text in fact_lines:
                    if not fact_text:
                        continue
                    # Check for duplicate before adding
                    stmt = select(StudentFact).where(StudentFact.content == fact_text)
                    existing = (await session.execute(stmt)).scalar_one_or_none()
                    if not existing:
                        session.add(StudentFact(content=fact_text, source="compaction"))
                        added_count += 1

                await session.commit()

            logger.info(f"Added {added_count} facts from compaction")
        except Exception as e:
            # Log but don't fail compaction - summary is more important
            logger.error(f"Failed to add student facts: {e}")

    async def _archive_messages(self, message_ids: List[int]) -> None:
        """Mark messages as archived."""
        async with async_session_maker() as session:
            stmt = (
                update(ChatMessage)
                .where(ChatMessage.id.in_(message_ids))
                .values(is_archived=True)
            )
            await session.execute(stmt)
            await session.commit()


async def run_compaction_if_needed(session_id: str) -> Optional[Dict]:
    """
    Check if compaction is needed and run it if so.

    This is the main entry point for background task integration.
    """
    service = MemoryService()

    if await service.should_compact(session_id):
        return await service.run_compaction(session_id)

    return None
