"""
Configuration settings for the Web Scraper Service
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings"""
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Database
    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/content_engine"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/2"
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None
    
    # Scraper Configuration
    SCRAPER_USER_AGENT: str = "AquaSceneBot/1.0"
    SCRAPER_DELAY: int = 2
    SCRAPER_MAX_CONCURRENT: int = 5
    SCRAPER_TIMEOUT: int = 30
    SCRAPER_RETRY_ATTEMPTS: int = 3
    
    # Service Configuration
    SERVICE_HOST: str = "0.0.0.0"
    SERVICE_PORT: int = 8002
    
    # Logging
    LOG_LEVEL: str = "info"
    
    # Health Check
    HEALTH_CHECK_TIMEOUT: int = 10
    HEALTH_CHECK_INTERVAL: int = 30
    HEALTH_CHECK_RETRIES: int = 3
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 3600  # 1 hour
    
    # Content Sources
    ALLOWED_DOMAINS: list = [
        "reddit.com",
        "aquascaping.org",
        "plantedtank.net",
        "barrreport.com",
        "ukaps.org"
    ]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()