"""
API tests for chat routes.
"""
import pytest
from unittest.mock import patch, AsyncMock


class TestGetChatHistory:
    """Tests for GET /api/chat/history/{session_id} endpoint."""

    @pytest.mark.asyncio
    async def test_returns_history(self, test_client, sample_session, sample_messages):
        """Test retrieving chat history."""
        response = await test_client.get(f"/api/chat/history/{sample_session.id}")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    @pytest.mark.asyncio
    async def test_returns_messages_in_order(self, test_client, sample_session, sample_messages):
        """Test that messages are returned in chronological order."""
        response = await test_client.get(f"/api/chat/history/{sample_session.id}")

        data = response.json()
        # First message should be from user
        assert data[0]["role"] == "user"
        assert data[1]["role"] == "assistant"

    @pytest.mark.asyncio
    async def test_returns_message_fields(self, test_client, sample_session, sample_messages):
        """Test that message fields are included."""
        response = await test_client.get(f"/api/chat/history/{sample_session.id}")

        msg = response.json()[0]
        assert "id" in msg
        assert "role" in msg
        assert "content" in msg
        assert "has_image" in msg
        assert "created_at" in msg

    @pytest.mark.asyncio
    async def test_returns_empty_for_new_session(self, test_client):
        """Test that empty list is returned for session with no messages."""
        response = await test_client.get("/api/chat/history/nonexistent_session")

        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_respects_limit(self, test_client, sample_session, sample_messages):
        """Test that limit parameter is respected."""
        response = await test_client.get(f"/api/chat/history/{sample_session.id}?limit=1")

        assert response.status_code == 200
        assert len(response.json()) == 1


class TestStreamChat:
    """Tests for POST /api/chat/stream endpoint."""

    @pytest.mark.asyncio
    async def test_returns_stream_response(self, test_client, test_settings):
        """Test that stream endpoint returns SSE response."""
        # Mock the Gemini client to avoid actual API calls

        async def mock_generate_stream(*args, **kwargs):
            yield 'data: {"type": "text", "content": "Hello"}\n\n'
            yield 'data: {"type": "done"}\n\n'

        with patch('app.api.chat.generate_stream', mock_generate_stream):
            response = await test_client.post(
                "/api/chat/stream",
                json={
                    "message": "こんにちは",
                    "session_id": "test_session",
                }
            )

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")

    @pytest.mark.asyncio
    async def test_returns_error_without_api_key(self, test_client):
        """Test that error is returned when API key is not configured."""
        from app.config import Settings

        settings_no_key = Settings(
            database_url="sqlite+aiosqlite:///:memory:",
            gemini_api_key="",  # No API key
        )

        with patch('app.api.chat.get_settings', return_value=settings_no_key):
            response = await test_client.post(
                "/api/chat/stream",
                json={
                    "message": "test",
                    "session_id": "test_session",
                }
            )

        assert response.status_code == 200  # SSE always returns 200
        content = response.text
        assert "error" in content.lower() or "not configured" in content.lower()

    @pytest.mark.asyncio
    async def test_accepts_image_data(self, test_client, test_settings):
        """Test that image data is accepted."""
        async def mock_generate_stream(*args, **kwargs):
            yield 'data: {"type": "done"}\n\n'

        with patch('app.api.chat.generate_stream', mock_generate_stream):
            response = await test_client.post(
                "/api/chat/stream",
                json={
                    "message": "What's in this image?",
                    "image_data": "base64encodeddata",
                    "session_id": "test_session",
                }
            )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_accepts_difficulty_feedback(self, test_client, test_settings):
        """Test that difficulty feedback is accepted."""
        async def mock_generate_stream(*args, **kwargs):
            yield 'data: {"type": "done"}\n\n'

        with patch('app.api.chat.generate_stream', mock_generate_stream):
            response = await test_client.post(
                "/api/chat/stream",
                json={
                    "message": "test",
                    "session_id": "test_session",
                    "difficulty_feedback": "too_hard",
                }
            )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_accepts_model_override(self, test_client, test_settings):
        """Test that the chat request accepts a model override."""
        seen = {}

        async def mock_generate_stream(request, *args, **kwargs):
            seen["model"] = request.model
            yield 'data: {"type": "done"}\n\n'

        with patch('app.api.chat.generate_stream', mock_generate_stream):
            response = await test_client.post(
                "/api/chat/stream",
                json={
                    "message": "test",
                    "session_id": "test_session",
                    "model": "gemini-3-pro-preview",
                }
            )

        assert response.status_code == 200
        assert seen["model"] == "gemini-3-pro-preview"

    @pytest.mark.asyncio
    async def test_accepts_provider_override(self, test_client, test_settings):
        """Test that the chat request accepts a provider override."""
        seen = {}

        async def mock_generate_stream(request, *args, **kwargs):
            seen["provider"] = request.provider
            seen["model"] = request.model
            yield 'data: {"type": "done"}\n\n'

        with patch('app.api.chat.generate_stream', mock_generate_stream):
            response = await test_client.post(
                "/api/chat/stream",
                json={
                    "message": "test",
                    "session_id": "test_session",
                    "provider": "groq",
                    "model": "llama-3.1-8b-instant",
                }
            )

        assert response.status_code == 200
        assert seen == {
            "provider": "groq",
            "model": "llama-3.1-8b-instant",
        }

    @pytest.mark.asyncio
    async def test_rejects_unknown_model_override(self, test_client, test_settings):
        """Test that unknown model overrides are rejected before streaming."""
        response = await test_client.post(
            "/api/chat/stream",
            json={
                "message": "test",
                "session_id": "test_session",
                "model": "unknown-model",
            }
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_requires_session_id(self, test_client):
        """Test that session_id is required."""
        response = await test_client.post(
            "/api/chat/stream",
            json={"message": "test"}
        )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_requires_message(self, test_client):
        """Test that message is required."""
        response = await test_client.post(
            "/api/chat/stream",
            json={"session_id": "test"}
        )

        assert response.status_code == 422  # Validation error
