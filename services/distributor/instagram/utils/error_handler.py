"""
Comprehensive Error Handling and Retry Logic for Instagram Automation
Handles API errors, network issues, rate limiting, and provides robust retry mechanisms.
"""

import time
import logging
import asyncio
import functools
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import json
import sqlite3
from concurrent.futures import ThreadPoolExecutor
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class ErrorType(Enum):
    API_ERROR = "api_error"
    RATE_LIMIT = "rate_limit"
    NETWORK_ERROR = "network_error"
    AUTHENTICATION_ERROR = "authentication_error"
    VALIDATION_ERROR = "validation_error"
    MEDIA_ERROR = "media_error"
    QUOTA_EXCEEDED = "quota_exceeded"
    TEMPORARY_ERROR = "temporary_error"
    PERMANENT_ERROR = "permanent_error"
    UNKNOWN_ERROR = "unknown_error"


class ErrorSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ErrorRecord:
    """Record of an error occurrence"""
    id: str
    error_type: ErrorType
    severity: ErrorSeverity
    message: str
    context: Dict[str, Any]
    timestamp: datetime
    retry_count: int = 0
    resolved: bool = False
    resolution_notes: str = ""


@dataclass
class RetryConfig:
    """Configuration for retry behavior"""
    max_attempts: int = 3
    initial_delay: float = 1.0
    max_delay: float = 300.0
    exponential_base: float = 2.0
    jitter: bool = True
    retryable_errors: List[ErrorType] = None
    
    def __post_init__(self):
        if self.retryable_errors is None:
            self.retryable_errors = [
                ErrorType.NETWORK_ERROR,
                ErrorType.RATE_LIMIT,
                ErrorType.TEMPORARY_ERROR,
                ErrorType.API_ERROR
            ]


class InstagramAPIException(Exception):
    """Custom exception for Instagram API errors"""
    
    def __init__(self, message: str, error_type: ErrorType, 
                 error_code: str = None, retry_after: int = None):
        super().__init__(message)
        self.error_type = error_type
        self.error_code = error_code
        self.retry_after = retry_after


class ErrorTracker:
    """Tracks and analyzes error patterns"""
    
    def __init__(self, db_path: str = "error_tracking.db"):
        self.db_path = db_path
        self.init_database()
        self.logger = logging.getLogger(__name__)
    
    def init_database(self):
        """Initialize error tracking database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS error_records (
                id TEXT PRIMARY KEY,
                error_type TEXT,
                severity TEXT,
                message TEXT,
                context TEXT,
                timestamp TEXT,
                retry_count INTEGER DEFAULT 0,
                resolved BOOLEAN DEFAULT FALSE,
                resolution_notes TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS error_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_name TEXT,
                error_type TEXT,
                frequency INTEGER,
                last_occurrence TEXT,
                suggested_action TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS retry_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                error_id TEXT,
                attempt_number INTEGER,
                timestamp TEXT,
                success BOOLEAN,
                delay_seconds REAL,
                error_message TEXT
            )
        """)
        
        conn.commit()
        conn.close()
    
    def record_error(self, error_record: ErrorRecord):
        """Record an error occurrence"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO error_records
            (id, error_type, severity, message, context, timestamp, retry_count, resolved, resolution_notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            error_record.id,
            error_record.error_type.value,
            error_record.severity.value,
            error_record.message,
            json.dumps(error_record.context),
            error_record.timestamp.isoformat(),
            error_record.retry_count,
            error_record.resolved,
            error_record.resolution_notes
        ))
        
        conn.commit()
        conn.close()
        
        self.logger.error(f"Error recorded: {error_record.error_type.value} - {error_record.message}")
    
    def record_retry_attempt(self, error_id: str, attempt_number: int, 
                           success: bool, delay_seconds: float, 
                           error_message: str = None):
        """Record a retry attempt"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO retry_attempts
            (error_id, attempt_number, timestamp, success, delay_seconds, error_message)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            error_id,
            attempt_number,
            datetime.now().isoformat(),
            success,
            delay_seconds,
            error_message
        ))
        
        conn.commit()
        conn.close()
    
    def get_error_statistics(self, hours_back: int = 24) -> Dict:
        """Get error statistics for analysis"""
        conn = sqlite3.connect(self.db_path)
        
        query = """
            SELECT error_type, severity, COUNT(*) as count
            FROM error_records 
            WHERE timestamp >= datetime('now', '-{} hours')
            GROUP BY error_type, severity
        """.format(hours_back)
        
        cursor = conn.cursor()
        cursor.execute(query)
        results = cursor.fetchall()
        
        stats = {
            'total_errors': 0,
            'by_type': {},
            'by_severity': {},
            'error_rate': 0.0
        }
        
        for error_type, severity, count in results:
            stats['total_errors'] += count
            stats['by_type'][error_type] = stats['by_type'].get(error_type, 0) + count
            stats['by_severity'][severity] = stats['by_severity'].get(severity, 0) + count
        
        # Calculate error rate (errors per hour)
        stats['error_rate'] = stats['total_errors'] / hours_back if hours_back > 0 else 0
        
        conn.close()
        return stats


class RetryHandler:
    """Handles retry logic with exponential backoff"""
    
    def __init__(self, config: RetryConfig = None):
        self.config = config or RetryConfig()
        self.error_tracker = ErrorTracker()
        self.logger = logging.getLogger(__name__)
    
    def retry_with_backoff(self, error_id: str = None):
        """Decorator for retry with exponential backoff"""
        
        def decorator(func: Callable) -> Callable:
            
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                last_exception = None
                
                for attempt in range(self.config.max_attempts):
                    try:
                        result = func(*args, **kwargs)
                        
                        # Record successful retry if this wasn't the first attempt
                        if attempt > 0 and error_id:
                            self.error_tracker.record_retry_attempt(
                                error_id, attempt + 1, True, 0
                            )
                        
                        return result
                        
                    except Exception as e:
                        last_exception = e
                        error_type = self._classify_error(e)
                        
                        # Check if this error type is retryable
                        if error_type not in self.config.retryable_errors:
                            self.logger.error(f"Non-retryable error: {error_type.value}")
                            raise e
                        
                        # Calculate delay for next attempt
                        if attempt < self.config.max_attempts - 1:
                            delay = self._calculate_delay(attempt, e)
                            
                            self.logger.warning(
                                f"Attempt {attempt + 1} failed: {str(e)}. "
                                f"Retrying in {delay:.2f} seconds..."
                            )
                            
                            # Record retry attempt
                            if error_id:
                                self.error_tracker.record_retry_attempt(
                                    error_id, attempt + 1, False, delay, str(e)
                                )
                            
                            time.sleep(delay)
                        else:
                            self.logger.error(f"All {self.config.max_attempts} attempts failed")
                
                # All attempts failed
                raise last_exception
            
            return wrapper
        return decorator
    
    async def async_retry_with_backoff(self, func: Callable, *args, **kwargs) -> Any:
        """Async version of retry with backoff"""
        
        last_exception = None
        
        for attempt in range(self.config.max_attempts):
            try:
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                
                return result
                
            except Exception as e:
                last_exception = e
                error_type = self._classify_error(e)
                
                if error_type not in self.config.retryable_errors:
                    raise e
                
                if attempt < self.config.max_attempts - 1:
                    delay = self._calculate_delay(attempt, e)
                    self.logger.warning(
                        f"Async attempt {attempt + 1} failed: {str(e)}. "
                        f"Retrying in {delay:.2f} seconds..."
                    )
                    await asyncio.sleep(delay)
        
        raise last_exception
    
    def _calculate_delay(self, attempt: int, exception: Exception) -> float:
        """Calculate delay with exponential backoff and jitter"""
        
        # Handle rate limit errors specially
        if isinstance(exception, InstagramAPIException) and exception.retry_after:
            return min(exception.retry_after, self.config.max_delay)
        
        # Exponential backoff
        delay = self.config.initial_delay * (self.config.exponential_base ** attempt)
        delay = min(delay, self.config.max_delay)
        
        # Add jitter to prevent thundering herd
        if self.config.jitter:
            import random
            delay = delay * (0.5 + random.random() * 0.5)
        
        return delay
    
    def _classify_error(self, exception: Exception) -> ErrorType:
        """Classify exception into error type"""
        
        if isinstance(exception, InstagramAPIException):
            return exception.error_type
        
        # Network-related errors
        if isinstance(exception, (
            requests.exceptions.ConnectionError,
            requests.exceptions.Timeout,
            requests.exceptions.ReadTimeout
        )):
            return ErrorType.NETWORK_ERROR
        
        # HTTP status code based classification
        if isinstance(exception, requests.exceptions.HTTPError):
            status_code = exception.response.status_code if exception.response else 0
            
            if status_code == 429:
                return ErrorType.RATE_LIMIT
            elif status_code == 401:
                return ErrorType.AUTHENTICATION_ERROR
            elif 500 <= status_code < 600:
                return ErrorType.TEMPORARY_ERROR
            elif 400 <= status_code < 500:
                return ErrorType.VALIDATION_ERROR
        
        return ErrorType.UNKNOWN_ERROR


class CircuitBreaker:
    """Circuit breaker pattern implementation"""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half-open
        self.logger = logging.getLogger(__name__)
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        
        if self.state == "open":
            if self._should_attempt_reset():
                self.state = "half-open"
                self.logger.info("Circuit breaker attempting reset")
            else:
                raise Exception("Circuit breaker is OPEN - calls are blocked")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
            
        except Exception as e:
            self._on_failure()
            raise e
    
    def _should_attempt_reset(self) -> bool:
        """Check if circuit breaker should attempt to reset"""
        if self.last_failure_time is None:
            return True
        
        return (datetime.now() - self.last_failure_time).seconds >= self.recovery_timeout
    
    def _on_success(self):
        """Handle successful call"""
        self.failure_count = 0
        if self.state == "half-open":
            self.state = "closed"
            self.logger.info("Circuit breaker reset to CLOSED")
    
    def _on_failure(self):
        """Handle failed call"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "open"
            self.logger.warning(f"Circuit breaker opened after {self.failure_count} failures")


class ErrorRecoveryManager:
    """Manages error recovery strategies"""
    
    def __init__(self):
        self.error_tracker = ErrorTracker()
        self.retry_handler = RetryHandler()
        self.circuit_breaker = CircuitBreaker()
        self.logger = logging.getLogger(__name__)
        
        # Recovery strategies for different error types
        self.recovery_strategies = {
            ErrorType.RATE_LIMIT: self._handle_rate_limit,
            ErrorType.AUTHENTICATION_ERROR: self._handle_auth_error,
            ErrorType.MEDIA_ERROR: self._handle_media_error,
            ErrorType.NETWORK_ERROR: self._handle_network_error,
            ErrorType.QUOTA_EXCEEDED: self._handle_quota_exceeded
        }
    
    def handle_error(self, exception: Exception, context: Dict[str, Any]) -> Optional[str]:
        """
        Handle error with appropriate recovery strategy.
        Returns recovery action taken or None.
        """
        
        error_type = self.retry_handler._classify_error(exception)
        severity = self._determine_severity(error_type, exception)
        
        # Create error record
        error_record = ErrorRecord(
            id=f"error_{datetime.now().timestamp()}",
            error_type=error_type,
            severity=severity,
            message=str(exception),
            context=context,
            timestamp=datetime.now()
        )
        
        self.error_tracker.record_error(error_record)
        
        # Apply recovery strategy
        recovery_strategy = self.recovery_strategies.get(error_type)
        if recovery_strategy:
            try:
                recovery_action = recovery_strategy(exception, context)
                self.logger.info(f"Applied recovery strategy: {recovery_action}")
                return recovery_action
            except Exception as recovery_error:
                self.logger.error(f"Recovery strategy failed: {recovery_error}")
        
        return None
    
    def _determine_severity(self, error_type: ErrorType, exception: Exception) -> ErrorSeverity:
        """Determine error severity"""
        
        severity_mapping = {
            ErrorType.AUTHENTICATION_ERROR: ErrorSeverity.CRITICAL,
            ErrorType.QUOTA_EXCEEDED: ErrorSeverity.HIGH,
            ErrorType.PERMANENT_ERROR: ErrorSeverity.HIGH,
            ErrorType.RATE_LIMIT: ErrorSeverity.MEDIUM,
            ErrorType.MEDIA_ERROR: ErrorSeverity.MEDIUM,
            ErrorType.NETWORK_ERROR: ErrorSeverity.LOW,
            ErrorType.TEMPORARY_ERROR: ErrorSeverity.LOW
        }
        
        return severity_mapping.get(error_type, ErrorSeverity.MEDIUM)
    
    def _handle_rate_limit(self, exception: Exception, context: Dict) -> str:
        """Handle rate limit errors"""
        
        # Extract retry-after header if available
        retry_after = getattr(exception, 'retry_after', None)
        if not retry_after:
            retry_after = 3600  # Default 1 hour
        
        self.logger.warning(f"Rate limit hit. Waiting {retry_after} seconds")
        
        # Could implement queue pausing here
        return f"Applied rate limit backoff: {retry_after} seconds"
    
    def _handle_auth_error(self, exception: Exception, context: Dict) -> str:
        """Handle authentication errors"""
        
        self.logger.critical("Authentication error detected - token may be expired")
        
        # Could trigger token refresh here
        return "Flagged for token refresh"
    
    def _handle_media_error(self, exception: Exception, context: Dict) -> str:
        """Handle media-related errors"""
        
        self.logger.warning("Media error - checking media URLs")
        
        # Could implement media validation/re-upload here
        return "Media validation triggered"
    
    def _handle_network_error(self, exception: Exception, context: Dict) -> str:
        """Handle network errors"""
        
        self.logger.warning("Network error - checking connectivity")
        
        # Could implement network diagnostics here
        return "Network diagnostics initiated"
    
    def _handle_quota_exceeded(self, exception: Exception, context: Dict) -> str:
        """Handle quota exceeded errors"""
        
        self.logger.error("API quota exceeded - pausing operations")
        
        # Could implement quota management here
        return "Operations paused due to quota limits"


class HealthChecker:
    """System health monitoring and diagnostics"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.error_tracker = ErrorTracker()
    
    def check_system_health(self) -> Dict[str, Any]:
        """Perform comprehensive system health check"""
        
        health_report = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': 'healthy',
            'components': {},
            'recommendations': []
        }
        
        # Check error rates
        error_stats = self.error_tracker.get_error_statistics(24)
        health_report['components']['error_rate'] = {
            'status': 'healthy' if error_stats['error_rate'] < 1.0 else 'degraded',
            'error_rate_per_hour': error_stats['error_rate'],
            'total_errors_24h': error_stats['total_errors']
        }
        
        # Check API connectivity
        api_health = self._check_api_connectivity()
        health_report['components']['api_connectivity'] = api_health
        
        # Check database connectivity
        db_health = self._check_database_connectivity()
        health_report['components']['database'] = db_health
        
        # Determine overall status
        component_statuses = [comp['status'] for comp in health_report['components'].values()]
        if 'critical' in component_statuses:
            health_report['overall_status'] = 'critical'
        elif 'degraded' in component_statuses:
            health_report['overall_status'] = 'degraded'
        
        # Generate recommendations
        health_report['recommendations'] = self._generate_health_recommendations(health_report)
        
        return health_report
    
    def _check_api_connectivity(self) -> Dict[str, Any]:
        """Check Instagram API connectivity"""
        
        try:
            # Simple connectivity test
            response = requests.get("https://graph.facebook.com/", timeout=10)
            
            return {
                'status': 'healthy' if response.status_code == 200 else 'degraded',
                'response_time_ms': response.elapsed.total_seconds() * 1000,
                'last_check': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'critical',
                'error': str(e),
                'last_check': datetime.now().isoformat()
            }
    
    def _check_database_connectivity(self) -> Dict[str, Any]:
        """Check database connectivity"""
        
        try:
            conn = sqlite3.connect(self.error_tracker.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            conn.close()
            
            return {
                'status': 'healthy',
                'last_check': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'critical',
                'error': str(e),
                'last_check': datetime.now().isoformat()
            }
    
    def _generate_health_recommendations(self, health_report: Dict) -> List[str]:
        """Generate health recommendations based on system status"""
        
        recommendations = []
        
        # Error rate recommendations
        error_rate = health_report['components']['error_rate']['error_rate_per_hour']
        if error_rate > 2.0:
            recommendations.append("High error rate detected. Review error logs and consider reducing request frequency.")
        
        # API connectivity recommendations
        api_status = health_report['components']['api_connectivity']['status']
        if api_status != 'healthy':
            recommendations.append("API connectivity issues detected. Check network connection and API credentials.")
        
        # Database recommendations
        db_status = health_report['components']['database']['status']
        if db_status != 'healthy':
            recommendations.append("Database connectivity issues detected. Check database configuration and disk space.")
        
        return recommendations


# Usage example and testing
if __name__ == "__main__":
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Initialize error handling components
    error_manager = ErrorRecoveryManager()
    health_checker = HealthChecker()
    retry_handler = RetryHandler()
    
    # Example: Function that might fail
    @retry_handler.retry_with_backoff()
    def example_api_call():
        import random
        if random.random() < 0.7:  # 70% chance of failure
            raise requests.exceptions.ConnectionError("Simulated network error")
        return "Success!"
    
    # Test retry mechanism
    try:
        result = example_api_call()
        print(f"Result: {result}")
    except Exception as e:
        print(f"Final failure: {e}")
    
    # Check system health
    health_report = health_checker.check_system_health()
    print(f"System health: {health_report['overall_status']}")
    
    # Get error statistics
    error_stats = ErrorTracker().get_error_statistics(24)
    print(f"Error statistics: {error_stats}")