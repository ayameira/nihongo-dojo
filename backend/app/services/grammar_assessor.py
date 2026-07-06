"""Background grammar assessment service.

Evaluates student's use of grammar points across conversations.
Uses a pre-filtering approach for token efficiency:
1. For each "Learning" grammar point, search messages for usage patterns
2. Only send relevant excerpts to AI for evaluation
3. Track when each grammar point was last assessed to avoid re-processing
"""

import logging
import re
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from sqlalchemy import select, update, and_

from app.db.database import async_session_maker
from app.db.models import GrammarEntry, ChatMessage, ChatSession
from app.config import get_settings, Settings, resolve_provider_settings
from app.core.language_profiles import get_language_profile, normalize_language_code

logger = logging.getLogger(__name__)

# Only re-assess grammar every N hours
ASSESSMENT_COOLDOWN_HOURS = 24
# Minimum relevant messages needed before sending to AI
MIN_RELEVANT_MESSAGES = 3
# Maximum messages to send per grammar point (token budget)
MAX_MESSAGES_PER_POINT = 10
# Maximum grammar points to assess per run
MAX_GRAMMAR_PER_RUN = 20


ASSESSMENT_PROMPT_TEMPLATE = get_language_profile("ja").grammar_assessment_prompt_template


class GrammarAssessor:
    """Token-efficient grammar assessment using pre-filtering."""

    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or get_settings()

    def with_provider(
        self,
        provider: Optional[str] = None,
        model: Optional[str] = None,
    ) -> "GrammarAssessor":
        return GrammarAssessor(resolve_provider_settings(self.settings, provider, model))

    async def run_assessment(self, language_code: Optional[str] = None) -> Dict:
        """Main entry point. Assess all eligible grammar points."""
        language_code = normalize_language_code(language_code or self.settings.target_language_code)

        # 1. Get "Learning" grammar points that haven't been assessed recently
        grammar_points = await self._get_assessable_grammar(language_code)

        if not grammar_points:
            logger.info("No grammar points need assessment")
            return {"status": "skipped", "reason": "no_eligible_points"}

        # 2. For each grammar point, grep recent messages for relevant usage
        assessable_groups = []
        for grammar in grammar_points:
            relevant_messages = await self._find_relevant_messages(grammar, language_code)
            if len(relevant_messages) >= MIN_RELEVANT_MESSAGES:
                assessable_groups.append({
                    "grammar": grammar,
                    "messages": relevant_messages[:MAX_MESSAGES_PER_POINT],
                })

        if not assessable_groups:
            logger.info("No grammar points have enough relevant messages for assessment")
            # Still update last_assessed_at to avoid re-checking too soon
            await self._update_assessed_timestamps([g["id"] for g in grammar_points])
            return {"status": "skipped", "reason": "insufficient_usage_data"}

        # 3. Batch assessable grammar points and send to AI
        # Group into batches of ~5 to keep prompt size manageable
        batch_size = 5
        all_assessments = []

        for i in range(0, len(assessable_groups), batch_size):
            batch = assessable_groups[i:i + batch_size]
            assessments = await self._assess_batch(batch, language_code)
            all_assessments.extend(assessments)

        # 4. Apply status changes based on AI recommendations
        changes_made = await self._apply_assessments(all_assessments)

        # 5. Update assessed timestamps for all checked grammar points
        all_grammar_ids = [g["id"] for g in grammar_points]
        await self._update_assessed_timestamps(all_grammar_ids)

        return {
            "status": "success",
            "assessed_count": len(all_assessments),
            "changes_made": changes_made,
        }

    async def _get_assessable_grammar(self, language_code: str) -> List[Dict]:
        """Get Learning grammar points not assessed in the cooldown period."""
        cutoff = datetime.now() - timedelta(hours=ASSESSMENT_COOLDOWN_HOURS)

        async with async_session_maker() as session:
            stmt = (
                select(GrammarEntry)
                .where(GrammarEntry.status == "Learning")
                .where(GrammarEntry.language_code == language_code)
                .where(
                    (GrammarEntry.last_assessed_at == None) |
                    (GrammarEntry.last_assessed_at < cutoff)
                )
                .order_by(GrammarEntry.last_assessed_at.asc().nullsfirst())
                .limit(MAX_GRAMMAR_PER_RUN)
            )
            result = await session.execute(stmt)
            entries = result.scalars().all()

            return [
                {
                    "id": e.id,
                    "pattern": e.pattern,
                    "meaning": e.meaning,
                    "jlpt_level": e.jlpt_level,
                    "times_seen": e.times_seen,
                    "times_correct": e.times_correct,
                }
                for e in entries
            ]

    async def _find_relevant_messages(self, grammar: Dict, language_code: str) -> List[Dict]:
        """Search recent messages for usage of a grammar pattern.

        This is the token-efficient pre-filtering step: we search the database
        for messages containing the grammar pattern using SQL LIKE, rather than
        sending all messages to AI.
        """
        pattern = grammar["pattern"]

        # Build search patterns for SQL LIKE
        # Strip numeric disambiguators (e.g., "が 1" -> "が")
        clean_pattern = re.sub(r'\s*\d+$', '', pattern).strip()

        # Remove ○○ placeholders for search
        search_term = clean_pattern.replace("○○", "")

        if not search_term or len(search_term) < 2:
            return []

        async with async_session_maker() as session:
            # Search in user messages (student's usage) across all sessions
            # Look at messages from the last 30 days
            cutoff = datetime.now() - timedelta(days=30)

            stmt = (
                select(ChatMessage)
                .join(ChatSession, ChatSession.id == ChatMessage.session_id)
                .where(ChatMessage.role == "user")
                .where(ChatMessage.content.like(f"%{search_term}%"))
                .where(ChatMessage.created_at > cutoff)
                .where(ChatSession.language_code == language_code)
                .order_by(ChatMessage.created_at.desc())
                .limit(MAX_MESSAGES_PER_POINT)
            )
            result = await session.execute(stmt)
            messages = result.scalars().all()

            return [
                {
                    "role": m.role,
                    "content": m.content[:300],  # Truncate for token efficiency
                    "session_id": m.session_id,
                    "created_at": m.created_at.isoformat() if m.created_at else "",
                }
                for m in messages
            ]

    async def _assess_batch(self, batch: List[Dict], language_code: str) -> List[Dict]:
        """Send a batch of grammar points with their relevant messages to AI."""
        from app.core.llm_client import get_llm_client, is_llm_configured

        profile = get_language_profile(language_code)
        scheme_name = profile.grammar_level_scheme.name

        # Format grammar points
        grammar_text = "\n".join(
            f"- [ID: {g['grammar']['id']}] {g['grammar']['pattern']} "
            f"({g['grammar']['meaning']}) [{scheme_name}: {g['grammar'].get('jlpt_level') or 'custom'}]"
            for g in batch
        )

        # Format excerpts grouped by grammar point
        excerpts_parts = []
        for g in batch:
            excerpts_parts.append(f"\n### Excerpts for: {g['grammar']['pattern']}")
            for msg in g["messages"]:
                excerpts_parts.append(f"[Student]: {msg['content']}")
        excerpts_text = "\n".join(excerpts_parts)

        prompt = profile.grammar_assessment_prompt_template.format(
            grammar_points=grammar_text,
            excerpts=excerpts_text,
        )

        try:
            if not is_llm_configured(self.settings):
                logger.warning("Grammar assessment skipped because LLM is not configured")
                return []

            client = get_llm_client(self.settings)
            response = await client.generate_json(prompt)
            result = response.get("result", {})
            return result.get("assessments", [])
        except Exception as e:
            logger.error(f"Grammar assessment AI call failed: {e}")
            return []

    async def _apply_assessments(self, assessments: List[Dict]) -> int:
        """Apply AI assessment recommendations to grammar point statuses."""
        changes = 0

        async with async_session_maker() as session:
            for assessment in assessments:
                grammar_id = assessment.get("grammar_id")
                recommendation = assessment.get("recommendation")

                if not grammar_id or not recommendation:
                    continue

                stmt = select(GrammarEntry).where(GrammarEntry.id == grammar_id)
                entry = (await session.execute(stmt)).scalar_one_or_none()

                if not entry:
                    continue

                new_status = None
                if recommendation == "promote_to_burned" and entry.status == "Learning":
                    new_status = "Burned"
                elif recommendation == "demote_to_new" and entry.status == "Learning":
                    new_status = "New"

                if new_status:
                    entry.status = new_status
                    changes += 1
                    logger.info(
                        f"Grammar assessment: '{entry.pattern}' "
                        f"{entry.status} -> {new_status} "
                        f"(reason: {assessment.get('reasoning', 'N/A')})"
                    )

                # Update tracking stats from AI assessment
                times_correct = assessment.get("times_used_correctly", 0)
                times_incorrect = assessment.get("times_used_incorrectly", 0)
                entry.times_seen = times_correct + times_incorrect
                entry.times_correct = times_correct

            await session.commit()

        return changes

    async def _update_assessed_timestamps(self, grammar_ids: List[int]) -> None:
        """Mark grammar points as recently assessed."""
        if not grammar_ids:
            return

        async with async_session_maker() as session:
            stmt = (
                update(GrammarEntry)
                .where(GrammarEntry.id.in_(grammar_ids))
                .values(last_assessed_at=datetime.now())
            )
            await session.execute(stmt)
            await session.commit()


async def run_grammar_assessment(
    provider: Optional[str] = None,
    model: Optional[str] = None,
    language_code: Optional[str] = None,
) -> Optional[Dict]:
    """Entry point for background task integration."""
    try:
        assessor = GrammarAssessor().with_provider(provider, model)
        return await assessor.run_assessment(language_code)
    except Exception as e:
        logger.error(f"Grammar assessment failed: {e}")
        return {"status": "error", "error": str(e)}
