from pathlib import Path
import shutil

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.config import get_settings
from app.core.llm_client import is_llm_configured
from app.db.database import init_db, close_db, get_session
from app.api import chat, vocab, notes, telemetry, config, sessions, media, grammar, anki
from app.services.anki_importer import sync_all_decks

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def _seed_database_if_needed():
    """Copy the pre-seeded nihongo_dojo.db from the repo into the runtime
    location if no database file exists yet (e.g. first deploy on Render)."""
    runtime_db = Path("nihongo_dojo.db")
    # The pre-seeded DB lives next to the backend package inside the repo
    seeded_db = Path(__file__).resolve().parent.parent / "nihongo_dojo.db"

    if not runtime_db.exists() and seeded_db.exists():
        shutil.copy2(seeded_db, runtime_db)
        logger.info(f"Copied pre-seeded database from {seeded_db}")
    elif runtime_db.exists():
        logger.info("Runtime database already exists, skipping seed copy")
    else:
        logger.warning("No pre-seeded database found at %s", seeded_db)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Nihongo Dojo API...")
    settings = get_settings()

    # Verify LLM configuration
    if not is_llm_configured(settings):
        logger.warning("LLM is not configured. Chat functionality will not work.")
    else:
        logger.info(f"LLM configured: {settings.llm_provider} / {settings.llm_model}")

    # Seed the database from the pre-built snapshot if this is a fresh deploy
    _seed_database_if_needed()

    # Initialize database
    await init_db()
    logger.info("Database initialized")

    # Ensure TTS audio cache directory exists
    cache_dir = Path(settings.tts_cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"TTS cache directory ready: {cache_dir}")

    # Sync configured Anki deck sources on startup
    try:
        async for session in get_session():
            results = await sync_all_decks(session)
            if results:
                logger.info(f"Anki sync complete for {len(results)} deck source(s)")
            else:
                logger.info("No Anki deck sources configured; skipping sync")
            break
    except Exception as e:
        logger.error(f"Anki sync failed: {e}")

    # Seed grammar data on startup if table is empty
    try:
        from app.services.grammar_seeder import check_and_seed_grammar
        async for session in get_session():
            result = await check_and_seed_grammar(session)
            if result.get("count", 0) > 0:
                logger.info(f"Grammar seeded: {result['count']} entries")
            break
    except Exception as e:
        logger.error(f"Grammar seed failed: {e}")

    yield

    # Shutdown
    logger.info("Shutting down Nihongo Dojo API...")
    await close_db()


app = FastAPI(
    title="Nihongo Dojo API",
    description="Japanese language learning tutor with pluggable LLM providers",
    version="0.2.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for the portfolio deployment
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
app.include_router(grammar.router, prefix="/api/grammar", tags=["grammar"])
app.include_router(anki.router, prefix="/api/anki", tags=["anki"])


@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "version": "0.2.0"}
