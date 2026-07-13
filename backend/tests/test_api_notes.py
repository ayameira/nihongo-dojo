"""
Tests for the notes API endpoints (student facts).
"""
import pytest
from httpx import AsyncClient


class TestGetNotes:
    """Tests for GET /api/notes endpoint."""

    @pytest.mark.asyncio
    async def test_returns_empty_placeholder(self, test_client: AsyncClient):
        """Test returns placeholder when no facts exist."""
        response = await test_client.get("/api/notes")
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert "No information recorded yet" in data["content"]


class TestListFacts:
    """Tests for GET /api/notes/facts endpoint."""

    @pytest.mark.asyncio
    async def test_returns_empty_list(self, test_client: AsyncClient):
        """Test returns empty list when no facts exist."""
        response = await test_client.get("/api/notes/facts")
        assert response.status_code == 200
        data = response.json()
        assert data["facts"] == []


class TestAddFact:
    """Tests for POST /api/notes/facts endpoint."""

    @pytest.mark.asyncio
    async def test_adds_fact(self, test_client: AsyncClient):
        """Test adding a new fact."""
        response = await test_client.post(
            "/api/notes/facts",
            json={"content": "Likes anime"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["content"] == "Likes anime"
        assert data["source"] == "manual"
        assert "id" in data

    @pytest.mark.asyncio
    async def test_prevents_duplicate(self, test_client: AsyncClient):
        """Test that duplicate facts are prevented."""
        # Add first fact
        await test_client.post(
            "/api/notes/facts",
            json={"content": "Duplicate fact"}
        )
        # Try to add duplicate
        response = await test_client.post(
            "/api/notes/facts",
            json={"content": "Duplicate fact"}
        )
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]


class TestDeleteFact:
    """Tests for DELETE /api/notes/facts/{id} endpoint."""

    @pytest.mark.asyncio
    async def test_deletes_fact(self, test_client: AsyncClient):
        """Test deleting a fact."""
        # Add a fact first
        add_response = await test_client.post(
            "/api/notes/facts",
            json={"content": "Fact to delete"}
        )
        fact_id = add_response.json()["id"]

        # Delete it
        response = await test_client.delete(f"/api/notes/facts/{fact_id}")
        assert response.status_code == 200

        # Verify it's gone
        list_response = await test_client.get("/api/notes/facts")
        facts = list_response.json()["facts"]
        assert not any(f["id"] == fact_id for f in facts)

    @pytest.mark.asyncio
    async def test_returns_404_for_nonexistent(self, test_client: AsyncClient):
        """Test 404 for nonexistent fact."""
        response = await test_client.delete("/api/notes/facts/99999")
        assert response.status_code == 404


class TestUpdateFact:
    """Tests for PUT /api/notes/facts/{id} endpoint."""

    @pytest.mark.asyncio
    async def test_updates_fact(self, test_client: AsyncClient):
        """Test updating a fact."""
        # Add a fact first
        add_response = await test_client.post(
            "/api/notes/facts",
            json={"content": "Original content"}
        )
        fact_id = add_response.json()["id"]

        # Update it
        response = await test_client.put(
            f"/api/notes/facts/{fact_id}",
            json={"content": "Updated content"}
        )
        assert response.status_code == 200
        assert response.json()["content"] == "Updated content"

    @pytest.mark.asyncio
    async def test_returns_404_for_nonexistent(self, test_client: AsyncClient):
        """Test 404 for nonexistent fact."""
        response = await test_client.put(
            "/api/notes/facts/99999",
            json={"content": "New content"}
        )
        assert response.status_code == 404


class TestFactsLanguageRooms:
    """Each language room has its own student profile."""

    @pytest.mark.asyncio
    async def test_returns_only_the_rooms_facts(self, test_client: AsyncClient, async_session):
        from app.db.models import StudentFact

        async_session.add_all([
            StudentFact(content="Japanese fact", source="listener", language_code="ja"),
            StudentFact(content="French fact", source="listener", language_code="fr"),
        ])
        await async_session.commit()

        response = await test_client.get("/api/notes/facts", params={"language_code": "fr"})

        assert response.status_code == 200
        contents = [f["content"] for f in response.json()["facts"]]
        assert contents == ["French fact"]

    @pytest.mark.asyncio
    async def test_no_filter_returns_all_facts(self, test_client: AsyncClient, async_session):
        from app.db.models import StudentFact

        async_session.add_all([
            StudentFact(content="Japanese fact", source="listener", language_code="ja"),
            StudentFact(content="French fact", source="listener", language_code="fr"),
        ])
        await async_session.commit()

        response = await test_client.get("/api/notes/facts")

        assert response.status_code == 200
        assert len(response.json()["facts"]) == 2

    @pytest.mark.asyncio
    async def test_manual_fact_is_stored_in_its_room(self, test_client: AsyncClient):
        response = await test_client.post(
            "/api/notes/facts",
            json={"content": "Prefers formal French", "language_code": "fr"},
        )

        assert response.status_code == 200
        assert response.json()["language_code"] == "fr"

        fr_facts = await test_client.get("/api/notes/facts", params={"language_code": "fr"})
        ja_facts = await test_client.get("/api/notes/facts", params={"language_code": "ja"})
        assert [f["content"] for f in fr_facts.json()["facts"]] == ["Prefers formal French"]
        assert ja_facts.json()["facts"] == []

    @pytest.mark.asyncio
    async def test_same_fact_can_exist_in_two_rooms(self, test_client: AsyncClient):
        first = await test_client.post(
            "/api/notes/facts",
            json={"content": "Name: Aya", "language_code": "ja"},
        )
        second = await test_client.post(
            "/api/notes/facts",
            json={"content": "Name: Aya", "language_code": "fr"},
        )

        assert first.status_code == 200
        assert second.status_code == 200


class TestGetTokenCount:
    """Tests for GET /api/notes/token-count endpoint."""

    @pytest.mark.asyncio
    async def test_returns_token_count(self, test_client: AsyncClient):
        """Test returns token count."""
        # Add some facts
        await test_client.post(
            "/api/notes/facts",
            json={"content": "This is a test fact with some content"}
        )

        response = await test_client.get("/api/notes/token-count")
        assert response.status_code == 200
        data = response.json()
        assert "token_count" in data
        assert data["token_count"] > 0
