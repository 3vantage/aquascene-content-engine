"""
Error handling utilities for Content Manager
"""
import logging
import traceback
from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium" 
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for better classification"""
    DATABASE = "database"
    VALIDATION = "validation"
    EXTERNAL_API = "external_api"
    WORKFLOW = "workflow"
    AUTHENTICATION = "authentication"
    CONFIGURATION = "configuration"
    BUSINESS_LOGIC = "business_logic"


class ContentManagerException(Exception):
    """Base exception class for Content Manager"""
    
    def __init__(
        self, 
        message: str, 
        category: ErrorCategory = ErrorCategory.BUSINESS_LOGIC,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.category = category
        self.severity = severity
        self.details = details or {}
        self.timestamp = datetime.utcnow()
        super().__init__(self.message)


class DatabaseException(ContentManagerException):
    """Database-related exceptions"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message, 
            category=ErrorCategory.DATABASE, 
            severity=ErrorSeverity.HIGH,
            details=details
        )


class ValidationException(ContentManagerException):
    """Data validation exceptions"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message,
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.MEDIUM,
            details=details
        )


class WorkflowException(ContentManagerException):
    """Workflow execution exceptions"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message,
            category=ErrorCategory.WORKFLOW,
            severity=ErrorSeverity.HIGH,
            details=details
        )


class ExternalAPIException(ContentManagerException):
    """External API communication exceptions"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message,
            category=ErrorCategory.EXTERNAL_API,
            severity=ErrorSeverity.MEDIUM,
            details=details
        )


class ErrorHandler:
    """Centralized error handling and logging"""
    
    def __init__(self):
        self.error_counts = {}
        self.recent_errors = []
        
    def handle_exception(
        self,
        exception: Exception,
        context: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Handle exceptions with proper logging and response formatting
        
        Args:
            exception: The exception to handle
            context: Additional context about where the error occurred
            user_id: ID of user who triggered the error
            
        Returns:
            Dictionary with error details for API response
        """
        context = context or {}
        
        # Extract error information
        error_info = self._extract_error_info(exception)
        error_info.update(context)
        
        if user_id:
            error_info['user_id'] = user_id
            
        # Log the error
        self._log_error(error_info)
        
        # Track error statistics
        self._track_error(error_info)
        
        # Return sanitized error for API response
        return self._format_error_response(error_info)
    
    def _extract_error_info(self, exception: Exception) -> Dict[str, Any]:
        """Extract relevant information from exception"""
        error_info = {
            'error_type': type(exception).__name__,
            'message': str(exception),
            'timestamp': datetime.utcnow().isoformat(),
            'traceback': traceback.format_exc()
        }
        
        # Add additional info for ContentManagerException
        if isinstance(exception, ContentManagerException):
            error_info.update({
                'category': exception.category.value,
                'severity': exception.severity.value,
                'details': exception.details
            })
        
        return error_info
    
    def _log_error(self, error_info: Dict[str, Any]):
        """Log error with appropriate level based on severity"""
        severity = error_info.get('severity', ErrorSeverity.MEDIUM.value)
        message = f"Content Manager Error: {error_info.get('message')}"
        
        # Include context in log message
        context_parts = []
        if error_info.get('user_id'):
            context_parts.append(f"User: {error_info['user_id']}")
        if error_info.get('endpoint'):
            context_parts.append(f"Endpoint: {error_info['endpoint']}")
        if error_info.get('operation'):
            context_parts.append(f"Operation: {error_info['operation']}")
            
        if context_parts:
            message += f" | Context: {', '.join(context_parts)}"
        
        # Log with appropriate level
        if severity == ErrorSeverity.CRITICAL.value:
            logger.critical(message, extra=error_info)
        elif severity == ErrorSeverity.HIGH.value:
            logger.error(message, extra=error_info)
        elif severity == ErrorSeverity.MEDIUM.value:
            logger.warning(message, extra=error_info)
        else:
            logger.info(message, extra=error_info)
    
    def _track_error(self, error_info: Dict[str, Any]):
        """Track error statistics"""
        error_type = error_info.get('error_type', 'Unknown')
        category = error_info.get('category', 'unknown')
        
        # Increment error counts
        key = f"{category}:{error_type}"
        self.error_counts[key] = self.error_counts.get(key, 0) + 1
        
        # Keep recent errors (limit to last 100)
        self.recent_errors.append(error_info)
        if len(self.recent_errors) > 100:
            self.recent_errors.pop(0)
    
    def _format_error_response(self, error_info: Dict[str, Any]) -> Dict[str, Any]:
        """Format error for API response (sanitized)"""
        response = {
            'error': True,
            'error_type': error_info.get('error_type', 'Unknown'),
            'message': error_info.get('message', 'An error occurred'),
            'timestamp': error_info.get('timestamp')
        }
        
        # Include category and severity if available
        if 'category' in error_info:
            response['category'] = error_info['category']
        if 'severity' in error_info:
            response['severity'] = error_info['severity']
        
        # Include safe details (no sensitive information)
        details = error_info.get('details', {})
        safe_details = {}
        
        # Only include non-sensitive details
        safe_keys = ['validation_errors', 'field_errors', 'operation', 'step']
        for key in safe_keys:
            if key in details:
                safe_details[key] = details[key]
        
        if safe_details:
            response['details'] = safe_details
        
        return response
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics"""
        return {
            'error_counts': dict(self.error_counts),
            'recent_errors_count': len(self.recent_errors),
            'most_common_errors': self._get_most_common_errors()
        }
    
    def _get_most_common_errors(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most common error types"""
        sorted_errors = sorted(
            self.error_counts.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        
        return [
            {'error': error, 'count': count}
            for error, count in sorted_errors[:limit]
        ]
    
    def clear_error_history(self):
        """Clear error tracking history"""
        self.error_counts.clear()
        self.recent_errors.clear()
        logger.info("Error history cleared")


# Global error handler instance
error_handler = ErrorHandler()


def handle_database_error(func):
    """Decorator for handling database errors"""
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            context = {
                'operation': func.__name__,
                'function': f"{func.__module__}.{func.__qualname__}"
            }
            
            if hasattr(e, '__cause__') and e.__cause__:
                # Database-specific error handling
                db_error = DatabaseException(
                    f"Database operation failed in {func.__name__}: {str(e)}",
                    details={'original_error': str(e)}
                )
                raise db_error
            else:
                raise e
    
    return wrapper


def handle_validation_error(func):
    """Decorator for handling validation errors"""
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except (ValueError, TypeError) as e:
            validation_error = ValidationException(
                f"Validation failed in {func.__name__}: {str(e)}",
                details={'function': func.__name__, 'original_error': str(e)}
            )
            raise validation_error
        except Exception as e:
            raise e
    
    return wrapper