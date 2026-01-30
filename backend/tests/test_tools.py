"""
Tests for the tools module.
"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from app.core.tools import (
    UPDATE_STUDENT_RECORD_TOOL,
    ALL_TOOLS,
    execute_tool_call,
    execute_update_student_record,
)


class TestToolDefinitions:
    """Tests for tool definition schemas."""

    def test_update_student_record_tool_schema(self):
        """Test update_student_record tool has correct schema."""
        assert UPDATE_STUDENT_RECORD_TOOL["name"] == "update_student_record"
        assert "description" in UPDATE_STUDENT_RECORD_TOOL
        assert "parameters" in UPDATE_STUDENT_RECORD_TOOL

        params = UPDATE_STUDENT_RECORD_TOOL["parameters"]
        assert params["type"] == "object"
        assert "section" in params["properties"]
        assert "action" in params["properties"]
        assert "content" in params["properties"]

        # Check enums
        section_prop = params["properties"]["section"]
        assert "goals" in section_prop["enum"]
        assert "background" in section_prop["enum"]
        assert "interests" in section_prop["enum"]
        assert "preferences" in section_prop["enum"]
        assert "notes" in section_prop["enum"]

        action_prop = params["properties"]["action"]
        assert "append" in action_prop["enum"]
        assert "replace" in action_prop["enum"]

        # Check required fields
        assert "section" in params["required"]
        assert "action" in params["required"]
        assert "content" in params["required"]

    def test_all_tools_contains_student_record_tool(self):
        """Test ALL_TOOLS contains the student record tool."""
        assert len(ALL_TOOLS) == 1
        names = [t["name"] for t in ALL_TOOLS]
        assert "update_student_record" in names


class TestExecuteToolCall:
    """Tests for the execute_tool_call dispatcher."""

    @pytest.mark.asyncio
    async def test_dispatches_to_update_student_record(self):
        """Test that update_student_record is dispatched correctly."""
        with patch('app.core.tools.execute_update_student_record', new_callable=AsyncMock) as mock:
            mock.return_value = "Updated student record: goals"
            result = await execute_tool_call(
                "update_student_record",
                {"section": "goals", "action": "replace", "content": "test"}
            )
            mock.assert_called_once()
            assert result == "Updated student record: goals"

    @pytest.mark.asyncio
    async def test_returns_error_for_unknown_tool(self):
        """Test that unknown tools return error message."""
        result = await execute_tool_call("unknown_tool", {})
        assert "Unknown tool" in result

    @pytest.mark.asyncio
    async def test_handles_execution_error(self):
        """Test that execution errors are caught and reported."""
        with patch('app.core.tools.execute_update_student_record', new_callable=AsyncMock) as mock:
            mock.side_effect = Exception("Database error")
            result = await execute_tool_call("update_student_record", {})
            assert "Error executing" in result
            assert "Database error" in result


class TestExecuteUpdateStudentRecord:
    """Tests for execute_update_student_record function."""

    @pytest.mark.asyncio
    async def test_updates_section(self, temp_student_record_file, test_settings):
        """Test updating a student record section."""
        test_settings.student_record_path = temp_student_record_file

        with patch('app.config.get_settings', return_value=test_settings):
            result = await execute_update_student_record({
                "section": "goals",
                "action": "replace",
                "content": "New goals content",
            })

        assert "Updated student record: goals" in result

    @pytest.mark.asyncio
    async def test_appends_to_section(self, temp_student_record_file, test_settings):
        """Test appending to a student record section."""
        test_settings.student_record_path = temp_student_record_file

        with patch('app.config.get_settings', return_value=test_settings):
            result = await execute_update_student_record({
                "section": "notes",
                "action": "append",
                "content": "Additional observation",
            })

        assert "Updated student record: notes" in result
