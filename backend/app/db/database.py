from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import event
from app.config import get_settings
from app.db.models import Base

engine = None
async_session_maker = None


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
