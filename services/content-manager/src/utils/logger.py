"""
Logging utilities for Content Manager
"""
import logging
import sys
from datetime import datetime
from typing import Dict, Any
import structlog

from ..config.settings import get_settings


def setup_logger() -> structlog.BoundLogger:
    """Setup structured logger for Content Manager"""
    settings = get_settings()
    
    # Configure standard logging
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
        ]
    )
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            add_service_info,
            add_environment_info,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    return structlog.get_logger("content-manager")


def add_service_info(logger, method_name: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add service information to log entries"""
    event_dict["service"] = "content-manager"
    event_dict["version"] = "1.0.0"
    return event_dict


def add_environment_info(logger, method_name: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add environment information to log entries"""
    settings = get_settings()
    event_dict["environment"] = settings.environment
    return event_dict


class ContentManagerLogger:
    """Enhanced logger for Content Manager with context tracking"""
    
    def __init__(self):
        self.logger = setup_logger()
        self.request_context = {}
    
    def set_request_context(self, **context):
        """Set context for the current request"""
        self.request_context.update(context)
    
    def clear_request_context(self):
        """Clear request context"""
        self.request_context.clear()
    
    def log_operation_start(self, operation: str, **context):
        """Log the start of an operation"""
        self.logger.info(
            f"Starting {operation}",
            operation=operation,
            status="started",
            **self.request_context,
            **context
        )
    
    def log_operation_success(self, operation: str, duration_ms: float = None, **context):
        """Log successful operation completion"""
        log_data = {
            "operation": operation,
            "status": "completed",
            **self.request_context,
            **context
        }
        
        if duration_ms is not None:
            log_data["duration_ms"] = duration_ms
        
        self.logger.info(f"Completed {operation}", **log_data)
    
    def log_operation_error(self, operation: str, error: Exception, **context):
        """Log operation error"""
        self.logger.error(
            f"Failed {operation}",
            operation=operation,
            status="failed",
            error_type=type(error).__name__,
            error_message=str(error),
            **self.request_context,
            **context
        )
    
    def log_content_lifecycle_event(self, event_type: str, content_id: str, **context):
        """Log content lifecycle events"""
        self.logger.info(
            f"Content lifecycle event: {event_type}",
            event_type="content_lifecycle",
            lifecycle_event=event_type,
            content_id=content_id,
            **self.request_context,
            **context
        )
    
    def log_workflow_event(self, workflow_name: str, step: str, status: str, **context):
        """Log workflow execution events"""
        self.logger.info(
            f"Workflow {workflow_name} - {step}: {status}",
            event_type="workflow",
            workflow_name=workflow_name,
            workflow_step=step,
            workflow_status=status,
            **self.request_context,
            **context
        )
    
    def log_database_operation(self, operation: str, table: str, record_id: str = None, **context):
        """Log database operations"""
        log_data = {
            "event_type": "database",
            "db_operation": operation,
            "table": table,
            **self.request_context,
            **context
        }
        
        if record_id:
            log_data["record_id"] = record_id
        
        self.logger.debug(f"Database {operation} on {table}", **log_data)
    
    def log_api_request(self, method: str, endpoint: str, user_id: str = None, **context):
        """Log API requests"""
        log_data = {
            "event_type": "api_request",
            "http_method": method,
            "endpoint": endpoint,
            "timestamp": datetime.utcnow().isoformat(),
            **context
        }
        
        if user_id:
            log_data["user_id"] = user_id
            
        self.logger.info(f"API {method} {endpoint}", **log_data)
    
    def log_api_response(self, method: str, endpoint: str, status_code: int, duration_ms: float, **context):
        """Log API responses"""
        self.logger.info(
            f"API {method} {endpoint} - {status_code}",
            event_type="api_response",
            http_method=method,
            endpoint=endpoint,
            status_code=status_code,
            duration_ms=duration_ms,
            **context
        )
    
    def log_performance_metric(self, metric_name: str, metric_value: float, unit: str = None, **context):
        """Log performance metrics"""
        log_data = {
            "event_type": "performance_metric",
            "metric_name": metric_name,
            "metric_value": metric_value,
            "timestamp": datetime.utcnow().isoformat(),
            **context
        }
        
        if unit:
            log_data["unit"] = unit
            
        self.logger.info(f"Metric {metric_name}: {metric_value}", **log_data)
    
    def log_business_event(self, event_name: str, **context):
        """Log business logic events"""
        self.logger.info(
            f"Business event: {event_name}",
            event_type="business_event",
            event_name=event_name,
            **self.request_context,
            **context
        )


# Global logger instance
cm_logger = ContentManagerLogger()