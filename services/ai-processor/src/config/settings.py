"""
Application Settings

Configuration management using Pydantic Settings for the AI content processor.
Handles environment variables and configuration validation.
"""

import os
from functools import lru_cache
from typing import Optional, List, Dict, Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    # Server configuration
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8001, env="PORT")
    debug: bool = Field(default=False, env="DEBUG")
    environment: str = Field(default="development", env="ENVIRONMENT")
    
    # LLM API Keys
    openai_api_key: Optional[str] = Field(None, env="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(None, env="ANTHROPIC_API_KEY")
    
    # Ollama configuration
    ollama_base_url: Optional[str] = Field(None, env="OLLAMA_BASE_URL")
    ollama_models: List[str] = Field(
        default=["llama3.1:8b", "mistral:7b"], 
        env="OLLAMA_MODELS"
    )
    
    # Database configuration
    database_url: Optional[str] = Field(None, env="DATABASE_URL")
    redis_url: Optional[str] = Field(None, env="REDIS_URL")
    
    # Content generation settings
    default_temperature: float = Field(default=0.7, env="DEFAULT_TEMPERATURE")
    default_max_tokens: int = Field(default=2000, env="DEFAULT_MAX_TOKENS")
    default_timeout_seconds: int = Field(default=30, env="DEFAULT_TIMEOUT_SECONDS")
    
    # Batch processing settings
    max_concurrent_requests: int = Field(default=5, env="MAX_CONCURRENT_REQUESTS")
    batch_processing_timeout: int = Field(default=3600, env="BATCH_PROCESSING_TIMEOUT")
    max_batch_size: int = Field(default=100, env="MAX_BATCH_SIZE")
    
    # Rate limiting
    requests_per_minute_limit: int = Field(default=100, env="REQUESTS_PER_MINUTE_LIMIT")
    burst_limit: int = Field(default=20, env="BURST_LIMIT")
    
    # Template directories
    template_directories: List[str] = Field(
        default_factory=lambda: [
            "templates",
            "../distributor/templates",
            "/app/templates"
        ],
        env="TEMPLATE_DIRECTORIES"
    )
    
    # Knowledge base settings
    knowledge_base_directory: str = Field(
        default="data/knowledge", 
        env="KNOWLEDGE_BASE_DIRECTORY"
    )
    
    # Monitoring and logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    structured_logging: bool = Field(default=True, env="STRUCTURED_LOGGING")
    sentry_dsn: Optional[str] = Field(None, env="SENTRY_DSN")
    
    # Metrics and monitoring
    enable_metrics: bool = Field(default=True, env="ENABLE_METRICS")
    metrics_port: int = Field(default=9090, env="METRICS_PORT")
    health_check_interval: int = Field(default=30, env="HEALTH_CHECK_INTERVAL")
    
    # Resource management
    max_memory_usage_percent: float = Field(
        default=80.0, 
        env="MAX_MEMORY_USAGE_PERCENT"
    )
    max_cpu_usage_percent: float = Field(
        default=90.0, 
        env="MAX_CPU_USAGE_PERCENT"
    )
    max_active_jobs: int = Field(default=10, env="MAX_ACTIVE_JOBS")
    
    # Security settings
    api_key: Optional[str] = Field(None, env="API_KEY")
    allowed_origins: List[str] = Field(
        default=["*"], 
        env="ALLOWED_ORIGINS"
    )
    
    # Content optimization settings
    enable_seo_optimization: bool = Field(default=True, env="ENABLE_SEO_OPTIMIZATION")
    enable_engagement_optimization: bool = Field(
        default=True, 
        env="ENABLE_ENGAGEMENT_OPTIMIZATION"
    )
    enable_social_optimization: bool = Field(
        default=True, 
        env="ENABLE_SOCIAL_OPTIMIZATION"
    )
    
    # Brand settings
    brand_voice: str = Field(
        default="professional and educational", 
        env="BRAND_VOICE"
    )
    target_audience: str = Field(
        default="aquascaping enthusiasts", 
        env="TARGET_AUDIENCE"
    )
    company_name: str = Field(default="AquaScene", env="COMPANY_NAME")
    
    # File storage settings
    content_storage_directory: str = Field(
        default="data/content", 
        env="CONTENT_STORAGE_DIRECTORY"
    )
    max_file_size_mb: int = Field(default=10, env="MAX_FILE_SIZE_MB")
    
    # Cache settings
    enable_caching: bool = Field(default=True, env="ENABLE_CACHING")
    cache_ttl_seconds: int = Field(default=3600, env="CACHE_TTL_SECONDS")
    
    # Development settings
    mock_llm_responses: bool = Field(default=False, env="MOCK_LLM_RESPONSES")
    enable_debug_endpoints: bool = Field(default=False, env="ENABLE_DEBUG_ENDPOINTS")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v):
        """Validate environment setting"""
        allowed_envs = ["development", "staging", "production", "testing"]
        if v not in allowed_envs:
            raise ValueError(f"Environment must be one of: {allowed_envs}")
        return v
    
    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v):
        """Validate log level"""
        allowed_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in allowed_levels:
            raise ValueError(f"Log level must be one of: {allowed_levels}")
        return v.upper()
    
    @field_validator("default_temperature")
    @classmethod
    def validate_temperature(cls, v):
        """Validate temperature setting"""
        if not 0.0 <= v <= 2.0:
            raise ValueError("Temperature must be between 0.0 and 2.0")
        return v
    
    @field_validator("max_memory_usage_percent", "max_cpu_usage_percent")
    @classmethod
    def validate_percentage(cls, v):
        """Validate percentage values"""
        if not 0.0 <= v <= 100.0:
            raise ValueError("Percentage must be between 0.0 and 100.0")
        return v
    
    @field_validator("ollama_models", mode="before")
    @classmethod
    def parse_ollama_models(cls, v):
        """Parse comma-separated string into list"""
        if isinstance(v, str):
            return [model.strip() for model in v.split(",") if model.strip()]
        return v
    
    @field_validator("template_directories", mode="before")
    @classmethod
    def parse_template_directories(cls, v):
        """Parse comma-separated string into list"""
        if isinstance(v, str):
            return [dir.strip() for dir in v.split(",") if dir.strip()]
        return v
    
    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_allowed_origins(cls, v):
        """Parse comma-separated string into list"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v
    
    def get_llm_configs(self) -> Dict[str, Dict[str, Any]]:
        """Get LLM configuration dictionary"""
        configs = {}
        
        if self.openai_api_key:
            configs["openai"] = {
                "api_key": self.openai_api_key,
                "temperature": self.default_temperature,
                "max_tokens": self.default_max_tokens,
                "timeout_seconds": self.default_timeout_seconds
            }
        
        if self.anthropic_api_key:
            configs["anthropic"] = {
                "api_key": self.anthropic_api_key,
                "temperature": self.default_temperature,
                "max_tokens": self.default_max_tokens,
                "timeout_seconds": self.default_timeout_seconds
            }
        
        if self.ollama_base_url:
            configs["ollama"] = {
                "base_url": self.ollama_base_url,
                "temperature": self.default_temperature,
                "max_tokens": self.default_max_tokens,
                "timeout_seconds": self.default_timeout_seconds,
                "models": self.ollama_models
            }
        
        return configs
    
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.environment == "production"
    
    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.environment == "development"
    
    def get_database_config(self) -> Optional[Dict[str, Any]]:
        """Get database configuration"""
        if not self.database_url:
            return None
        
        return {
            "url": self.database_url,
            "echo": self.debug,
            "pool_size": 10,
            "max_overflow": 20
        }
    
    def get_redis_config(self) -> Optional[Dict[str, Any]]:
        """Get Redis configuration"""
        if not self.redis_url:
            return None
        
        return {
            "url": self.redis_url,
            "decode_responses": True,
            "socket_timeout": 5,
            "socket_connect_timeout": 5
        }
    
    def get_monitoring_config(self) -> Dict[str, Any]:
        """Get monitoring configuration"""
        return {
            "enable_metrics": self.enable_metrics,
            "metrics_port": self.metrics_port,
            "health_check_interval": self.health_check_interval,
            "sentry_dsn": self.sentry_dsn,
            "log_level": self.log_level,
            "structured_logging": self.structured_logging
        }
    
    def get_optimization_config(self) -> Dict[str, Any]:
        """Get content optimization configuration"""
        return {
            "enable_seo": self.enable_seo_optimization,
            "enable_engagement": self.enable_engagement_optimization,
            "enable_social": self.enable_social_optimization,
            "brand_voice": self.brand_voice,
            "target_audience": self.target_audience
        }
    
    def create_directories(self) -> None:
        """Create necessary directories if they don't exist"""
        directories = [
            self.knowledge_base_directory,
            self.content_storage_directory,
            *self.template_directories
        ]
        
        for directory in directories:
            if directory and not os.path.exists(directory):
                try:
                    os.makedirs(directory, exist_ok=True)
                except Exception as e:
                    print(f"Warning: Could not create directory {directory}: {e}")


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings"""
    settings = Settings()
    
    # Create necessary directories
    if not settings.is_production():
        settings.create_directories()
    
    return settings