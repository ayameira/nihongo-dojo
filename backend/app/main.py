from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.config import get_settings
from app.db.database import init_db, close_db, get_session
from app.api import chat, vocab, notes, telemetry, config, sessions, media
from app.services.anki_sync import export_anki_to_db
from app.services.anki_importer import import_from_export_db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Nihongo Dojo API...")
    settings = get_settings()

    # Verify Gemini API key
    if not settings.gemini_api_key:
        logger.warning("GEMINI_API_KEY not set. Chat functionality will not work.")
    else:
        logger.info("Gemini API key configured")

    # Initialize database
    await init_db()
    logger.info("Database initialized")

    # Ensure TTS audio cache directory exists
    cache_dir = Path(settings.tts_cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"TTS cache directory ready: {cache_dir}")

    # Sync Anki data on startup
    try:
        logger.info("Syncing Anki collection...")
        export_path = export_anki_to_db()
        if export_path:
            async for session in get_session():
                result = await import_from_export_db(export_path, session)
                logger.info(f"Anki sync complete: {result['imported']} imported, {result['updated']} updated")
                break
        else:
            logger.warning("No Anki data to sync")
    except Exception as e:
        logger.error(f"Anki sync failed: {e}")

    yield

    # Shutdown
    logger.info("Shutting down Nihongo Dojo API...")
    await close_db()


app = FastAPI(
    title="Nihongo Dojo API",
    description="Japanese language learning tutor with Gemini AI",
    version="0.2.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routers
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(vocab.router, prefix="/api/vocab", tags=["vocabulary"])
app.include_router(notes.router, prefix="/api/notes", tags=["notes"])
app.include_router(telemetry.router, prefix="/api/telemetry", tags=["telemetry"])
app.include_router(config.router, prefix="/api/config", tags=["config"])
app.include_router(sessions.router, prefix="/api/sessions", tags=["sessions"])
app.include_router(media.router, prefix="/api/media", tags=["media"])


@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "version": "0.2.0"}
