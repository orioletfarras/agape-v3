from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)
from app.infrastructure.config import settings


class DatabaseConnection:
    """Database connection manager for Aurora MySQL"""

    def __init__(self):
        self._writer_engine = None
        self._reader_engine = None
        self._async_session_maker = None
        self._reader_session_maker = None

    def initialize(self):
        """Initialize database engines and session makers"""

        # Writer engine (for writes)
        self._writer_engine = create_async_engine(
            settings.DATABASE_URL,
            echo=settings.DB_ECHO,
            pool_size=settings.DB_POOL_SIZE,
            max_overflow=settings.DB_MAX_OVERFLOW,
            pool_timeout=settings.DB_POOL_TIMEOUT,
            pool_recycle=settings.DB_POOL_RECYCLE,
            pool_pre_ping=True,  # Verify connections before using
        )

        self._async_session_maker = async_sessionmaker(
            self._writer_engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )

        # Reader engine (optional - for read replicas)
        if settings.DATABASE_READER_URL:
            self._reader_engine = create_async_engine(
                settings.DATABASE_READER_URL,
                echo=settings.DB_ECHO,
                pool_size=settings.DB_POOL_SIZE,
                max_overflow=settings.DB_MAX_OVERFLOW,
                pool_timeout=settings.DB_POOL_TIMEOUT,
                pool_recycle=settings.DB_POOL_RECYCLE,
                pool_pre_ping=True,
            )

            self._reader_session_maker = async_sessionmaker(
                self._reader_engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autocommit=False,
                autoflush=False,
            )

    async def close(self):
        """Close all database connections"""
        if self._writer_engine:
            await self._writer_engine.dispose()
        if self._reader_engine:
            await self._reader_engine.dispose()

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get database session for writes"""
        if not self._async_session_maker:
            raise RuntimeError("Database not initialized. Call initialize() first.")

        async with self._async_session_maker() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    async def get_reader_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get database session for reads (from read replica if configured)"""
        session_maker = self._reader_session_maker or self._async_session_maker

        if not session_maker:
            raise RuntimeError("Database not initialized. Call initialize() first.")

        async with session_maker() as session:
            try:
                yield session
            finally:
                await session.close()


# Global database connection instance
db = DatabaseConnection()


# Dependency for FastAPI
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for database sessions"""
    async for session in db.get_session():
        yield session


async def get_reader_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for read-only database sessions"""
    async for session in db.get_reader_session():
        yield session
