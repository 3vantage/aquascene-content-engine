"""
Configuration settings for the Subscriber Manager Service
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
    REDIS_URL: str = "redis://localhost:6379/4"
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None
    
    # Security
    JWT_SECRET: str = "your-jwt-secret-key-here"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 30
    ENCRYPTION_KEY: str = "your-32-char-encryption-key-here"
    
    # Email Configuration
    SENDGRID_API_KEY: str = "your-sendgrid-api-key-here"
    SENDER_EMAIL: str = "noreply@aquascene.com"
    SENDER_NAME: str = "AquaScene Team"
    
    # Service Configuration
    SERVICE_HOST: str = "0.0.0.0"
    SERVICE_PORT: int = 8004
    
    # Logging
    LOG_LEVEL: str = "info"
    
    # Health Check
    HEALTH_CHECK_TIMEOUT: int = 10
    HEALTH_CHECK_INTERVAL: int = 30
    HEALTH_CHECK_RETRIES: int = 3
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 3600  # 1 hour
    
    # Email Templates
    WELCOME_EMAIL_TEMPLATE: str = "welcome"
    RESET_PASSWORD_TEMPLATE: str = "reset_password"
    NEWSLETTER_TEMPLATE: str = "newsletter"
    
    # Subscription Settings
    DEFAULT_SUBSCRIPTION_STATUS: str = "pending"
    CONFIRM_EMAIL_EXPIRE_HOURS: int = 24
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()