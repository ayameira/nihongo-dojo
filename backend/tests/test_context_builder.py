"""
Tests for the context builder module.
"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from datetime import date

from app.core.context_builder import (
    build_context,
    fetch_learning_vocab,
    format_vocab_list,
    get_chat_history,
    SYSTEM_PROMPT_TEMPLATE,
)


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
        assert "to eat" in result
        assert "[verb]" in result

    def test_formats_kana_only_vocab(self):
        """Test formatting vocabulary without kanji."""
        vocab = [
            {"kanji": None, "kana": "これ", "meaning": "this", "pos": "other"},
        ]

        result = format_vocab_list(vocab)

        assert "これ:" in result
        assert "this" in result
        assert "[other]" in result
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
            result = await fetch_learning_vocab(limit=50)

        assert len(result) == 1
        assert result[0]["kanji"] == "学ぶ"
        assert result[0]["kana"] == "まなぶ"

    @pytest.mark.asyncio
    async def test_returns_empty_on_error(self):
        """Test that errors return empty list."""
        with patch('app.db.database.async_session_maker', side_effect=Exception("DB Error")):
            result = await fetch_learning_vocab()

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


class TestBuildContext:
    """Tests for build_context function."""

    @pytest.mark.asyncio
    async def test_builds_context_with_all_components(self, test_settings, temp_notes_file):
        """Test that context includes all components."""
        test_settings.class_notes_path = temp_notes_file

        with patch('app.core.context_builder.get_settings', return_value=test_settings):
            with patch('app.core.context_builder.fetch_learning_vocab', new_callable=AsyncMock) as mock_vocab:
                with patch('app.core.context_builder.get_chat_history', new_callable=AsyncMock) as mock_history:
                    mock_vocab.return_value = [
                        {"kanji": "食べる", "kana": "たべる", "meaning": "to eat", "pos": "verb"}
                    ]
                    mock_history.return_value = []

                    result = await build_context("test_session_123")

        assert "system_prompt" in result
        assert "chat_history" in result
        assert "食べる" in result["system_prompt"]

    @pytest.mark.asyncio
    async def test_includes_current_date(self, test_settings, temp_notes_file):
        """Test that system prompt includes current date."""
        test_settings.class_notes_path = temp_notes_file

        with patch('app.core.context_builder.get_settings', return_value=test_settings):
            with patch('app.core.context_builder.fetch_learning_vocab', new_callable=AsyncMock) as mock_vocab:
                with patch('app.core.context_builder.get_chat_history', new_callable=AsyncMock) as mock_history:
                    mock_vocab.return_value = []
                    mock_history.return_value = []

                    result = await build_context("test_session")

        today = date.today().isoformat()
        assert today in result["system_prompt"]

    @pytest.mark.asyncio
    async def test_includes_too_hard_instruction(self, test_settings, temp_notes_file):
        """Test that 'too_hard' feedback adds simplification instruction."""
        test_settings.class_notes_path = temp_notes_file

        with patch('app.core.context_builder.get_settings', return_value=test_settings):
            with patch('app.core.context_builder.fetch_learning_vocab', new_callable=AsyncMock) as mock_vocab:
                with patch('app.core.context_builder.get_chat_history', new_callable=AsyncMock) as mock_history:
                    mock_vocab.return_value = []
                    mock_history.return_value = []

                    result = await build_context("test_session", difficulty_feedback="too_hard")

        assert "too hard" in result["system_prompt"].lower()
        assert "simplify" in result["system_prompt"].lower()

    @pytest.mark.asyncio
    async def test_includes_too_easy_instruction(self, test_settings, temp_notes_file):
        """Test that 'too_easy' feedback adds complexity instruction."""
        test_settings.class_notes_path = temp_notes_file

        with patch('app.core.context_builder.get_settings', return_value=test_settings):
            with patch('app.core.context_builder.fetch_learning_vocab', new_callable=AsyncMock) as mock_vocab:
                with patch('app.core.context_builder.get_chat_history', new_callable=AsyncMock) as mock_history:
                    mock_vocab.return_value = []
                    mock_history.return_value = []

                    result = await build_context("test_session", difficulty_feedback="too_easy")

        assert "too easy" in result["system_prompt"].lower()
        assert "complexity" in result["system_prompt"].lower()

    @pytest.mark.asyncio
    async def test_handles_no_vocab(self, test_settings, temp_notes_file):
        """Test context building when no vocab is available."""
        test_settings.class_notes_path = temp_notes_file

        with patch('app.core.context_builder.get_settings', return_value=test_settings):
            with patch('app.core.context_builder.fetch_learning_vocab', new_callable=AsyncMock) as mock_vocab:
                with patch('app.core.context_builder.get_chat_history', new_callable=AsyncMock) as mock_history:
                    mock_vocab.return_value = []
                    mock_history.return_value = []

                    result = await build_context("test_session")

        assert "No vocabulary loaded" in result["system_prompt"]


class TestSystemPromptTemplate:
    """Tests for the system prompt template."""

    def test_template_has_required_placeholders(self):
        """Test that template has all required format placeholders."""
        assert "{today}" in SYSTEM_PROMPT_TEMPLATE
        assert "{class_notes_content}" in SYSTEM_PROMPT_TEMPLATE
        assert "{vocab_list_formatted}" in SYSTEM_PROMPT_TEMPLATE
        assert "{difficulty_instruction}" in SYSTEM_PROMPT_TEMPLATE

    def test_template_describes_tutor_role(self):
        """Test that template establishes tutor role."""
        assert "Japanese" in SYSTEM_PROMPT_TEMPLATE
        assert "tutor" in SYSTEM_PROMPT_TEMPLATE.lower()

    def test_template_mentions_tools(self):
        """Test that template mentions available tools."""
        assert "save_vocab" in SYSTEM_PROMPT_TEMPLATE
        assert "update_notes" in SYSTEM_PROMPT_TEMPLATE
