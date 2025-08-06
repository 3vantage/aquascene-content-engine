"""
Database connection and initialization for Subscriber Manager Service
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
        
        # Create users table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                first_name VARCHAR(100),
                last_name VARCHAR(100),
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create subscribers table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS subscribers (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                email VARCHAR(255) UNIQUE NOT NULL,
                first_name VARCHAR(100),
                last_name VARCHAR(100),
                interests JSONB DEFAULT '[]',
                status VARCHAR(20) DEFAULT 'pending',
                confirmation_token VARCHAR(255),
                token_expires TIMESTAMP,
                confirmed_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create email_campaigns table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS email_campaigns (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                subject VARCHAR(255) NOT NULL,
                content TEXT NOT NULL,
                template_name VARCHAR(100),
                status VARCHAR(20) DEFAULT 'draft',
                scheduled_at TIMESTAMP,
                sent_at TIMESTAMP,
                recipient_count INTEGER DEFAULT 0,
                delivered_count INTEGER DEFAULT 0,
                opened_count INTEGER DEFAULT 0,
                clicked_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create email_logs table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS email_logs (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                subscriber_id UUID REFERENCES subscribers(id) ON DELETE CASCADE,
                campaign_id UUID REFERENCES email_campaigns(id) ON DELETE CASCADE,
                email VARCHAR(255) NOT NULL,
                status VARCHAR(20) NOT NULL,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                opened_at TIMESTAMP,
                clicked_at TIMESTAMP,
                error_message TEXT
            )
        """)
        
        # Create indexes
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_subscribers_email ON subscribers(email)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_subscribers_status ON subscribers(status)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_subscribers_created_at ON subscribers(created_at)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_email_logs_subscriber_id ON email_logs(subscriber_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_email_logs_campaign_id ON email_logs(campaign_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_email_campaigns_status ON email_campaigns(status)")
        
        await conn.close()
        logger.info("Database initialized successfully for Subscriber Manager Service")
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


async def get_db_connection() -> asyncpg.Connection:
    """Get a database connection"""
    return await asyncpg.connect(settings.DATABASE_URL)