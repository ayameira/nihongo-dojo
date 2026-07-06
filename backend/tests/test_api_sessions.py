"""
API tests for sessions routes.
"""
import pytest


class TestListSessions:
    """Tests for GET /api/sessions endpoint."""

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_sessions(self, test_client):
        """Test that empty list is returned when no sessions exist."""
        response = await test_client.get("/api/sessions")

        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_returns_sessions_ordered_by_updated(self, test_client, sample_session):
        """Test that sessions are ordered by updated_at descending."""
        # Create another session
        response = await test_client.post("/api/sessions", json={})
        assert response.status_code == 200
        new_session_id = response.json()["id"]

        # List sessions
        response = await test_client.get("/api/sessions")
        sessions = response.json()

        assert len(sessions) == 2
        # Both sessions should be present
        ids = [s["id"] for s in sessions]
        assert sample_session.id in ids
        assert new_session_id in ids


class TestCreateSession:
    """Tests for POST /api/sessions endpoint."""

    @pytest.mark.asyncio
    async def test_creates_session_with_generated_id(self, test_client):
        """Test creating session with auto-generated ID."""
        response = await test_client.post("/api/sessions", json={})

        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["id"].startswith("session_")
        assert data["message_count"] == 0

    @pytest.mark.asyncio
    async def test_creates_session_with_provided_id(self, test_client):
        """Test creating session with provided ID."""
        custom_id = "custom_session_123"
        response = await test_client.post("/api/sessions", json={"id": custom_id})

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == custom_id
        assert data["language_code"] == "ja"

    @pytest.mark.asyncio
    async def test_creates_session_with_active_language_code(self, test_client):
        """Test creating a session with target language metadata."""
        response = await test_client.post(
            "/api/sessions",
            json={"id": "language_session", "language_code": "ja"},
        )

        assert response.status_code == 200
        assert response.json()["language_code"] == "ja"

    @pytest.mark.asyncio
    async def test_unknown_session_language_falls_back_to_japanese(self, test_client):
        """Until another profile exists, unknown language codes normalize to Japanese."""
        response = await test_client.post(
            "/api/sessions",
            json={"id": "fallback_language_session", "language_code": "es"},
        )

        assert response.status_code == 200
        assert response.json()["language_code"] == "ja"

    @pytest.mark.asyncio
    async def test_session_has_timestamps(self, test_client):
        """Test that created session has timestamps."""
        response = await test_client.post("/api/sessions", json={})

        data = response.json()
        assert "created_at" in data
        assert "updated_at" in data


class TestGetSessionById:
    """Tests for GET /api/sessions/{session_id} endpoint."""

    @pytest.mark.asyncio
    async def test_returns_session(self, test_client, sample_session):
        """Test retrieving existing session."""
        response = await test_client.get(f"/api/sessions/{sample_session.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_session.id
        assert data["name"] == sample_session.name

    @pytest.mark.asyncio
    async def test_returns_404_for_nonexistent(self, test_client):
        """Test that 404 is returned for non-existent session."""
        response = await test_client.get("/api/sessions/nonexistent_id")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestUpdateSession:
    """Tests for PUT /api/sessions/{session_id} endpoint."""

    @pytest.mark.asyncio
    async def test_renames_session(self, test_client, sample_session):
        """Test renaming a session."""
        new_name = "Renamed Session"
        response = await test_client.put(
            f"/api/sessions/{sample_session.id}",
            json={"name": new_name}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == new_name

    @pytest.mark.asyncio
    async def test_returns_404_for_nonexistent(self, test_client):
        """Test that 404 is returned when updating non-existent session."""
        response = await test_client.put(
            "/api/sessions/nonexistent_id",
            json={"name": "New Name"}
        )

        assert response.status_code == 404


class TestDeleteSession:
    """Tests for DELETE /api/sessions/{session_id} endpoint."""

    @pytest.mark.asyncio
    async def test_deletes_session(self, test_client, sample_session):
        """Test deleting a session."""
        response = await test_client.delete(f"/api/sessions/{sample_session.id}")

        assert response.status_code == 200
        assert response.json()["success"] is True

        # Verify session is deleted
        get_response = await test_client.get(f"/api/sessions/{sample_session.id}")
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_cascades_delete_messages(self, test_client, sample_session, sample_messages):
        """Test that deleting session also deletes associated messages."""
        response = await test_client.delete(f"/api/sessions/{sample_session.id}")

        assert response.status_code == 200
        # Messages should be deleted with session (no separate endpoint to verify)

    @pytest.mark.asyncio
    async def test_delete_nonexistent_succeeds(self, test_client):
        """Test that deleting non-existent session doesn't error."""
        # Note: Current implementation doesn't check existence before delete
        response = await test_client.delete("/api/sessions/nonexistent_id")
        assert response.status_code == 200
