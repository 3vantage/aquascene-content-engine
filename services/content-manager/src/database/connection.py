"""
Database connection management
"""
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, Engine

from ..config.settings import get_settings
from ..models.base import Base

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Database connection and session manager"""
    
    def __init__(self):
        self.settings = get_settings()
        self._async_engine: Optional[AsyncEngine] = None
        self._sync_engine: Optional[Engine] = None
        self._async_session_factory = None
        self._sync_session_factory = None
    
    @property
    def async_engine(self) -> AsyncEngine:
        """Get or create async database engine"""
        if self._async_engine is None:
            if not self.settings.database_url:
                raise ValueError("DATABASE_URL not configured")
            
            # Convert postgres:// to postgresql+asyncpg://
            database_url = self.settings.database_url
            if database_url.startswith('postgres://'):
                database_url = database_url.replace('postgres://', 'postgresql+asyncpg://', 1)
            elif database_url.startswith('postgresql://'):
                database_url = database_url.replace('postgresql://', 'postgresql+asyncpg://', 1)
            
            self._async_engine = create_async_engine(
                database_url,
                echo=self.settings.environment == "development",
                future=True,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,
                pool_recycle=3600,
            )
            
            logger.info("Created async database engine")
        
        return self._async_engine
    
    @property
    def sync_engine(self) -> Engine:
        """Get or create sync database engine"""
        if self._sync_engine is None:
            if not self.settings.database_url:
                raise ValueError("DATABASE_URL not configured")
            
            # Convert to sync postgresql URL
            database_url = self.settings.database_url
            if database_url.startswith('postgres://'):
                database_url = database_url.replace('postgres://', 'postgresql+psycopg2://', 1)
            elif database_url.startswith('postgresql://'):
                database_url = database_url.replace('postgresql://', 'postgresql+psycopg2://', 1)
            
            self._sync_engine = create_engine(
                database_url,
                echo=self.settings.environment == "development",
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,
                pool_recycle=3600,
            )
            
            logger.info("Created sync database engine")
        
        return self._sync_engine
    
    @property 
    def async_session_factory(self):
        """Get or create async session factory"""
        if self._async_session_factory is None:
            self._async_session_factory = async_sessionmaker(
                bind=self.async_engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autoflush=True,
                autocommit=False
            )
        return self._async_session_factory
    
    @property
    def sync_session_factory(self):
        """Get or create sync session factory"""
        if self._sync_session_factory is None:
            self._sync_session_factory = sessionmaker(
                bind=self.sync_engine,
                autoflush=True,
                autocommit=False
            )
        return self._sync_session_factory
    
    async def create_tables(self):
        """Create all database tables"""
        async with self.async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created")
    
    async def close(self):
        """Close database connections"""
        if self._async_engine:
            await self._async_engine.dispose()
            logger.info("Closed async database connections")
        
        if self._sync_engine:
            self._sync_engine.dispose()
            logger.info("Closed sync database connections")


# Global database manager instance
db_manager = DatabaseManager()


@asynccontextmanager
async def get_async_db_session():
    """Dependency to get async database session"""
    async with db_manager.async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            await session.close()


def get_db_session():
    """Dependency to get sync database session"""
    session = db_manager.sync_session_factory()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database session error: {e}")
        raise
    finally:
        session.close()


# Import AsyncSession after engine creation to avoid circular imports
from sqlalchemy.ext.asyncio import AsyncSession