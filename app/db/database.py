"""Database configuration and session management."""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings


settings = get_settings()

engine = create_async_engine(
    settings.database_url,
    echo=settings.environment == "development",
    future=True,
)

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Base class for all models."""
    pass


async def get_db() -> AsyncSession:
    """Dependency to get database session."""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Initialize database tables."""
    # Skip DB init if using in-memory SQLite (for testing)
    if ":memory:" in settings.database_url or settings.database_url.startswith("sqlite"):
        # For SQLite in-memory, tables are created on first connection
        # Skip init to avoid issues with :memory: databases
        return

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
