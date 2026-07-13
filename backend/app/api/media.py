import hashlib
import logging
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel

from app.config import get_settings
from app.core.language_profiles import get_language_profile
from app.services import kokoro_tts
from app.services.tts_service import (
    generate_audio,
    get_speakers,
    TTSServiceUnavailable,
    TTSGenerationError,
)

router = APIRouter()
logger = logging.getLogger(__name__)

# Speaker ids are strings: VOICEVOX style ids ("2"), Kokoro voice names
# ("af_heart"), or this reserved id for the browser's Web Speech API —
# the frontend synthesizes locally instead of calling /tts when selected.
BROWSER_SPEAKER = {
    "id": "browser",
    "name": "Browser TTS",
    "style": "Default",
    "display_name": "Browser voice",
}


@router.get("/speakers")
async def list_speakers(language_code: Optional[str] = None):
    """
    List available speakers/voices for the given target language.

    Japanese uses VOICEVOX, English and French use Kokoro; languages
    without a server engine get the browser-synthesis speaker only.
    """
    profile = get_language_profile(language_code)

    try:
        if profile.tts_engine == "voicevox":
            settings = get_settings()
            speakers = [
                {**speaker, "id": str(speaker["id"])}
                for speaker in await get_speakers()
            ]
            return {
                "speakers": speakers,
                "default_speaker_id": str(settings.default_speaker_id),
            }

        if profile.tts_engine == "kokoro":
            speakers = await kokoro_tts.get_voices(profile.code)
            if speakers:
                return {
                    "speakers": speakers,
                    "default_speaker_id": kokoro_tts.default_voice(profile.code, speakers),
                }

    except TTSServiceUnavailable as e:
        logger.warning(f"TTS server not available: {e}")
        raise HTTPException(
            status_code=503,
            detail=str(e)
        )

    return {
        "speakers": [BROWSER_SPEAKER],
        "default_speaker_id": BROWSER_SPEAKER["id"],
    }


class TTSRequest(BaseModel):
    text: str
    speaker_id: Optional[str] = None
    language_code: Optional[str] = None


def get_cache_path(text: str, speaker_key: str) -> Path:
    """Generate cache file path based on text and speaker key hash."""
    settings = get_settings()
    cache_key = f"{text}_{speaker_key}"
    hash_value = hashlib.md5(cache_key.encode("utf-8")).hexdigest()
    cache_dir = Path(settings.tts_cache_dir)
    return cache_dir / f"{hash_value}.wav"


def ensure_cache_dir() -> None:
    """Create cache directory if it doesn't exist."""
    settings = get_settings()
    cache_dir = Path(settings.tts_cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)


@router.post("/tts")
async def text_to_speech(request: TTSRequest):
    """
    Generate audio via the language's TTS engine (VOICEVOX or Kokoro).

    Uses file-based caching for instant playback of repeated words.
    The cache key is MD5(text + engine-qualified speaker).

    Returns WAV audio data.
    """
    profile = get_language_profile(request.language_code)
    engine = profile.tts_engine
    if engine is None or request.speaker_id == BROWSER_SPEAKER["id"]:
        raise HTTPException(
            status_code=400,
            detail=f"Server TTS is not available for {profile.display_name}; use the browser voice.",
        )

    if engine == "voicevox":
        settings = get_settings()
        try:
            speaker = int(request.speaker_id) if request.speaker_id else settings.default_speaker_id
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid VOICEVOX speaker id: {request.speaker_id}",
            )
    else:
        speaker = request.speaker_id or kokoro_tts.default_voice(profile.code)

    # Ensure cache directory exists
    ensure_cache_dir()

    # Check cache
    cache_path = get_cache_path(request.text, f"{engine}_{speaker}")

    if cache_path.exists():
        logger.info(f"Cache HIT for: {request.text[:30]}...")
        return FileResponse(
            path=cache_path,
            media_type="audio/wav",
            filename="audio.wav"
        )

    # Cache miss - generate audio
    logger.info(f"Cache MISS for: {request.text[:30]}...")

    try:
        if engine == "voicevox":
            audio_data = await generate_audio(request.text, speaker)
        else:
            audio_data = await kokoro_tts.generate_audio(request.text, speaker)

        # Save to cache
        cache_path.write_bytes(audio_data)
        logger.info(f"Cached audio at: {cache_path}")

        return Response(
            content=audio_data,
            media_type="audio/wav",
            headers={"Content-Disposition": "attachment; filename=audio.wav"}
        )

    except TTSServiceUnavailable as e:
        logger.error(f"TTS service unavailable: {e}")
        raise HTTPException(
            status_code=503,
            detail=str(e)
        )
    except TTSGenerationError as e:
        logger.error(f"TTS generation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
