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
    result = await conn.execute(text("PRAGMA table_info(vocab_entries)"))
    columns = {row[1] for row in result.fetchall()}
    if "deck_config_id" not in columns:
        await conn.execute(
            text("ALTER TABLE vocab_entries ADD COLUMN deck_config_id INTEGER")
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
