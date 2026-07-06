from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import event, text
from app.config import get_settings
from app.db.models import Base

engine = None
async_session_maker = None


async def _run_migrations(conn):
    """Lightweight, idempotent schema migrations for the SQLite database.

    This repo ships without Alembic, so columns added after a database has
    already been created are patched in here by hand.
    """
    async def ensure_column(table: str, column: str, ddl: str, backfill: str | None = None):
        result = await conn.execute(text(f"PRAGMA table_info({table})"))
        columns = {row[1] for row in result.fetchall()}
        if column not in columns:
            await conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {ddl}"))
            if backfill:
                await conn.execute(text(backfill))

    await ensure_column(
        "vocab_entries",
        "deck_config_id",
        "deck_config_id INTEGER",
    )
    await ensure_column(
        "vocab_entries",
        "language_code",
        "language_code VARCHAR(10) DEFAULT 'ja' NOT NULL",
        "UPDATE vocab_entries SET language_code = 'ja' WHERE language_code IS NULL",
    )
    await ensure_column(
        "anki_deck_configs",
        "language_code",
        "language_code VARCHAR(10) DEFAULT 'ja' NOT NULL",
        "UPDATE anki_deck_configs SET language_code = 'ja' WHERE language_code IS NULL",
    )
    await ensure_column(
        "chat_sessions",
        "language_code",
        "language_code VARCHAR(10) DEFAULT 'ja' NOT NULL",
        "UPDATE chat_sessions SET language_code = 'ja' WHERE language_code IS NULL",
    )
    await ensure_column(
        "student_facts",
        "language_code",
        "language_code VARCHAR(10)",
    )
    await ensure_column(
        "grammar_entries",
        "language_code",
        "language_code VARCHAR(10) DEFAULT 'ja' NOT NULL",
        "UPDATE grammar_entries SET language_code = 'ja' WHERE language_code IS NULL",
    )


async def init_db():
    global engine, async_session_maker
    settings = get_settings()

    engine = create_async_engine(
        settings.database_url,
        echo=False,
    )

    async_session_maker = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await _run_migrations(conn)


async def close_db():
    global engine
    if engine:
        await engine.dispose()


async def get_session() -> AsyncSession:
    global async_session_maker
    if async_session_maker is None:
        await init_db()
    async with async_session_maker() as session:
        yield session
