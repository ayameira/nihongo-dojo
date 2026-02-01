"""
Tests for the tools module.
"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from app.core.tools import (
    MANAGE_STUDENT_FACTS_TOOL,
    ALL_TOOLS,
    execute_tool_call,
    execute_manage_student_facts,
)


class TestToolDefinitions:
    """Tests for tool definition schemas."""

    def test_manage_student_facts_tool_schema(self):
        """Test manage_student_facts tool has correct schema."""
        assert MANAGE_STUDENT_FACTS_TOOL["name"] == "manage_student_facts"
        assert "description" in MANAGE_STUDENT_FACTS_TOOL
        assert "parameters" in MANAGE_STUDENT_FACTS_TOOL

        params = MANAGE_STUDENT_FACTS_TOOL["parameters"]
        assert params["type"] == "object"
        assert "action" in params["properties"]
        assert "content" in params["properties"]
        assert "fact_id" in params["properties"]

        # Check action enum
        action_prop = params["properties"]["action"]
        assert "add" in action_prop["enum"]
        assert "edit" in action_prop["enum"]
        assert "delete" in action_prop["enum"]

        # Check fact_id type
        fact_id_prop = params["properties"]["fact_id"]
        assert fact_id_prop["type"] == "integer"

        # Check required fields
        assert "action" in params["required"]

    def test_all_tools_contains_manage_student_facts(self):
        """Test ALL_TOOLS contains the student facts tool."""
        assert len(ALL_TOOLS) == 1
        names = [t["name"] for t in ALL_TOOLS]
        assert "manage_student_facts" in names


class TestExecuteToolCall:
    """Tests for the execute_tool_call dispatcher."""

    @pytest.mark.asyncio
    async def test_dispatches_to_manage_student_facts(self):
        """Test that manage_student_facts is dispatched correctly."""
        with patch('app.core.tools.execute_manage_student_facts', new_callable=AsyncMock) as mock:
            mock.return_value = "Added fact [#1]: test"
            result = await execute_tool_call(
                "manage_student_facts",
                {"action": "add", "content": "test fact"}
            )
            mock.assert_called_once()
            assert result == "Added fact [#1]: test"

    @pytest.mark.asyncio
    async def test_returns_error_for_unknown_tool(self):
        """Test that unknown tools return error message."""
        result = await execute_tool_call("unknown_tool", {})
        assert "Unknown tool" in result

    @pytest.mark.asyncio
    async def test_handles_execution_error(self):
        """Test that execution errors are caught and reported."""
        with patch('app.core.tools.execute_manage_student_facts', new_callable=AsyncMock) as mock:
            mock.side_effect = Exception("Database error")
            result = await execute_tool_call("manage_student_facts", {"action": "add", "content": "test"})
            assert "Error executing" in result
            assert "Database error" in result


class TestExecuteManageStudentFacts:
    """Tests for execute_manage_student_facts function."""

    @pytest.mark.asyncio
    async def test_add_fact(self, async_engine):
        """Test adding a new fact."""
        from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
        from sqlalchemy import select
        from app.db.models import StudentFact

        session_maker = async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

        with patch('app.db.database.async_session_maker', session_maker):
            result = await execute_manage_student_facts({
                "action": "add",
                "content": "Likes watching Naruto"
            })

        assert "Added fact" in result
        assert "Naruto" in result

        # Verify in DB
        async with session_maker() as session:
            stmt = select(StudentFact)
            facts = (await session.execute(stmt)).scalars().all()
            assert len(facts) == 1
            assert facts[0].content == "Likes watching Naruto"
            assert facts[0].source == "listener"

    @pytest.mark.asyncio
    async def test_add_duplicate_prevented(self, async_engine):
        """Test that duplicate facts are not added."""
        from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
        from app.db.models import StudentFact

        session_maker = async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

        # Add first fact
        async with session_maker() as session:
            session.add(StudentFact(content="Test fact", source="tutor"))
            await session.commit()

        # Try to add duplicate
        with patch('app.db.database.async_session_maker', session_maker):
            result = await execute_manage_student_facts({
                "action": "add",
                "content": "Test fact"
            })

        assert "already exists" in result

    @pytest.mark.asyncio
    async def test_add_requires_content(self, async_engine):
        """Test that add action requires content."""
        from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

        session_maker = async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

        with patch('app.db.database.async_session_maker', session_maker):
            result = await execute_manage_student_facts({
                "action": "add",
                "content": ""
            })

        assert "Error" in result
        assert "content" in result

    @pytest.mark.asyncio
    async def test_edit_fact_by_id(self, async_engine):
        """Test editing an existing fact by ID."""
        from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
        from sqlalchemy import select
        from app.db.models import StudentFact

        session_maker = async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

        # Add fact to edit
        async with session_maker() as session:
            fact = StudentFact(content="Original content", source="tutor")
            session.add(fact)
            await session.commit()
            await session.refresh(fact)
            fact_id = fact.id

        # Edit the fact by ID
        with patch('app.db.database.async_session_maker', session_maker):
            result = await execute_manage_student_facts({
                "action": "edit",
                "fact_id": fact_id,
                "content": "Updated content"
            })

        assert "Updated fact" in result

        # Verify in DB
        async with session_maker() as session:
            stmt = select(StudentFact).where(StudentFact.id == fact_id)
            fact = (await session.execute(stmt)).scalar_one()
            assert fact.content == "Updated content"

    @pytest.mark.asyncio
    async def test_edit_nonexistent_fact(self, async_engine):
        """Test editing a nonexistent fact."""
        from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

        session_maker = async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

        with patch('app.db.database.async_session_maker', session_maker):
            result = await execute_manage_student_facts({
                "action": "edit",
                "fact_id": 99999,
                "content": "New content"
            })

        assert "Error" in result
        assert "No fact found" in result

    @pytest.mark.asyncio
    async def test_edit_requires_fact_id(self, async_engine):
        """Test that edit action requires fact_id."""
        from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

        session_maker = async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

        with patch('app.db.database.async_session_maker', session_maker):
            result = await execute_manage_student_facts({
                "action": "edit",
                "content": "New content"
            })

        assert "Error" in result
        assert "fact_id" in result

    @pytest.mark.asyncio
    async def test_delete_fact_by_id(self, async_engine):
        """Test deleting a fact by ID."""
        from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
        from sqlalchemy import select
        from app.db.models import StudentFact

        session_maker = async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

        # Add fact to delete
        async with session_maker() as session:
            fact = StudentFact(content="Fact to delete", source="tutor")
            session.add(fact)
            await session.commit()
            await session.refresh(fact)
            fact_id = fact.id

        # Delete the fact by ID
        with patch('app.db.database.async_session_maker', session_maker):
            result = await execute_manage_student_facts({
                "action": "delete",
                "fact_id": fact_id
            })

        assert "Deleted fact" in result

        # Verify deleted
        async with session_maker() as session:
            stmt = select(StudentFact)
            facts = (await session.execute(stmt)).scalars().all()
            assert len(facts) == 0

    @pytest.mark.asyncio
    async def test_delete_nonexistent_fact(self, async_engine):
        """Test deleting a nonexistent fact."""
        from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

        session_maker = async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

        with patch('app.db.database.async_session_maker', session_maker):
            result = await execute_manage_student_facts({
                "action": "delete",
                "fact_id": 99999
            })

        assert "Error" in result
        assert "No fact found" in result

    @pytest.mark.asyncio
    async def test_delete_requires_fact_id(self, async_engine):
        """Test that delete action requires fact_id."""
        from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

        session_maker = async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

        with patch('app.db.database.async_session_maker', session_maker):
            result = await execute_manage_student_facts({
                "action": "delete"
            })

        assert "Error" in result
        assert "fact_id" in result
