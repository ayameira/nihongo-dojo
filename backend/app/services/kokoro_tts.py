"""Kokoro-FastAPI text-to-speech integration.

Talks to a user-run Kokoro-FastAPI server (https://github.com/remsky/Kokoro-FastAPI)
over its OpenAI-compatible API, the same way tts_service.py talks to VOICEVOX.
"""
import httpx
import logging
from typing import Any, Dict, List

from app.config import get_settings
from app.services.tts_service import TTSGenerationError, TTSServiceUnavailable

logger = logging.getLogger(__name__)

# Kokoro voice names start with a language+gender prefix: "af"/"am" are
# American English female/male, "bf"/"bm" British English, "ff" French.
LANGUAGE_VOICE_PREFIXES: Dict[str, tuple] = {
    "en": ("af", "am", "bf", "bm"),
    "fr": ("ff", "fm"),
}

PREFIX_LABELS: Dict[str, str] = {
    "af": "US female",
    "am": "US male",
    "bf": "UK female",
    "bm": "UK male",
    "ff": "French female",
    "fm": "French male",
}

# Preferred default voice per language, used when the server has it.
PREFERRED_VOICES: Dict[str, str] = {
    "en": "af_heart",
    "fr": "ff_siwis",
}


def _voice_to_speaker(voice: str) -> Dict[str, Any]:
    prefix, _, name = voice.partition("_")
    label = PREFIX_LABELS.get(prefix, prefix)
    display = name.title() if name else voice
    return {
        "id": voice,
        "name": display,
        "style": label,
        "display_name": f"{display} ({label})",
    }


def _normalize_voice_ids(voices: list) -> List[str]:
    """Kokoro-FastAPI has returned both plain names and {"id": ...} objects
    across versions; accept either shape."""
    names = []
    for voice in voices:
        if isinstance(voice, dict):
            name = voice.get("id") or voice.get("name") or ""
        else:
            name = str(voice)
        if name:
            names.append(name)
    return names


async def get_voices(language_code: str) -> List[Dict[str, Any]]:
    """
    Fetch Kokoro voices for a language, shaped like the speaker dicts
    the frontend already consumes.

    Raises:
        TTSServiceUnavailable: Kokoro server is not running
    """
    settings = get_settings()
    base_url = settings.kokoro_url
    prefixes = LANGUAGE_VOICE_PREFIXES.get(language_code, ())

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{base_url}/v1/audio/voices")

            if response.status_code != 200:
                logger.error(f"Failed to fetch Kokoro voices: {response.status_code}")
                return []

            voices = response.json().get("voices", [])

    except httpx.ConnectError as e:
        logger.error(f"Cannot connect to Kokoro at {base_url}: {e}")
        raise TTSServiceUnavailable(
            f"Kokoro is not running. Please start the Kokoro-FastAPI server. "
            f"Expected at: {base_url}"
        ) from e

    return [
        _voice_to_speaker(voice)
        for voice in _normalize_voice_ids(voices)
        if voice.partition("_")[0] in prefixes
    ]


def default_voice(language_code: str, speakers: List[Dict[str, Any]] | None = None) -> str:
    """Preferred voice for the language, or the first available one."""
    preferred = PREFERRED_VOICES.get(language_code)
    if speakers is None:
        return preferred or ""
    available = {speaker["id"] for speaker in speakers}
    if preferred in available:
        return preferred
    return speakers[0]["id"] if speakers else preferred or ""


async def generate_audio(text: str, voice: str) -> bytes:
    """
    Generate WAV audio from text via Kokoro's OpenAI-compatible endpoint.

    Raises:
        TTSServiceUnavailable: Kokoro server is not running
        TTSGenerationError: Audio generation failed
    """
    settings = get_settings()
    base_url = settings.kokoro_url

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{base_url}/v1/audio/speech",
                json={
                    "model": "kokoro",
                    "input": text,
                    "voice": voice,
                    "response_format": "wav",
                },
            )

            if response.status_code != 200:
                logger.error(
                    f"Kokoro synthesis failed: {response.status_code} - {response.text}"
                )
                raise TTSGenerationError(
                    f"Failed to synthesize audio: {response.status_code}"
                )

            logger.info(f"Generated Kokoro audio for: {text[:30]}... (voice={voice})")
            return response.content

    except httpx.ConnectError as e:
        logger.error(f"Cannot connect to Kokoro at {base_url}: {e}")
        raise TTSServiceUnavailable(
            f"Kokoro is not running. Please start the Kokoro-FastAPI server. "
            f"Expected at: {base_url}"
        ) from e
    except httpx.TimeoutException as e:
        logger.error(f"Kokoro request timed out: {e}")
        raise TTSGenerationError("Audio generation timed out") from e
