"""
Database infrastructure: async SQLAlchemy engine, session management, initialization.
"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from app.infrastructure.config import get_settings

settings = get_settings()


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


class DatabaseManager:
    """Manages database engine and session lifecycle."""

    def __init__(self) -> None:
        self._engine: AsyncEngine | None = None
        self._session_factory: async_sessionmaker[AsyncSession] | None = None

    def initialize(self) -> None:
        """Create engine and session factory."""
        if self._engine is not None:
            return

        db_settings = settings.database

        # Create async engine
        self._engine = create_async_engine(
            str(db_settings.url),
            pool_size=db_settings.pool_size,
            max_overflow=db_settings.max_overflow,
            pool_timeout=db_settings.pool_timeout,
            pool_recycle=db_settings.pool_recycle,
            pool_pre_ping=True,
            echo=db_settings.echo and settings.is_development,
            # Use NullPool for testing
            poolclass=NullPool if settings.is_development and "test" in str(db_settings.url) else None,
        )

        # Add connection event listeners for debugging
        @event.listens_for(self._engine.sync_engine, "connect")
        def set_timezone(dbapi_connection, connection_record):
            """Set timezone to UTC for all connections."""
            cursor = dbapi_connection.cursor()
            cursor.execute("SET TIME ZONE 'UTC'")
            cursor.close()

        # Session factory
        self._session_factory = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )

    async def close(self) -> None:
        """Dispose of engine."""
        if self._engine:
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None

    @property
    def engine(self) -> AsyncEngine:
        if self._engine is None:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        return self._engine

    @property
    def session_factory(self) -> async_sessionmaker[AsyncSession]:
        if self._session_factory is None:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        return self._session_factory

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """Provide a transactional session."""
        async with self.session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    @asynccontextmanager
    async def transaction(self) -> AsyncGenerator[AsyncSession, None]:
        """Provide a session with explicit transaction control."""
        async with self.session_factory() as session:
            async with session.begin():
                try:
                    yield session
                except Exception:
                    await session.rollback()
                    raise


# Global database manager instance
db_manager = DatabaseManager()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for database session."""
    async with db_manager.session() as session:
        yield session


async def init_db() -> None:
    """Initialize database: create tables if they don't exist."""
    db_manager.initialize()
    # Tables created via Alembic migrations, not here
    # This function ensures engine is ready
    async with db_manager.engine.begin() as conn:
        # Verify connection
        await conn.execute(__import__("sqlalchemy").text("SELECT 1"))


async def close_db() -> None:
    """Close database connections."""
    await db_manager.close()