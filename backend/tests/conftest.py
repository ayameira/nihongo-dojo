"""
Pytest fixtures and configuration for backend tests.
"""
import asyncio
import os
import tempfile
from typing import AsyncGenerator, Generator
from unittest.mock import MagicMock, AsyncMock, patch

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from httpx import AsyncClient, ASGITransport

from app.db.models import Base, VocabEntry, ChatMessage, ChatSession, TokenLog, StudentFact
from app.config import Settings


# Use a separate event loop for tests
@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_settings() -> Settings:
    """Create test settings with mocked values."""
    return Settings(
        database_url="sqlite+aiosqlite:///:memory:",
        gemini_api_key="test-api-key",
        gemini_model="gemini-2.0-flash",
        anki_collection_path="",
        cost_limit_weekly=10.0,
        gemini_input_cost_per_1m=0.075,
        gemini_output_cost_per_1m=0.30,
    )


@pytest_asyncio.fixture
async def async_engine():
    """Create an async engine for testing with in-memory SQLite."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest_asyncio.fixture
async def async_session(async_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create an async session for testing."""
    async_session_maker = async_sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with async_session_maker() as session:
        yield session


@pytest_asyncio.fixture
async def test_client(async_engine, test_settings) -> AsyncGenerator[AsyncClient, None]:
    """Create a test client with database override."""
    from app.main import app
    from app.db.database import get_session
    from app.config import get_settings

    async_session_maker = async_sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async def override_get_session():
        async with async_session_maker() as session:
            yield session

    def override_get_settings():
        return test_settings

    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_settings] = override_get_settings

    # Patch the global async_session_maker used in tools.py and context_builder.py
    with patch('app.db.database.async_session_maker', async_session_maker):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def sample_vocab(async_session: AsyncSession) -> VocabEntry:
    """Create a sample vocabulary entry."""
    entry = VocabEntry(
        kanji="食べる",
        kana="たべる",
        meaning="to eat",
        pos="verb",
        status="Learning",
        source="manual",
    )
    async_session.add(entry)
    await async_session.commit()
    await async_session.refresh(entry)
    return entry


@pytest_asyncio.fixture
async def sample_session(async_session: AsyncSession) -> ChatSession:
    """Create a sample chat session."""
    session = ChatSession(
        id="test_session_123",
        name="Test Session",
        preview="Hello, this is a test",
        message_count=0,
    )
    async_session.add(session)
    await async_session.commit()
    await async_session.refresh(session)
    return session


@pytest_asyncio.fixture
async def sample_messages(async_session: AsyncSession, sample_session: ChatSession) -> list[ChatMessage]:
    """Create sample chat messages."""
    from datetime import datetime, timedelta

    base_time = datetime(2024, 1, 15, 10, 0, 0)
    messages = [
        ChatMessage(
            session_id=sample_session.id,
            role="user",
            content="こんにちは",
            created_at=base_time,
        ),
        ChatMessage(
            session_id=sample_session.id,
            role="assistant",
            content="こんにちは！元気ですか？",
            created_at=base_time + timedelta(seconds=30),
        ),
    ]
    for msg in messages:
        async_session.add(msg)
    await async_session.commit()
    return messages


@pytest_asyncio.fixture
async def sample_token_logs(async_session: AsyncSession, sample_session: ChatSession) -> list[TokenLog]:
    """Create sample token logs."""
    from datetime import datetime, timedelta

    logs = []
    for i in range(3):
        log = TokenLog(
            session_id=sample_session.id,
            model="gemini-2.0-flash",
            input_tokens=100 + i * 50,
            output_tokens=200 + i * 100,
            image_count=0,
            cost_usd=0.001 + i * 0.0005,
        )
        async_session.add(log)
        logs.append(log)

    await async_session.commit()
    return logs


@pytest.fixture
def mock_gemini_client():
    """Create a mock Gemini client."""
    mock = MagicMock()

    async def mock_stream(*args, **kwargs):
        yield {"type": "text", "content": "テスト"}
        yield {"type": "text", "content": "返答"}
        yield {
            "type": "usage",
            "input_tokens": 100,
            "output_tokens": 50,
            "cost_usd": 0.001,
        }

    mock.stream_chat = mock_stream
    return mock
