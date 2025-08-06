"""
Database session factories and dependencies
"""
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker, Session
from .connection import db_manager

# Session factories
AsyncSessionLocal = db_manager.async_session_factory
SessionLocal = db_manager.sync_session_factory

# FastAPI dependency functions
async def get_async_session() -> AsyncSession:
    """FastAPI dependency for async database sessions"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


def get_session() -> Session:
    """FastAPI dependency for sync database sessions"""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()