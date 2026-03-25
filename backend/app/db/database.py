from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings

settings = get_settings()

# Ensure the config directory exists before creating the engine.
# Uses try/except so this doesn't crash in read-only test environments.
try:
    settings.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
except OSError:
    pass

engine = create_async_engine(
    settings.DB_URL,
    echo=settings.DEBUG,
    connect_args={"check_same_thread": False},
    # Keep a single connection for SQLite (no multi-worker concern with 1 worker)
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency — yields a DB session and closes it after the request."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
