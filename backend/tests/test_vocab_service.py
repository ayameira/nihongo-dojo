"""
Tests for the vocabulary service.
"""
import pytest
from datetime import datetime

from app.services.vocab_service import (
    get_vocab_by_word,
    create_vocab,
    update_vocab_status,
    increment_seen,
    get_learning_vocab,
    search_vocab,
    get_vocab_stats,
)
from app.db.models import VocabEntry


class TestGetVocabByWord:
    """Tests for get_vocab_by_word function."""

    @pytest.mark.asyncio
    async def test_find_by_kanji_and_kana(self, async_session):
        """Test finding vocab by both kanji and kana."""
        entry = VocabEntry(
            kanji="食べる",
            kana="たべる",
            meaning="to eat",
            status="Learning",
        )
        async_session.add(entry)
        await async_session.commit()

        result = await get_vocab_by_word(async_session, "食べる", "たべる")

        assert result is not None
        assert result.kanji == "食べる"
        assert result.kana == "たべる"

    @pytest.mark.asyncio
    async def test_find_by_kana_only(self, async_session):
        """Test finding kana-only word."""
        entry = VocabEntry(
            kanji=None,
            kana="これ",
            meaning="this",
            status="New",
        )
        async_session.add(entry)
        await async_session.commit()

        result = await get_vocab_by_word(async_session, None, "これ")

        assert result is not None
        assert result.kana == "これ"

    @pytest.mark.asyncio
    async def test_returns_none_when_not_found(self, async_session):
        """Test that None is returned for non-existent word."""
        result = await get_vocab_by_word(async_session, "存在しない", "そんざいしない")
        assert result is None


class TestCreateVocab:
    """Tests for create_vocab function."""

    @pytest.mark.asyncio
    async def test_create_with_all_fields(self, async_session):
        """Test creating vocab with all fields."""
        entry = await create_vocab(
            async_session,
            kanji="走る",
            kana="はしる",
            meaning="to run",
            pos="verb",
            source="tutor",
        )

        assert entry.id is not None
        assert entry.kanji == "走る"
        assert entry.kana == "はしる"
        assert entry.meaning == "to run"
        assert entry.pos == "verb"
        assert entry.source == "tutor"
        assert entry.status == "New"

    @pytest.mark.asyncio
    async def test_create_with_defaults(self, async_session):
        """Test creating vocab with default values."""
        entry = await create_vocab(
            async_session,
            kanji=None,
            kana="あれ",
            meaning="that",
        )

        assert entry.source == "manual"
        assert entry.status == "New"
        assert entry.pos is None

    @pytest.mark.asyncio
    async def test_create_persists_to_database(self, async_session):
        """Test that created entry is persisted."""
        from sqlalchemy import select

        await create_vocab(async_session, None, "テスト", "test")

        stmt = select(VocabEntry).where(VocabEntry.kana == "テスト")
        result = await async_session.execute(stmt)
        found = result.scalar_one_or_none()

        assert found is not None
        assert found.meaning == "test"


class TestUpdateVocabStatus:
    """Tests for update_vocab_status function."""

    @pytest.mark.asyncio
    async def test_update_status(self, async_session):
        """Test updating vocab status."""
        entry = VocabEntry(kana="テスト", meaning="test", status="New")
        async_session.add(entry)
        await async_session.commit()

        result = await update_vocab_status(async_session, entry.id, "Learning")

        assert result is not None
        assert result.status == "Learning"

    @pytest.mark.asyncio
    async def test_update_nonexistent_returns_none(self, async_session):
        """Test updating non-existent entry returns None."""
        result = await update_vocab_status(async_session, 99999, "Learning")
        assert result is None


class TestIncrementSeen:
    """Tests for increment_seen function."""

    @pytest.mark.asyncio
    async def test_increment_times_seen(self, async_session):
        """Test incrementing times_seen counter."""
        entry = VocabEntry(
            kana="テスト",
            meaning="test",
            times_seen=5,
        )
        async_session.add(entry)
        await async_session.commit()

        result = await increment_seen(async_session, entry.id)

        assert result.times_seen == 6

    @pytest.mark.asyncio
    async def test_sets_last_seen_at(self, async_session):
        """Test that last_seen_at is updated."""
        entry = VocabEntry(
            kana="テスト",
            meaning="test",
            last_seen_at=None,
        )
        async_session.add(entry)
        await async_session.commit()

        result = await increment_seen(async_session, entry.id)

        assert result.last_seen_at is not None
        assert isinstance(result.last_seen_at, datetime)

    @pytest.mark.asyncio
    async def test_increment_nonexistent_returns_none(self, async_session):
        """Test incrementing non-existent entry returns None."""
        result = await increment_seen(async_session, 99999)
        assert result is None


class TestGetLearningVocab:
    """Tests for get_learning_vocab function."""

    @pytest.mark.asyncio
    async def test_returns_only_learning_status(self, async_session):
        """Test that only Learning status entries are returned."""
        entries = [
            VocabEntry(kana="one", meaning="1", status="New"),
            VocabEntry(kana="two", meaning="2", status="Learning"),
            VocabEntry(kana="three", meaning="3", status="Mature"),
            VocabEntry(kana="four", meaning="4", status="Learning"),
        ]
        for e in entries:
            async_session.add(e)
        await async_session.commit()

        result = await get_learning_vocab(async_session)

        assert len(result) == 2
        assert all(e.status == "Learning" for e in result)

    @pytest.mark.asyncio
    async def test_respects_limit(self, async_session):
        """Test that limit parameter is respected."""
        for i in range(10):
            async_session.add(VocabEntry(kana=f"word{i}", meaning=str(i), status="Learning"))
        await async_session.commit()

        result = await get_learning_vocab(async_session, limit=5)

        assert len(result) == 5

    @pytest.mark.asyncio
    async def test_returns_empty_when_none(self, async_session):
        """Test returns empty list when no Learning entries."""
        async_session.add(VocabEntry(kana="test", meaning="test", status="New"))
        await async_session.commit()

        result = await get_learning_vocab(async_session)

        assert result == []


class TestSearchVocab:
    """Tests for search_vocab function."""

    @pytest.mark.asyncio
    async def test_search_by_kanji(self, async_session):
        """Test searching by kanji."""
        async_session.add(VocabEntry(kanji="食べる", kana="たべる", meaning="to eat"))
        async_session.add(VocabEntry(kanji="飲む", kana="のむ", meaning="to drink"))
        await async_session.commit()

        result = await search_vocab(async_session, "食べ")

        assert len(result) == 1
        assert result[0].kanji == "食べる"

    @pytest.mark.asyncio
    async def test_search_by_kana(self, async_session):
        """Test searching by kana."""
        async_session.add(VocabEntry(kana="たべる", meaning="to eat"))
        async_session.add(VocabEntry(kana="のむ", meaning="to drink"))
        await async_session.commit()

        result = await search_vocab(async_session, "たべ")

        assert len(result) == 1
        assert result[0].kana == "たべる"

    @pytest.mark.asyncio
    async def test_search_by_meaning(self, async_session):
        """Test searching by meaning."""
        async_session.add(VocabEntry(kana="たべる", meaning="to eat"))
        async_session.add(VocabEntry(kana="のむ", meaning="to drink"))
        await async_session.commit()

        result = await search_vocab(async_session, "eat")

        assert len(result) == 1
        assert "eat" in result[0].meaning

    @pytest.mark.asyncio
    async def test_search_respects_limit(self, async_session):
        """Test that search respects limit parameter."""
        for i in range(20):
            async_session.add(VocabEntry(kana=f"test{i}", meaning=f"meaning{i}"))
        await async_session.commit()

        result = await search_vocab(async_session, "test", limit=5)

        assert len(result) == 5


class TestGetVocabStats:
    """Tests for get_vocab_stats function."""

    @pytest.mark.asyncio
    async def test_returns_all_counts(self, async_session):
        """Test that stats include all status counts."""
        entries = [
            VocabEntry(kana="a", meaning="a", status="New"),
            VocabEntry(kana="b", meaning="b", status="New"),
            VocabEntry(kana="c", meaning="c", status="Learning"),
            VocabEntry(kana="d", meaning="d", status="Learning"),
            VocabEntry(kana="e", meaning="e", status="Learning"),
            VocabEntry(kana="f", meaning="f", status="Mature"),
        ]
        for e in entries:
            async_session.add(e)
        await async_session.commit()

        stats = await get_vocab_stats(async_session)

        assert stats["new"] == 2
        assert stats["learning"] == 3
        assert stats["mature"] == 1
        assert stats["total"] == 6

    @pytest.mark.asyncio
    async def test_returns_zeros_when_empty(self, async_session):
        """Test that stats return zeros for empty database."""
        stats = await get_vocab_stats(async_session)

        assert stats["new"] == 0
        assert stats["learning"] == 0
        assert stats["mature"] == 0
        assert stats["total"] == 0
