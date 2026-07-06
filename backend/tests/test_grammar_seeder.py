"""
Tests for per-language grammar seeding.
"""
import pytest
from sqlalchemy import select, func

from app.db.models import GrammarEntry
from app.services.grammar_seeder import check_and_seed_all_grammar


class TestCheckAndSeedAllGrammar:
    @pytest.mark.asyncio
    async def test_seeds_only_profiles_with_seed_files(self, async_session):
        result = await check_and_seed_all_grammar(async_session)

        # Japanese ships a JLPT seed file; the generic profiles start empty.
        assert result["count"] > 0
        non_ja = await async_session.scalar(
            select(func.count()).where(GrammarEntry.language_code != "ja")
        )
        assert non_ja == 0
        ja = await async_session.scalar(
            select(func.count()).where(GrammarEntry.language_code == "ja")
        )
        assert ja == result["count"]

    @pytest.mark.asyncio
    async def test_reseeding_is_a_no_op(self, async_session):
        first = await check_and_seed_all_grammar(async_session)
        assert first["count"] > 0

        second = await check_and_seed_all_grammar(async_session)
        assert second["count"] == 0
