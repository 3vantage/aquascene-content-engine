"""
Database connection and initialization for Web Scraper Service
"""

import asyncpg
import logging
from typing import Optional

from ..config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


async def init_database() -> None:
    """Initialize database connection and create tables if needed"""
    try:
        conn = await asyncpg.connect(settings.DATABASE_URL)
        
        # Create scraping jobs table if it doesn't exist
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS scrape_jobs (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                url TEXT NOT NULL,
                status VARCHAR(20) NOT NULL DEFAULT 'queued',
                content_type VARCHAR(50) DEFAULT 'article',
                priority INTEGER DEFAULT 1,
                tags JSONB DEFAULT '[]',
                content JSONB,
                error_message TEXT,
                attempts INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_scrape_jobs_status ON scrape_jobs(status)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_scrape_jobs_created_at ON scrape_jobs(created_at)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_scrape_jobs_url ON scrape_jobs(url)")
        
        # Create scraped content table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS scraped_content (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                job_id UUID REFERENCES scrape_jobs(id) ON DELETE CASCADE,
                url TEXT NOT NULL,
                title TEXT,
                content TEXT,
                images JSONB DEFAULT '[]',
                links JSONB DEFAULT '[]',
                metadata JSONB DEFAULT '{}',
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                content_hash VARCHAR(64),
                UNIQUE(url, content_hash)
            )
        """)
        
        # Create indexes for scraped content
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_scraped_content_url ON scraped_content(url)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_scraped_content_scraped_at ON scraped_content(scraped_at)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_scraped_content_hash ON scraped_content(content_hash)")
        
        await conn.close()
        logger.info("Database initialized successfully for Web Scraper Service")
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


async def get_db_connection() -> asyncpg.Connection:
    """Get a database connection"""
    return await asyncpg.connect(settings.DATABASE_URL)