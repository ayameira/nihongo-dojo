"""
API tests for vocabulary routes.
"""
import pytest


class TestListVocab:
    """Tests for GET /api/vocab endpoint."""

    @pytest.mark.asyncio
    async def test_returns_empty_when_no_vocab(self, test_client):
        """Test that empty items list is returned when no vocab exists."""
        response = await test_client.get("/api/vocab")

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_returns_vocab_with_pagination(self, test_client, sample_vocab):
        """Test that vocab is returned with pagination info."""
        response = await test_client.get("/api/vocab")

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["total"] == 1
        assert data["page"] == 1
        assert data["limit"] == 50

    @pytest.mark.asyncio
    async def test_filters_by_status(self, test_client, sample_vocab):
        """Test filtering vocab by status."""
        # sample_vocab has status="Learning"
        response = await test_client.get("/api/vocab?status=Learning")
        assert response.status_code == 200
        assert len(response.json()["items"]) == 1

        response = await test_client.get("/api/vocab?status=New")
        assert response.status_code == 200
        assert len(response.json()["items"]) == 0

    @pytest.mark.asyncio
    async def test_search_by_kanji(self, test_client, sample_vocab):
        """Test searching by kanji."""
        response = await test_client.get("/api/vocab?search=食べ")

        assert response.status_code == 200
        assert len(response.json()["items"]) == 1

    @pytest.mark.asyncio
    async def test_search_by_meaning(self, test_client, sample_vocab):
        """Test searching by meaning."""
        response = await test_client.get("/api/vocab?search=eat")

        assert response.status_code == 200
        assert len(response.json()["items"]) == 1

    @pytest.mark.asyncio
    async def test_pagination_params(self, test_client, sample_vocab):
        """Test custom pagination parameters."""
        response = await test_client.get("/api/vocab?page=1&limit=10")

        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["limit"] == 10


class TestGetLearningVocab:
    """Tests for GET /api/vocab/learning endpoint."""

    @pytest.mark.asyncio
    async def test_returns_only_learning(self, test_client, sample_vocab):
        """Test that only Learning status vocab is returned."""
        response = await test_client.get("/api/vocab/learning")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert all(v["status"] == "Learning" for v in data)

    @pytest.mark.asyncio
    async def test_respects_limit(self, test_client, sample_vocab):
        """Test that limit parameter is respected."""
        response = await test_client.get("/api/vocab/learning?limit=1")

        assert response.status_code == 200
        assert len(response.json()) <= 1


class TestGetVocabStats:
    """Tests for GET /api/vocab/stats endpoint."""

    @pytest.mark.asyncio
    async def test_returns_all_stats(self, test_client, sample_vocab):
        """Test that all status counts are returned."""
        response = await test_client.get("/api/vocab/stats")

        assert response.status_code == 200
        data = response.json()
        assert "new" in data
        assert "learning" in data
        assert "mature" in data
        assert "total" in data
        assert data["total"] == 1


class TestGetVocab:
    """Tests for GET /api/vocab/{vocab_id} endpoint."""

    @pytest.mark.asyncio
    async def test_returns_vocab_by_id(self, test_client, sample_vocab):
        """Test retrieving vocab by ID."""
        response = await test_client.get(f"/api/vocab/{sample_vocab.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_vocab.id
        assert data["kanji"] == sample_vocab.kanji

    @pytest.mark.asyncio
    async def test_returns_404_for_nonexistent(self, test_client):
        """Test that 404 is returned for non-existent vocab."""
        response = await test_client.get("/api/vocab/99999")

        assert response.status_code == 404


class TestCreateVocab:
    """Tests for POST /api/vocab endpoint."""

    @pytest.mark.asyncio
    async def test_creates_vocab(self, test_client):
        """Test creating new vocabulary."""
        response = await test_client.post("/api/vocab", json={
            "kanji": "走る",
            "kana": "はしる",
            "meaning": "to run",
            "pos": "verb",
        })

        assert response.status_code == 200
        data = response.json()
        assert data["kanji"] == "走る"
        assert data["kana"] == "はしる"
        assert data["status"] == "New"
        assert data["source"] == "manual"

    @pytest.mark.asyncio
    async def test_creates_kana_only_vocab(self, test_client):
        """Test creating kana-only vocabulary."""
        response = await test_client.post("/api/vocab", json={
            "kana": "これ",
            "meaning": "this",
        })

        assert response.status_code == 200
        data = response.json()
        assert data["kanji"] is None
        assert data["kana"] == "これ"


class TestUpdateVocab:
    """Tests for PUT /api/vocab/{vocab_id} endpoint."""

    @pytest.mark.asyncio
    async def test_updates_vocab_fields(self, test_client, sample_vocab):
        """Test updating vocabulary fields."""
        response = await test_client.put(
            f"/api/vocab/{sample_vocab.id}",
            json={"meaning": "to eat (updated)"}
        )

        assert response.status_code == 200
        assert response.json()["meaning"] == "to eat (updated)"

    @pytest.mark.asyncio
    async def test_updates_status(self, test_client, sample_vocab):
        """Test updating vocabulary status."""
        response = await test_client.put(
            f"/api/vocab/{sample_vocab.id}",
            json={"status": "Mature"}
        )

        assert response.status_code == 200
        assert response.json()["status"] == "Mature"

    @pytest.mark.asyncio
    async def test_returns_404_for_nonexistent(self, test_client):
        """Test that 404 is returned for non-existent vocab."""
        response = await test_client.put(
            "/api/vocab/99999",
            json={"meaning": "test"}
        )

        assert response.status_code == 404


class TestDeleteVocab:
    """Tests for DELETE /api/vocab/{vocab_id} endpoint."""

    @pytest.mark.asyncio
    async def test_deletes_vocab(self, test_client, sample_vocab):
        """Test deleting vocabulary."""
        response = await test_client.delete(f"/api/vocab/{sample_vocab.id}")

        assert response.status_code == 200
        assert "deleted" in response.json()["message"].lower()

        # Verify deletion
        get_response = await test_client.get(f"/api/vocab/{sample_vocab.id}")
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_returns_404_for_nonexistent(self, test_client):
        """Test that 404 is returned for non-existent vocab."""
        response = await test_client.delete("/api/vocab/99999")

        assert response.status_code == 404


class TestMarkSeen:
    """Tests for POST /api/vocab/{vocab_id}/seen endpoint."""

    @pytest.mark.asyncio
    async def test_increments_times_seen(self, test_client, sample_vocab):
        """Test incrementing times_seen counter."""
        initial_seen = sample_vocab.times_seen

        response = await test_client.post(f"/api/vocab/{sample_vocab.id}/seen")

        assert response.status_code == 200
        assert response.json()["times_seen"] == initial_seen + 1

    @pytest.mark.asyncio
    async def test_returns_404_for_nonexistent(self, test_client):
        """Test that 404 is returned for non-existent vocab."""
        response = await test_client.post("/api/vocab/99999/seen")

        assert response.status_code == 404


class TestMarkCorrect:
    """Tests for POST /api/vocab/{vocab_id}/correct endpoint."""

    @pytest.mark.asyncio
    async def test_increments_times_correct(self, test_client, sample_vocab):
        """Test incrementing times_correct counter."""
        initial_correct = sample_vocab.times_correct

        response = await test_client.post(f"/api/vocab/{sample_vocab.id}/correct")

        assert response.status_code == 200
        assert response.json()["times_correct"] == initial_correct + 1

    @pytest.mark.asyncio
    async def test_returns_404_for_nonexistent(self, test_client):
        """Test that 404 is returned for non-existent vocab."""
        response = await test_client.post("/api/vocab/99999/correct")

        assert response.status_code == 404
