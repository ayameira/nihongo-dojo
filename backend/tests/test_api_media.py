"""
Tests for language gating on the media (TTS) API.
"""
import pytest
from httpx import AsyncClient


class TestSpeakersLanguageGating:
    """Tests for GET /api/media/speakers."""

    @pytest.mark.asyncio
    async def test_language_without_server_tts_gets_browser_speaker_only(self, test_client: AsyncClient):
        response = await test_client.get("/api/media/speakers", params={"language_code": "es"})

        assert response.status_code == 200
        data = response.json()
        assert data["default_speaker_id"] == 0
        assert [speaker["id"] for speaker in data["speakers"]] == [0]


class TestTTSLanguageGating:
    """Tests for POST /api/media/tts."""

    @pytest.mark.asyncio
    async def test_tts_rejected_for_language_without_server_tts(self, test_client: AsyncClient):
        response = await test_client.post(
            "/api/media/tts",
            json={"text": "hola", "language_code": "es"},
        )

        assert response.status_code == 400
        assert "browser voice" in response.json()["detail"]
