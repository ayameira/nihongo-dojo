import httpx
import logging
from typing import List, Dict, Any

from app.config import get_settings

logger = logging.getLogger(__name__)


class TTSServiceUnavailable(Exception):
    """Raised when VOICEVOX engine is unreachable."""
    pass


async def get_speakers() -> List[Dict[str, Any]]:
    """
    Fetch available speakers from VOICEVOX.

    Returns a simplified list of speakers with their styles.
    Each speaker can have multiple styles (e.g., normal, happy, sad).

    Returns:
        List of speaker dictionaries with id, name, and styles

    Raises:
        TTSServiceUnavailable: VOICEVOX is not running
    """
    settings = get_settings()
    base_url = settings.voicevox_url

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{base_url}/speakers")

            if response.status_code != 200:
                logger.error(f"Failed to fetch speakers: {response.status_code}")
                return []

            speakers_data = response.json()

            # Flatten into a simpler structure for the frontend
            speakers = []
            for speaker in speakers_data:
                for style in speaker.get("styles", []):
                    speakers.append({
                        "id": style["id"],
                        "name": speaker["name"],
                        "style": style["name"],
                        "display_name": f"{speaker['name']} ({style['name']})"
                    })

            return speakers

    except httpx.ConnectError as e:
        logger.error(f"Cannot connect to VOICEVOX at {base_url}: {e}")
        raise TTSServiceUnavailable(
            f"VOICEVOX is not running. Please start the VOICEVOX application."
        ) from e


class TTSGenerationError(Exception):
    """Raised when audio generation fails."""
    pass


async def generate_audio(text: str, speaker_id: int | None = None) -> bytes:
    """
    Generate audio from Japanese text using VOICEVOX.

    VOICEVOX requires a two-step process:
    1. POST /audio_query - Get synthesis parameters for the text
    2. POST /synthesis - Generate WAV audio from parameters

    Args:
        text: Japanese text to synthesize
        speaker_id: VOICEVOX speaker ID (defaults to config value)

    Returns:
        WAV audio data as bytes

    Raises:
        TTSServiceUnavailable: VOICEVOX is not running
        TTSGenerationError: Audio generation failed
    """
    settings = get_settings()

    if speaker_id is None:
        speaker_id = settings.default_speaker_id

    base_url = settings.voicevox_url

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Step 1: Generate audio query parameters
            query_response = await client.post(
                f"{base_url}/audio_query",
                params={"text": text, "speaker": speaker_id}
            )

            if query_response.status_code != 200:
                logger.error(
                    f"VOICEVOX audio_query failed: {query_response.status_code} - "
                    f"{query_response.text}"
                )
                raise TTSGenerationError(
                    f"Failed to generate audio query: {query_response.status_code}"
                )

            audio_query = query_response.json()

            # Future-proofing: Modify speedScale or pitchScale here if needed
            # audio_query["speedScale"] = 1.0
            # audio_query["pitchScale"] = 0.0

            # Step 2: Synthesize audio from query
            synthesis_response = await client.post(
                f"{base_url}/synthesis",
                params={"speaker": speaker_id},
                json=audio_query,
                headers={"Content-Type": "application/json"}
            )

            if synthesis_response.status_code != 200:
                logger.error(
                    f"VOICEVOX synthesis failed: {synthesis_response.status_code} - "
                    f"{synthesis_response.text}"
                )
                raise TTSGenerationError(
                    f"Failed to synthesize audio: {synthesis_response.status_code}"
                )

            logger.info(f"Generated TTS audio for: {text[:30]}... (speaker={speaker_id})")
            return synthesis_response.content

    except httpx.ConnectError as e:
        logger.error(f"Cannot connect to VOICEVOX at {base_url}: {e}")
        raise TTSServiceUnavailable(
            f"VOICEVOX is not running. Please start the VOICEVOX application. "
            f"Expected at: {base_url}"
        ) from e
    except httpx.TimeoutException as e:
        logger.error(f"VOICEVOX request timed out: {e}")
        raise TTSGenerationError("Audio generation timed out") from e
