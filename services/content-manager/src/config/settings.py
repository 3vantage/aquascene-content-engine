"""
Content Manager Settings
"""
from functools import lru_cache
from typing import List, Optional

from pydantic import Field, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    # Server configuration
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8002, env="PORT")  # Different port from AI processor
    environment: str = Field(default="development", env="ENVIRONMENT")
    
    # Database
    database_url: Optional[str] = Field(None, env="DATABASE_URL")
    redis_url: Optional[str] = Field(None, env="REDIS_URL")
    
    # External services
    ai_processor_url: str = Field(default="http://ai-processor:8001", env="AI_PROCESSOR_URL")
    web_scraper_url: str = Field(default="http://web-scraper:8003", env="WEB_SCRAPER_URL")
    
    # Airtable integration
    airtable_api_key: Optional[str] = Field(None, env="AIRTABLE_API_KEY")
    airtable_base_id: Optional[str] = Field(None, env="AIRTABLE_BASE_ID")
    
    # Security
    allowed_origins: List[str] = Field(default=["*"], env="ALLOWED_ORIGINS")
    secret_key: str = Field(default="content-manager-secret-key", env="SECRET_KEY")
    
    # Content management
    auto_approve_threshold: float = Field(default=0.85, env="AUTO_APPROVE_THRESHOLD")
    max_content_age_days: int = Field(default=365, env="MAX_CONTENT_AGE_DAYS")
    
    # Workflow settings
    batch_processing_size: int = Field(default=10, env="BATCH_PROCESSING_SIZE")
    workflow_timeout_minutes: int = Field(default=30, env="WORKFLOW_TIMEOUT_MINUTES")
    
    # Newsletter settings
    default_newsletter_frequency: str = Field(default="weekly", env="DEFAULT_NEWSLETTER_FREQUENCY")
    max_newsletter_content_items: int = Field(default=10, env="MAX_NEWSLETTER_CONTENT_ITEMS")
    
    # Social media settings
    instagram_optimal_hours: List[int] = Field(default=[9, 12, 17], env="INSTAGRAM_OPTIMAL_HOURS")
    social_posting_interval_minutes: int = Field(default=30, env="SOCIAL_POSTING_INTERVAL_MINUTES")
    
    # Monitoring
    enable_metrics: bool = Field(default=True, env="ENABLE_METRICS")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    @validator('allowed_origins', pre=True)
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',')]
        return v
    
    @validator('environment')
    def validate_environment(cls, v):
        valid_environments = ['development', 'staging', 'production', 'testing']
        if v not in valid_environments:
            raise ValueError(f'Environment must be one of: {valid_environments}')
        return v
    
    @validator('auto_approve_threshold')
    def validate_threshold(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('Auto approve threshold must be between 0.0 and 1.0')
        return v
    
    @validator('default_newsletter_frequency')
    def validate_newsletter_frequency(cls, v):
        valid_frequencies = ['daily', 'weekly', 'bi_weekly', 'monthly']
        if v not in valid_frequencies:
            raise ValueError(f'Newsletter frequency must be one of: {valid_frequencies}')
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()