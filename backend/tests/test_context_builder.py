"""
Tests for the context builder module.
"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from datetime import date

from app.core.context_builder import (
    build_tutor_context,
    build_listener_context,
    fetch_learning_vocab,
    fetch_student_facts,
    format_vocab_list,
    format_student_facts,
    get_chat_history,
)
from app.core.agents import TUTOR_SYSTEM_PROMPT_TEMPLATE, LISTENER_SYSTEM_PROMPT_TEMPLATE


class TestFormatVocabList:
    """Tests for format_vocab_list function."""

    def test_formats_vocab_with_kanji(self):
        """Test formatting vocabulary with kanji."""
        vocab = [
            {"kanji": "食べる", "kana": "たべる", "meaning": "to eat", "pos": "verb"},
            {"kanji": "飲む", "kana": "のむ", "meaning": "to drink", "pos": "verb"},
        ]

        result = format_vocab_list(vocab)

        assert "食べる (たべる)" in result
        assert "飲む (のむ)" in result

    def test_formats_kana_only_vocab(self):
        """Test formatting vocabulary without kanji."""
        vocab = [
            {"kanji": None, "kana": "これ", "meaning": "this", "pos": "other"},
        ]

        result = format_vocab_list(vocab)

        assert "- これ" in result
        # Should not have parentheses for kana-only
        assert "(これ)" not in result

    def test_returns_empty_for_empty_list(self):
        """Test that empty list returns empty string."""
        result = format_vocab_list([])
        assert result == ""

    def test_formats_multiple_entries(self):
        """Test formatting multiple entries with line breaks."""
        vocab = [
            {"kanji": "一", "kana": "いち", "meaning": "one", "pos": "noun"},
            {"kanji": "二", "kana": "に", "meaning": "two", "pos": "noun"},
            {"kanji": "三", "kana": "さん", "meaning": "three", "pos": "noun"},
        ]

        result = format_vocab_list(vocab)
        lines = result.strip().split("\n")

        assert len(lines) == 3
        assert all(line.startswith("- ") for line in lines)


class TestFormatStudentFacts:
    """Tests for format_student_facts function."""

    def test_formats_facts_with_ids(self):
        """Test formatting facts with IDs in brackets."""
        facts = [
            {"id": 1, "content": "Likes anime"},
            {"id": 2, "content": "Learning for travel"}
        ]
        result = format_student_facts(facts)

        assert "- [1] Likes anime" in result
        assert "- [2] Learning for travel" in result

    def test_returns_placeholder_for_empty(self):
        """Test that empty facts return placeholder."""
        result = format_student_facts([])
        assert "No information recorded yet" in result


class TestFetchLearningVocab:
    """Tests for fetch_learning_vocab function."""

    @pytest.mark.asyncio
    async def test_fetches_learning_vocab(self, async_session):
        """Test fetching vocabulary with Learning status."""
        from app.db.models import VocabEntry

        # Add test vocab
        async_session.add(VocabEntry(kanji="学ぶ", kana="まなぶ", meaning="to learn", pos="verb", status="Learning"))
        async_session.add(VocabEntry(kana="これ", meaning="this", status="New"))
        await async_session.commit()

        # Mock async_session_maker
        mock_session_maker = MagicMock()
        mock_session_maker.return_value.__aenter__ = AsyncMock(return_value=async_session)
        mock_session_maker.return_value.__aexit__ = AsyncMock(return_value=None)

        with patch('app.db.database.async_session_maker', mock_session_maker):
            result = await fetch_learning_vocab()

        assert len(result) == 1
        assert result[0]["kanji"] == "学ぶ"
        assert result[0]["kana"] == "まなぶ"

    @pytest.mark.asyncio
    async def test_returns_empty_on_error(self):
        """Test that errors return empty list."""
        with patch('app.db.database.async_session_maker', side_effect=Exception("DB Error")):
            result = await fetch_learning_vocab()

        assert result == []


class TestFetchStudentFacts:
    """Tests for fetch_student_facts function."""

    @pytest.mark.asyncio
    async def test_fetches_all_facts_with_ids(self, async_engine):
        """Test fetching all student facts with IDs."""
        from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
        from app.db.models import StudentFact

        session_maker = async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

        async with session_maker() as session:
            session.add(StudentFact(content="Likes anime", source="tutor"))
            session.add(StudentFact(content="Learning for travel", source="compaction"))
            await session.commit()

        with patch('app.db.database.async_session_maker', session_maker):
            result = await fetch_student_facts()

        assert len(result) == 2
        # Check that results are dicts with id and content
        assert all("id" in f and "content" in f for f in result)
        contents = [f["content"] for f in result]
        assert "Likes anime" in contents
        assert "Learning for travel" in contents

    @pytest.mark.asyncio
    async def test_returns_empty_on_error(self):
        """Test that errors return empty list."""
        with patch('app.db.database.async_session_maker', side_effect=Exception("DB Error")):
            result = await fetch_student_facts()

        assert result == []


class TestGetChatHistory:
    """Tests for get_chat_history function."""

    @pytest.mark.asyncio
    async def test_fetches_chat_history(self, async_session, sample_session, sample_messages):
        """Test fetching chat history."""
        mock_session_maker = MagicMock()
        mock_session_maker.return_value.__aenter__ = AsyncMock(return_value=async_session)
        mock_session_maker.return_value.__aexit__ = AsyncMock(return_value=None)

        with patch('app.db.database.async_session_maker', mock_session_maker):
            result = await get_chat_history(sample_session.id)

        assert len(result) == 2
        assert result[0]["role"] == "user"
        assert result[1]["role"] == "model"  # assistant -> model

    @pytest.mark.asyncio
    async def test_returns_chronological_order(self, async_session, sample_session, sample_messages):
        """Test that history is returned in chronological order."""
        mock_session_maker = MagicMock()
        mock_session_maker.return_value.__aenter__ = AsyncMock(return_value=async_session)
        mock_session_maker.return_value.__aexit__ = AsyncMock(return_value=None)

        with patch('app.db.database.async_session_maker', mock_session_maker):
            result = await get_chat_history(sample_session.id)

        # First message should be from user
        assert result[0]["role"] == "user"

    @pytest.mark.asyncio
    async def test_maps_assistant_to_model(self, async_session, sample_session, sample_messages):
        """Test that 'assistant' role is mapped to 'model' for Gemini."""
        mock_session_maker = MagicMock()
        mock_session_maker.return_value.__aenter__ = AsyncMock(return_value=async_session)
        mock_session_maker.return_value.__aexit__ = AsyncMock(return_value=None)

        with patch('app.db.database.async_session_maker', mock_session_maker):
            result = await get_chat_history(sample_session.id)

        roles = [msg["role"] for msg in result]
        assert "assistant" not in roles
        assert "model" in roles

    @pytest.mark.asyncio
    async def test_returns_empty_on_error(self):
        """Test that errors return empty list."""
        with patch('app.db.database.async_session_maker', side_effect=Exception("DB Error")):
            result = await get_chat_history("some_session")

        assert result == []


class TestBuildTutorContext:
    """Tests for build_tutor_context function."""

    @pytest.mark.asyncio
    async def test_builds_context_with_all_components(self):
        """Test that context includes all components."""
        with patch('app.core.context_builder.fetch_student_facts', new_callable=AsyncMock) as mock_facts:
            with patch('app.core.context_builder.fetch_learning_vocab', new_callable=AsyncMock) as mock_vocab:
                with patch('app.core.context_builder.get_chat_history', new_callable=AsyncMock) as mock_history:
                    with patch('app.core.context_builder.get_session_summary', new_callable=AsyncMock) as mock_summary:
                        mock_facts.return_value = [{"id": 1, "content": "Likes anime"}]
                        mock_vocab.return_value = [
                            {"kanji": "食べる", "kana": "たべる", "meaning": "to eat", "pos": "verb"}
                        ]
                        mock_history.return_value = []
                        mock_summary.return_value = None

                        result = await build_tutor_context("test_session_123")

        assert "system_prompt" in result
        assert "chat_history" in result
        assert "食べる" in result["system_prompt"]
        assert "[1] Likes anime" in result["system_prompt"]

    @pytest.mark.asyncio
    async def test_includes_current_date(self):
        """Test that system prompt includes current date."""
        with patch('app.core.context_builder.fetch_student_facts', new_callable=AsyncMock) as mock_facts:
            with patch('app.core.context_builder.fetch_learning_vocab', new_callable=AsyncMock) as mock_vocab:
                with patch('app.core.context_builder.get_chat_history', new_callable=AsyncMock) as mock_history:
                    with patch('app.core.context_builder.get_session_summary', new_callable=AsyncMock) as mock_summary:
                        mock_facts.return_value = []
                        mock_vocab.return_value = []
                        mock_history.return_value = []
                        mock_summary.return_value = None

                        result = await build_tutor_context("test_session")

        today = date.today().isoformat()
        assert today in result["system_prompt"]

    @pytest.mark.asyncio
    async def test_handles_no_vocab(self):
        """Test context building when no vocab is available."""
        with patch('app.core.context_builder.fetch_student_facts', new_callable=AsyncMock) as mock_facts:
            with patch('app.core.context_builder.fetch_learning_vocab', new_callable=AsyncMock) as mock_vocab:
                with patch('app.core.context_builder.get_chat_history', new_callable=AsyncMock) as mock_history:
                    with patch('app.core.context_builder.get_session_summary', new_callable=AsyncMock) as mock_summary:
                        mock_facts.return_value = []
                        mock_vocab.return_value = []
                        mock_history.return_value = []
                        mock_summary.return_value = None

                        result = await build_tutor_context("test_session")

        assert "No vocabulary loaded" in result["system_prompt"]

    @pytest.mark.asyncio
    async def test_tutor_context_has_no_tool_instructions(self):
        """Test that Tutor context does NOT include tool instructions."""
        with patch('app.core.context_builder.fetch_student_facts', new_callable=AsyncMock) as mock_facts:
            with patch('app.core.context_builder.fetch_learning_vocab', new_callable=AsyncMock) as mock_vocab:
                with patch('app.core.context_builder.get_chat_history', new_callable=AsyncMock) as mock_history:
                    with patch('app.core.context_builder.get_session_summary', new_callable=AsyncMock) as mock_summary:
                        mock_facts.return_value = []
                        mock_vocab.return_value = []
                        mock_history.return_value = []
                        mock_summary.return_value = None

                        result = await build_tutor_context("test_session")

        # Tutor prompt should NOT have tool usage instructions
        assert "manage_student_facts" not in result["system_prompt"]


class TestBuildListenerContext:
    """Tests for build_listener_context function."""

    @pytest.mark.asyncio
    async def test_builds_listener_context(self):
        """Test that listener context includes facts and messages."""
        with patch('app.core.context_builder.fetch_student_facts', new_callable=AsyncMock) as mock_facts:
            mock_facts.return_value = [{"id": 1, "content": "Likes anime"}]

            result = await build_listener_context(
                user_message="I hate natto",
                tutor_message="Do you like natto?",
            )

        assert "system_prompt" in result
        assert "user_message" in result
        assert "[1] Likes anime" in result["system_prompt"]
        assert "Do you like natto?" in result["system_prompt"]
        assert "I hate natto" in result["system_prompt"]

    @pytest.mark.asyncio
    async def test_listener_context_minimal(self):
        """Test that listener context is minimal (no vocab, no history)."""
        with patch('app.core.context_builder.fetch_student_facts', new_callable=AsyncMock) as mock_facts:
            mock_facts.return_value = []

            result = await build_listener_context(
                user_message="Hello",
                tutor_message="Hi there!",
            )

        # Should NOT have vocab or chat_history keys
        assert "chat_history" not in result
        assert "_raw" not in result


class TestSystemPromptTemplates:
    """Tests for the system prompt templates."""

    def test_tutor_template_has_required_placeholders(self):
        """Test that Tutor template has all required format placeholders."""
        assert "{today}" in TUTOR_SYSTEM_PROMPT_TEMPLATE
        assert "{student_facts_formatted}" in TUTOR_SYSTEM_PROMPT_TEMPLATE
        assert "{vocab_list_formatted}" in TUTOR_SYSTEM_PROMPT_TEMPLATE
        assert "{session_summary}" in TUTOR_SYSTEM_PROMPT_TEMPLATE

    def test_tutor_template_describes_tutor_role(self):
        """Test that Tutor template establishes tutor role."""
        assert "Japanese" in TUTOR_SYSTEM_PROMPT_TEMPLATE
        assert "tutor" in TUTOR_SYSTEM_PROMPT_TEMPLATE.lower()

    def test_tutor_template_has_no_tool_instructions(self):
        """Test that Tutor template does NOT mention tools."""
        assert "manage_student_facts" not in TUTOR_SYSTEM_PROMPT_TEMPLATE

    def test_listener_template_has_required_placeholders(self):
        """Test that Listener template has required placeholders."""
        assert "{student_facts_formatted}" in LISTENER_SYSTEM_PROMPT_TEMPLATE
        assert "{tutor_message}" in LISTENER_SYSTEM_PROMPT_TEMPLATE
        assert "{user_message}" in LISTENER_SYSTEM_PROMPT_TEMPLATE

    def test_listener_template_focused_on_facts(self):
        """Test that Listener template is focused on fact extraction."""
        assert "extract" in LISTENER_SYSTEM_PROMPT_TEMPLATE.lower()
        assert "fact" in LISTENER_SYSTEM_PROMPT_TEMPLATE.lower()
