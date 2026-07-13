"""
Tests for language gating and engine dispatch on the media (TTS) API.
"""
import dataclasses

import pytest
from httpx import AsyncClient

from app.core.language_profiles import get_language_profile
from app.services.tts_service import TTSServiceUnavailable


def _profile_without_engine():
    """All registered languages currently have a server TTS engine, so the
    browser-only path is exercised with a profile stripped of its engine."""
    return dataclasses.replace(get_language_profile("fr"), tts_engine=None)


class TestSpeakersLanguageGating:
    """Tests for GET /api/media/speakers."""

    @pytest.mark.asyncio
    async def test_language_without_server_tts_gets_browser_speaker_only(self, test_client: AsyncClient, monkeypatch):
        profile = _profile_without_engine()
        monkeypatch.setattr("app.api.media.get_language_profile", lambda code=None: profile)

        response = await test_client.get("/api/media/speakers", params={"language_code": "fr"})

        assert response.status_code == 200
        data = response.json()
        assert data["default_speaker_id"] == "browser"
        assert [speaker["id"] for speaker in data["speakers"]] == ["browser"]

    @pytest.mark.asyncio
    async def test_kokoro_language_lists_kokoro_voices(self, test_client: AsyncClient, monkeypatch):
        async def fake_get_voices(language_code):
            assert language_code == "fr"
            return [
                {"id": "ff_siwis", "name": "Siwis", "style": "French female", "display_name": "Siwis (French female)"},
            ]

        monkeypatch.setattr("app.api.media.kokoro_tts.get_voices", fake_get_voices)

        response = await test_client.get("/api/media/speakers", params={"language_code": "fr"})

        assert response.status_code == 200
        data = response.json()
        assert data["default_speaker_id"] == "ff_siwis"
        assert [speaker["id"] for speaker in data["speakers"]] == ["ff_siwis"]

    @pytest.mark.asyncio
    async def test_english_default_prefers_af_heart(self, test_client: AsyncClient, monkeypatch):
        async def fake_get_voices(language_code):
            return [
                {"id": "af_bella", "name": "Bella", "style": "US female", "display_name": "Bella (US female)"},
                {"id": "af_heart", "name": "Heart", "style": "US female", "display_name": "Heart (US female)"},
            ]

        monkeypatch.setattr("app.api.media.kokoro_tts.get_voices", fake_get_voices)

        response = await test_client.get("/api/media/speakers", params={"language_code": "en"})

        assert response.status_code == 200
        assert response.json()["default_speaker_id"] == "af_heart"

    @pytest.mark.asyncio
    async def test_kokoro_unreachable_returns_503(self, test_client: AsyncClient, monkeypatch):
        async def fake_get_voices(language_code):
            raise TTSServiceUnavailable("Kokoro is not running")

        monkeypatch.setattr("app.api.media.kokoro_tts.get_voices", fake_get_voices)

        response = await test_client.get("/api/media/speakers", params={"language_code": "en"})

        assert response.status_code == 503

    @pytest.mark.asyncio
    async def test_kokoro_without_matching_voices_falls_back_to_browser(self, test_client: AsyncClient, monkeypatch):
        async def fake_get_voices(language_code):
            return []

        monkeypatch.setattr("app.api.media.kokoro_tts.get_voices", fake_get_voices)

        response = await test_client.get("/api/media/speakers", params={"language_code": "fr"})

        assert response.status_code == 200
        data = response.json()
        assert data["default_speaker_id"] == "browser"
        assert [speaker["id"] for speaker in data["speakers"]] == ["browser"]


class TestTTSLanguageGating:
    """Tests for POST /api/media/tts."""

    @pytest.mark.asyncio
    async def test_tts_rejected_for_language_without_server_tts(self, test_client: AsyncClient, monkeypatch):
        profile = _profile_without_engine()
        monkeypatch.setattr("app.api.media.get_language_profile", lambda code=None: profile)

        response = await test_client.post(
            "/api/media/tts",
            json={"text": "bonjour", "language_code": "fr"},
        )

        assert response.status_code == 400
        assert "browser voice" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_tts_rejected_for_browser_speaker(self, test_client: AsyncClient):
        response = await test_client.post(
            "/api/media/tts",
            json={"text": "hello", "language_code": "en", "speaker_id": "browser"},
        )

        assert response.status_code == 400
        assert "browser voice" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_tts_routes_to_kokoro(
        self, test_client: AsyncClient, monkeypatch, tmp_path, test_settings
    ):
        test_settings.tts_cache_dir = str(tmp_path)
        monkeypatch.setattr("app.api.media.get_settings", lambda: test_settings)

        called = {}

        async def fake_generate(text, voice):
            called["args"] = (text, voice)
            return b"RIFF-fake-wav"

        monkeypatch.setattr("app.api.media.kokoro_tts.generate_audio", fake_generate)

        response = await test_client.post(
            "/api/media/tts",
            json={"text": "bonjour", "language_code": "fr", "speaker_id": "ff_siwis"},
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "audio/wav"
        assert response.content == b"RIFF-fake-wav"
        assert called["args"] == ("bonjour", "ff_siwis")

    @pytest.mark.asyncio
    async def test_tts_rejects_non_numeric_voicevox_speaker(self, test_client: AsyncClient):
        response = await test_client.post(
            "/api/media/tts",
            json={"text": "こんにちは", "language_code": "ja", "speaker_id": "af_heart"},
        )

        assert response.status_code == 400
        assert "Invalid VOICEVOX speaker id" in response.json()["detail"]
