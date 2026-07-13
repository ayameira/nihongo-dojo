"""
Tests for Kokoro voice list parsing and speaker shaping.
"""
from app.services.kokoro_tts import (
    _normalize_voice_ids,
    _voice_to_speaker,
    default_voice,
)


def test_normalize_accepts_plain_names():
    assert _normalize_voice_ids(["af_heart", "ff_siwis"]) == ["af_heart", "ff_siwis"]


def test_normalize_accepts_id_objects():
    voices = [
        {"id": "af_heart", "name": "af_heart"},
        {"id": "ff_siwis", "name": "ff_siwis"},
    ]
    assert _normalize_voice_ids(voices) == ["af_heart", "ff_siwis"]


def test_normalize_skips_empty_entries():
    assert _normalize_voice_ids([{"name": ""}, "", "bf_emma"]) == ["bf_emma"]


def test_voice_to_speaker_labels_known_prefixes():
    speaker = _voice_to_speaker("ff_siwis")

    assert speaker["id"] == "ff_siwis"
    assert speaker["display_name"] == "Siwis (French female)"


def test_default_voice_prefers_known_voice():
    speakers = [_voice_to_speaker("af_bella"), _voice_to_speaker("af_heart")]

    assert default_voice("en", speakers) == "af_heart"
    assert default_voice("en", [_voice_to_speaker("af_bella")]) == "af_bella"
