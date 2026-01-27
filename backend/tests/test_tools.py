"""
Tests for the tools module.
"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from app.core.tools import (
    SAVE_VOCAB_TOOL,
    UPDATE_NOTES_TOOL,
    ADJUST_DIFFICULTY_TOOL,
    ALL_TOOLS,
    execute_tool_call,
    execute_save_vocab,
    execute_update_notes,
    execute_adjust_difficulty,
)


class TestToolDefinitions:
    """Tests for tool definition schemas."""

    def test_save_vocab_tool_schema(self):
        """Test save_vocab tool has correct schema."""
        assert SAVE_VOCAB_TOOL["name"] == "save_vocab"
        assert "description" in SAVE_VOCAB_TOOL
        assert "parameters" in SAVE_VOCAB_TOOL

        params = SAVE_VOCAB_TOOL["parameters"]
        assert params["type"] == "object"
        assert "kanji" in params["properties"]
        assert "kana" in params["properties"]
        assert "meaning" in params["properties"]
        assert "pos" in params["properties"]

        # Check required fields
        assert "kana" in params["required"]
        assert "meaning" in params["required"]
        assert "pos" in params["required"]

    def test_update_notes_tool_schema(self):
        """Test update_notes tool has correct schema."""
        assert UPDATE_NOTES_TOOL["name"] == "update_notes"

        params = UPDATE_NOTES_TOOL["parameters"]
        assert "section" in params["properties"]
        assert "action" in params["properties"]
        assert "content" in params["properties"]

        # Check enums
        section_prop = params["properties"]["section"]
        assert "current_focus" in section_prop["enum"]
        assert "recent_corrections" in section_prop["enum"]
        assert "recent_vocab" in section_prop["enum"]

        action_prop = params["properties"]["action"]
        assert "append" in action_prop["enum"]
        assert "replace" in action_prop["enum"]

    def test_adjust_difficulty_tool_schema(self):
        """Test adjust_difficulty tool has correct schema."""
        assert ADJUST_DIFFICULTY_TOOL["name"] == "adjust_difficulty"

        params = ADJUST_DIFFICULTY_TOOL["parameters"]
        direction_prop = params["properties"]["direction"]
        assert "easier" in direction_prop["enum"]
        assert "harder" in direction_prop["enum"]

        # Only direction is required
        assert "direction" in params["required"]
        assert "reason" not in params.get("required", [])

    def test_all_tools_contains_all_definitions(self):
        """Test ALL_TOOLS contains all tool definitions."""
        assert len(ALL_TOOLS) == 3
        names = [t["name"] for t in ALL_TOOLS]
        assert "save_vocab" in names
        assert "update_notes" in names
        assert "adjust_difficulty" in names

    def test_pos_enum_values(self):
        """Test that part of speech enum has expected values."""
        pos_prop = SAVE_VOCAB_TOOL["parameters"]["properties"]["pos"]
        expected_pos = ["noun", "verb", "i-adj", "na-adj", "adverb", "particle", "expression", "other"]
        for pos in expected_pos:
            assert pos in pos_prop["enum"]


class TestExecuteToolCall:
    """Tests for the execute_tool_call dispatcher."""

    @pytest.mark.asyncio
    async def test_dispatches_to_save_vocab(self):
        """Test that save_vocab is dispatched correctly."""
        with patch('app.core.tools.execute_save_vocab', new_callable=AsyncMock) as mock:
            mock.return_value = "Saved"
            result = await execute_tool_call("save_vocab", {"kana": "test", "meaning": "test", "pos": "noun"})
            mock.assert_called_once()
            assert result == "Saved"

    @pytest.mark.asyncio
    async def test_dispatches_to_update_notes(self):
        """Test that update_notes is dispatched correctly."""
        with patch('app.core.tools.execute_update_notes', new_callable=AsyncMock) as mock:
            mock.return_value = "Updated"
            result = await execute_tool_call("update_notes", {"section": "current_focus", "action": "replace", "content": "test"})
            mock.assert_called_once()
            assert result == "Updated"

    @pytest.mark.asyncio
    async def test_dispatches_to_adjust_difficulty(self):
        """Test that adjust_difficulty is dispatched correctly."""
        with patch('app.core.tools.execute_adjust_difficulty', new_callable=AsyncMock) as mock:
            mock.return_value = "Adjusted"
            result = await execute_tool_call("adjust_difficulty", {"direction": "easier"})
            mock.assert_called_once()
            assert result == "Adjusted"

    @pytest.mark.asyncio
    async def test_returns_error_for_unknown_tool(self):
        """Test that unknown tools return error message."""
        result = await execute_tool_call("unknown_tool", {})
        assert "Unknown tool" in result

    @pytest.mark.asyncio
    async def test_handles_execution_error(self):
        """Test that execution errors are caught and reported."""
        with patch('app.core.tools.execute_save_vocab', new_callable=AsyncMock) as mock:
            mock.side_effect = Exception("Database error")
            result = await execute_tool_call("save_vocab", {})
            assert "Error executing" in result
            assert "Database error" in result


class TestExecuteSaveVocab:
    """Tests for execute_save_vocab function."""

    @pytest.mark.asyncio
    async def test_creates_new_vocab_entry(self, async_session):
        """Test creating a new vocabulary entry."""
        # Mock the async_session_maker to return our test session
        mock_session_maker = MagicMock()
        mock_session_maker.return_value.__aenter__ = AsyncMock(return_value=async_session)
        mock_session_maker.return_value.__aexit__ = AsyncMock(return_value=None)

        with patch('app.db.database.async_session_maker', mock_session_maker):
            result = await execute_save_vocab({
                "kanji": "新しい",
                "kana": "あたらしい",
                "meaning": "new",
                "pos": "i-adj",
            })

        assert "Saved new vocabulary" in result
        assert "新しい" in result or "あたらしい" in result

    @pytest.mark.asyncio
    async def test_updates_existing_vocab(self, async_session, sample_vocab):
        """Test updating existing vocabulary entry."""
        mock_session_maker = MagicMock()
        mock_session_maker.return_value.__aenter__ = AsyncMock(return_value=async_session)
        mock_session_maker.return_value.__aexit__ = AsyncMock(return_value=None)

        with patch('app.db.database.async_session_maker', mock_session_maker):
            result = await execute_save_vocab({
                "kanji": "食べる",
                "kana": "たべる",
                "meaning": "to eat (updated)",
                "pos": "verb",
            })

        assert "Updated vocabulary" in result

    @pytest.mark.asyncio
    async def test_handles_kana_only_word(self, async_session):
        """Test creating kana-only word."""
        mock_session_maker = MagicMock()
        mock_session_maker.return_value.__aenter__ = AsyncMock(return_value=async_session)
        mock_session_maker.return_value.__aexit__ = AsyncMock(return_value=None)

        with patch('app.db.database.async_session_maker', mock_session_maker):
            result = await execute_save_vocab({
                "kanji": "",
                "kana": "これ",
                "meaning": "this",
                "pos": "other",
            })

        assert "Saved new vocabulary" in result
        assert "これ" in result


class TestExecuteUpdateNotes:
    """Tests for execute_update_notes function."""

    @pytest.mark.asyncio
    async def test_updates_section(self, temp_notes_file, test_settings):
        """Test updating a notes section."""
        test_settings.class_notes_path = temp_notes_file

        with patch('app.config.get_settings', return_value=test_settings):
            result = await execute_update_notes({
                "section": "current_focus",
                "action": "replace",
                "content": "New focus content",
            })

        assert "Updated current_focus section" in result

    @pytest.mark.asyncio
    async def test_appends_to_section(self, temp_notes_file, test_settings):
        """Test appending to a notes section."""
        test_settings.class_notes_path = temp_notes_file

        with patch('app.config.get_settings', return_value=test_settings):
            result = await execute_update_notes({
                "section": "recent_vocab",
                "action": "append",
                "content": "- 走る (はしる): to run",
            })

        assert "Updated recent_vocab section" in result


class TestExecuteAdjustDifficulty:
    """Tests for execute_adjust_difficulty function."""

    @pytest.mark.asyncio
    async def test_logs_easier_adjustment(self):
        """Test logging difficulty adjustment to easier."""
        result = await execute_adjust_difficulty({
            "direction": "easier",
            "reason": "Grammar was too complex",
        })

        assert "easier" in result
        assert "Noted" in result

    @pytest.mark.asyncio
    async def test_logs_harder_adjustment(self):
        """Test logging difficulty adjustment to harder."""
        result = await execute_adjust_difficulty({
            "direction": "harder",
        })

        assert "harder" in result
        assert "Noted" in result

    @pytest.mark.asyncio
    async def test_handles_missing_reason(self):
        """Test that missing reason doesn't cause error."""
        result = await execute_adjust_difficulty({
            "direction": "easier",
        })

        assert "easier" in result
