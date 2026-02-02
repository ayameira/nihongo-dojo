import hashlib
import logging
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel

from app.config import get_settings
from app.services.tts_service import (
    generate_audio,
    get_speakers,
    TTSServiceUnavailable,
    TTSGenerationError,
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/speakers")
async def list_speakers():
    """
    List available VOICEVOX speakers/voices.

    Returns a list of speakers with their style variations.
    """
    try:
        speakers = await get_speakers()
        settings = get_settings()
        return {
            "speakers": speakers,
            "default_speaker_id": settings.default_speaker_id
        }
    except TTSServiceUnavailable as e:
        logger.warning(f"VOICEVOX not available: {e}")
        raise HTTPException(
            status_code=503,
            detail=str(e)
        )


class TTSRequest(BaseModel):
    text: str
    speaker_id: Optional[int] = None


def get_cache_path(text: str, speaker_id: int) -> Path:
    """Generate cache file path based on text and speaker ID hash."""
    settings = get_settings()
    cache_key = f"{text}_{speaker_id}"
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
    Generate audio from Japanese text using VOICEVOX.

    Uses file-based caching for instant playback of repeated words.
    The cache key is MD5(text_speakerId).

    Returns WAV audio data.
    """
    settings = get_settings()
    speaker_id = request.speaker_id or settings.default_speaker_id

    # Ensure cache directory exists
    ensure_cache_dir()

    # Check cache
    cache_path = get_cache_path(request.text, speaker_id)

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
        audio_data = await generate_audio(request.text, speaker_id)

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
