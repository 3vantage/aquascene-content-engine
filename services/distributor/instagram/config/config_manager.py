"""
Configuration Management for Instagram Automation System
Handles environment variables, settings, and configuration validation.
"""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict, fields
from enum import Enum
import logging
from cryptography.fernet import Fernet


class Environment(Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


@dataclass
class InstagramAPIConfig:
    """Instagram API configuration"""
    access_token: str
    business_account_id: str
    app_id: str
    app_secret: str
    api_version: str = "v18.0"
    base_url: str = "https://graph.facebook.com"
    requests_per_hour: int = 200
    requests_per_day: int = 4800


@dataclass
class DatabaseConfig:
    """Database configuration"""
    scheduler_db_path: str = "instagram_scheduler.db"
    analytics_db_path: str = "instagram_analytics.db"
    queue_db_path: str = "content_queue.db"
    hashtag_db_path: str = "hashtag_database.db"
    error_db_path: str = "error_tracking.db"
    backup_enabled: bool = True
    backup_interval_hours: int = 24


@dataclass
class SchedulingConfig:
    """Content scheduling configuration"""
    default_posts_per_day: int = 2
    min_interval_hours: int = 4
    max_posts_per_day: int = 5
    optimal_hours: List[int] = None
    timezone: str = "Europe/Sofia"
    weekends_enabled: bool = True
    holiday_posting: bool = False
    
    def __post_init__(self):
        if self.optimal_hours is None:
            self.optimal_hours = [9, 13, 17, 19, 21]


@dataclass
class ContentConfig:
    """Content generation and validation configuration"""
    default_language: str = "bg"
    bilingual_posts: bool = True
    max_caption_length: int = 2200
    max_hashtags: int = 30
    min_hashtags: int = 10
    auto_hashtag_generation: bool = True
    content_validation_enabled: bool = True
    duplicate_check_enabled: bool = True
    brand_compliance_check: bool = True


@dataclass
class AnalyticsConfig:
    """Analytics and monitoring configuration"""
    collection_enabled: bool = True
    collection_interval_hours: int = 6
    retention_days: int = 90
    performance_alerts_enabled: bool = True
    low_engagement_threshold: float = 2.0
    high_error_rate_threshold: float = 5.0
    health_check_interval_minutes: int = 30


@dataclass
class SecurityConfig:
    """Security and encryption configuration"""
    encryption_enabled: bool = True
    token_rotation_enabled: bool = True
    token_rotation_days: int = 30
    audit_logging_enabled: bool = True
    rate_limit_buffer: float = 0.8  # Use 80% of rate limit
    request_timeout_seconds: int = 30


@dataclass
class NotificationConfig:
    """Notification configuration"""
    enabled: bool = True
    email_notifications: bool = True
    slack_webhook_url: Optional[str] = None
    discord_webhook_url: Optional[str] = None
    notification_levels: List[str] = None
    
    def __post_init__(self):
        if self.notification_levels is None:
            self.notification_levels = ["error", "warning", "success"]


@dataclass
class SystemConfig:
    """Complete system configuration"""
    environment: Environment
    instagram_api: InstagramAPIConfig
    database: DatabaseConfig
    scheduling: SchedulingConfig
    content: ContentConfig
    analytics: AnalyticsConfig
    security: SecurityConfig
    notifications: NotificationConfig
    debug_mode: bool = False
    log_level: str = "INFO"


class ConfigurationError(Exception):
    """Configuration-related errors"""
    pass


class ConfigManager:
    """
    Manages application configuration from multiple sources.
    """
    
    def __init__(self, config_dir: str = None):
        self.config_dir = Path(config_dir or "config")
        self.config_dir.mkdir(exist_ok=True)
        
        self.logger = logging.getLogger(__name__)
        self.encryption_key = self._get_or_create_encryption_key()
        self.cipher_suite = Fernet(self.encryption_key) if self.encryption_key else None
        
        self._config: Optional[SystemConfig] = None
        self._config_file_path = self.config_dir / "config.yaml"
        self._secrets_file_path = self.config_dir / "secrets.enc"
    
    def load_config(self, config_file: str = None) -> SystemConfig:
        """
        Load configuration from file and environment variables.
        Priority: Environment variables > Config file > Defaults
        """
        
        if config_file:
            config_path = Path(config_file)
        else:
            config_path = self._config_file_path
        
        # Load base configuration from file
        if config_path.exists():
            with open(config_path, 'r') as f:
                if config_path.suffix.lower() == '.yaml' or config_path.suffix.lower() == '.yml':
                    file_config = yaml.safe_load(f)
                else:
                    file_config = json.load(f)
        else:
            file_config = {}
        
        # Load secrets
        secrets = self._load_secrets()
        
        # Merge with environment variables
        env_config = self._load_from_environment()
        
        # Merge configurations (env > secrets > file > defaults)
        merged_config = self._merge_configs(file_config, secrets, env_config)
        
        # Validate and create configuration object
        self._config = self._create_config_object(merged_config)
        
        # Validate configuration
        self._validate_config(self._config)
        
        self.logger.info(f"Configuration loaded successfully for {self._config.environment.value} environment")
        return self._config
    
    def save_config(self, config: SystemConfig, save_secrets: bool = True):
        """Save configuration to file"""
        
        # Separate sensitive data
        config_dict = asdict(config)
        secrets_dict = {}
        
        if save_secrets:
            # Extract sensitive fields
            sensitive_fields = [
                'instagram_api.access_token',
                'instagram_api.app_secret',
                'notifications.slack_webhook_url',
                'notifications.discord_webhook_url'
            ]
            
            for field_path in sensitive_fields:
                keys = field_path.split('.')
                current_dict = config_dict
                secret_dict = secrets_dict
                
                # Navigate to the parent dict
                for key in keys[:-1]:
                    if key in current_dict and isinstance(current_dict[key], dict):
                        if key not in secret_dict:
                            secret_dict[key] = {}
                        current_dict = current_dict[key]
                        secret_dict = secret_dict[key]
                
                # Move sensitive value
                final_key = keys[-1]
                if final_key in current_dict:
                    secret_dict[final_key] = current_dict[final_key]
                    current_dict[final_key] = "[ENCRYPTED]"
        
        # Save main config
        with open(self._config_file_path, 'w') as f:
            yaml.dump(config_dict, f, default_flow_style=False, indent=2)
        
        # Save encrypted secrets
        if secrets_dict and save_secrets:
            self._save_secrets(secrets_dict)
        
        self.logger.info("Configuration saved successfully")
    
    def get_config(self) -> SystemConfig:
        """Get current configuration"""
        if self._config is None:
            self._config = self.load_config()
        return self._config
    
    def update_config(self, updates: Dict[str, Any], save: bool = True):
        """Update configuration with new values"""
        
        if self._config is None:
            self._config = self.load_config()
        
        # Apply updates
        config_dict = asdict(self._config)
        self._deep_update(config_dict, updates)
        
        # Recreate config object
        self._config = self._create_config_object(config_dict)
        
        # Validate
        self._validate_config(self._config)
        
        if save:
            self.save_config(self._config)
        
        self.logger.info("Configuration updated successfully")
    
    def _load_from_environment(self) -> Dict[str, Any]:
        """Load configuration from environment variables"""
        
        env_config = {}
        
        # Define environment variable mappings
        env_mappings = {
            # Instagram API
            'INSTAGRAM_ACCESS_TOKEN': 'instagram_api.access_token',
            'INSTAGRAM_BUSINESS_ACCOUNT_ID': 'instagram_api.business_account_id',
            'INSTAGRAM_APP_ID': 'instagram_api.app_id',
            'INSTAGRAM_APP_SECRET': 'instagram_api.app_secret',
            'INSTAGRAM_API_VERSION': 'instagram_api.api_version',
            
            # Environment
            'ENVIRONMENT': 'environment',
            'DEBUG_MODE': 'debug_mode',
            'LOG_LEVEL': 'log_level',
            
            # Database
            'DATABASE_BACKUP_ENABLED': 'database.backup_enabled',
            'DATABASE_BACKUP_INTERVAL': 'database.backup_interval_hours',
            
            # Scheduling
            'POSTS_PER_DAY': 'scheduling.default_posts_per_day',
            'TIMEZONE': 'scheduling.timezone',
            
            # Content
            'DEFAULT_LANGUAGE': 'content.default_language',
            'BILINGUAL_POSTS': 'content.bilingual_posts',
            
            # Analytics
            'ANALYTICS_ENABLED': 'analytics.collection_enabled',
            'ANALYTICS_RETENTION_DAYS': 'analytics.retention_days',
            
            # Security
            'ENCRYPTION_ENABLED': 'security.encryption_enabled',
            'TOKEN_ROTATION_ENABLED': 'security.token_rotation_enabled',
            
            # Notifications
            'NOTIFICATIONS_ENABLED': 'notifications.enabled',
            'SLACK_WEBHOOK_URL': 'notifications.slack_webhook_url',
            'DISCORD_WEBHOOK_URL': 'notifications.discord_webhook_url',
        }
        
        for env_var, config_path in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                # Convert value to appropriate type
                value = self._convert_env_value(value)
                
                # Set nested value
                keys = config_path.split('.')
                current_dict = env_config
                
                for key in keys[:-1]:
                    if key not in current_dict:
                        current_dict[key] = {}
                    current_dict = current_dict[key]
                
                current_dict[keys[-1]] = value
        
        return env_config
    
    def _convert_env_value(self, value: str) -> Any:
        """Convert environment variable string to appropriate type"""
        
        # Boolean conversion
        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'
        
        # Integer conversion
        try:
            return int(value)
        except ValueError:
            pass
        
        # Float conversion
        try:
            return float(value)
        except ValueError:
            pass
        
        # List conversion (comma-separated)
        if ',' in value:
            return [item.strip() for item in value.split(',')]
        
        # Return as string
        return value
    
    def _load_secrets(self) -> Dict[str, Any]:
        """Load encrypted secrets from file"""
        
        if not self._secrets_file_path.exists() or not self.cipher_suite:
            return {}
        
        try:
            with open(self._secrets_file_path, 'rb') as f:
                encrypted_data = f.read()
            
            decrypted_data = self.cipher_suite.decrypt(encrypted_data)
            return json.loads(decrypted_data.decode())
            
        except Exception as e:
            self.logger.warning(f"Failed to load secrets: {e}")
            return {}
    
    def _save_secrets(self, secrets: Dict[str, Any]):
        """Save encrypted secrets to file"""
        
        if not self.cipher_suite:
            self.logger.warning("Encryption not available, secrets not saved")
            return
        
        try:
            json_data = json.dumps(secrets).encode()
            encrypted_data = self.cipher_suite.encrypt(json_data)
            
            with open(self._secrets_file_path, 'wb') as f:
                f.write(encrypted_data)
            
        except Exception as e:
            self.logger.error(f"Failed to save secrets: {e}")
    
    def _get_or_create_encryption_key(self) -> Optional[bytes]:
        """Get or create encryption key"""
        
        key_file = self.config_dir / ".encryption_key"
        
        if key_file.exists():
            try:
                with open(key_file, 'rb') as f:
                    return f.read()
            except Exception as e:
                self.logger.warning(f"Failed to load encryption key: {e}")
        
        # Create new key
        try:
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            
            # Secure the key file
            os.chmod(key_file, 0o600)
            return key
            
        except Exception as e:
            self.logger.error(f"Failed to create encryption key: {e}")
            return None
    
    def _merge_configs(self, *configs: Dict[str, Any]) -> Dict[str, Any]:
        """Merge multiple configuration dictionaries"""
        
        result = {}
        for config in configs:
            if config:
                self._deep_update(result, config)
        return result
    
    def _deep_update(self, base_dict: Dict[str, Any], update_dict: Dict[str, Any]):
        """Deep update dictionary"""
        
        for key, value in update_dict.items():
            if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                self._deep_update(base_dict[key], value)
            else:
                base_dict[key] = value
    
    def _create_config_object(self, config_dict: Dict[str, Any]) -> SystemConfig:
        """Create SystemConfig object from dictionary"""
        
        # Set defaults
        defaults = {
            'environment': Environment.DEVELOPMENT,
            'debug_mode': False,
            'log_level': 'INFO'
        }
        
        # Apply defaults
        for key, default_value in defaults.items():
            if key not in config_dict:
                config_dict[key] = default_value
        
        # Convert environment string to enum
        if isinstance(config_dict.get('environment'), str):
            config_dict['environment'] = Environment(config_dict['environment'])
        
        # Create sub-config objects
        instagram_api = InstagramAPIConfig(**config_dict.get('instagram_api', {}))
        database = DatabaseConfig(**config_dict.get('database', {}))
        scheduling = SchedulingConfig(**config_dict.get('scheduling', {}))
        content = ContentConfig(**config_dict.get('content', {}))
        analytics = AnalyticsConfig(**config_dict.get('analytics', {}))
        security = SecurityConfig(**config_dict.get('security', {}))
        notifications = NotificationConfig(**config_dict.get('notifications', {}))
        
        return SystemConfig(
            environment=config_dict['environment'],
            instagram_api=instagram_api,
            database=database,
            scheduling=scheduling,
            content=content,
            analytics=analytics,
            security=security,
            notifications=notifications,
            debug_mode=config_dict['debug_mode'],
            log_level=config_dict['log_level']
        )
    
    def _validate_config(self, config: SystemConfig):
        """Validate configuration"""
        
        errors = []
        
        # Validate Instagram API config
        if not config.instagram_api.access_token:
            errors.append("Instagram access token is required")
        
        if not config.instagram_api.business_account_id:
            errors.append("Instagram business account ID is required")
        
        # Validate scheduling config
        if config.scheduling.default_posts_per_day < 1:
            errors.append("Posts per day must be at least 1")
        
        if config.scheduling.min_interval_hours < 1:
            errors.append("Minimum interval must be at least 1 hour")
        
        # Validate content config
        if config.content.max_caption_length > 2200:
            errors.append("Maximum caption length cannot exceed 2200 characters")
        
        if config.content.max_hashtags > 30:
            errors.append("Maximum hashtags cannot exceed 30")
        
        # Validate analytics config
        if config.analytics.retention_days < 1:
            errors.append("Retention days must be at least 1")
        
        if errors:
            raise ConfigurationError(f"Configuration validation failed: {'; '.join(errors)}")
    
    def create_sample_config(self) -> SystemConfig:
        """Create a sample configuration file"""
        
        sample_config = SystemConfig(
            environment=Environment.DEVELOPMENT,
            instagram_api=InstagramAPIConfig(
                access_token="YOUR_ACCESS_TOKEN",
                business_account_id="YOUR_BUSINESS_ACCOUNT_ID",
                app_id="YOUR_APP_ID",
                app_secret="YOUR_APP_SECRET"
            ),
            database=DatabaseConfig(),
            scheduling=SchedulingConfig(),
            content=ContentConfig(),
            analytics=AnalyticsConfig(),
            security=SecurityConfig(),
            notifications=NotificationConfig(),
            debug_mode=True,
            log_level="DEBUG"
        )
        
        return sample_config


# Usage example
if __name__ == "__main__":
    
    # Initialize config manager
    config_manager = ConfigManager()
    
    # Create sample configuration
    sample_config = config_manager.create_sample_config()
    config_manager.save_config(sample_config)
    print("Sample configuration created")
    
    # Load configuration
    try:
        config = config_manager.load_config()
        print(f"Configuration loaded for {config.environment.value} environment")
        print(f"Posts per day: {config.scheduling.default_posts_per_day}")
        print(f"Default language: {config.content.default_language}")
        
    except ConfigurationError as e:
        print(f"Configuration error: {e}")
    
    # Update configuration
    updates = {
        'scheduling': {
            'default_posts_per_day': 3
        },
        'content': {
            'default_language': 'en'
        }
    }
    
    try:
        config_manager.update_config(updates)
        print("Configuration updated successfully")
    except Exception as e:
        print(f"Update failed: {e}")