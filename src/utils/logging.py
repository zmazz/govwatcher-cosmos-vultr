"""
Logging configuration for the Cosmos Gov-Watcher system.
Sets up structured logging with JSON output for CloudWatch.
"""

import os
import sys
import time
import json
from typing import Dict, Any, Optional
import structlog
from structlog.stdlib import LoggerFactory
from structlog.dev import ConsoleRenderer
from structlog.processors import JSONRenderer, TimeStamper, add_log_level


def setup_logging(
    level: str = None,
    json_output: bool = None,
    service_name: str = "govwatcher"
) -> None:
    """
    Set up structured logging configuration.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR)
        json_output: Whether to output JSON format (default: True in production)
        service_name: Service name to include in logs
    """
    # Set defaults based on environment
    if level is None:
        level = os.getenv('LOG_LEVEL', 'INFO').upper()
    
    if json_output is None:
        # Use JSON output in production/Lambda, human-readable in development
        json_output = os.getenv('AWS_LAMBDA_FUNCTION_NAME') is not None
    
    # Configure processors
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        add_log_level,
        TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        add_service_context(service_name),
        add_lambda_context(),
    ]
    
    if json_output:
        processors.append(JSONRenderer())
    else:
        processors.append(ConsoleRenderer(colors=True))
    
    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Set logging level
    import logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, level, logging.INFO),
    )


def add_service_context(service_name: str):
    """Add service context to all log entries."""
    def processor(logger, method_name, event_dict):
        event_dict["service"] = service_name
        event_dict["version"] = os.getenv("SERVICE_VERSION", "unknown")
        return event_dict
    return processor


def add_lambda_context():
    """Add Lambda context information to log entries."""
    def processor(logger, method_name, event_dict):
        # Add Lambda-specific context if available
        function_name = os.getenv('AWS_LAMBDA_FUNCTION_NAME')
        if function_name:
            event_dict["lambda_function"] = function_name
            event_dict["lambda_version"] = os.getenv('AWS_LAMBDA_FUNCTION_VERSION', '$LATEST')
            event_dict["lambda_memory"] = os.getenv('AWS_LAMBDA_FUNCTION_MEMORY_SIZE')
            
        # Add request ID if available from Lambda context
        request_id = getattr(add_lambda_context, '_request_id', None)
        if request_id:
            event_dict["request_id"] = request_id
            
        return event_dict
    return processor


def set_lambda_request_id(request_id: str):
    """Set the current Lambda request ID for logging."""
    add_lambda_context._request_id = request_id


class LogEntry:
    """Helper class for creating structured log entries for S3 storage."""
    
    @staticmethod
    def create_log_entry(
        lambda_name: str,
        request_id: str,
        event_type: str,
        data: Dict[str, Any],
        success: bool = True,
        error_msg: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a structured log entry for S3 storage."""
        return {
            "timestamp": int(time.time()),
            "lambda_name": lambda_name,
            "request_id": request_id,
            "event_type": event_type,
            "data": data,
            "success": success,
            "error_msg": error_msg,
            "service": "govwatcher",
            "version": os.getenv("SERVICE_VERSION", "unknown")
        }
    
    @staticmethod
    def create_s3_key(timestamp: int, lambda_name: str, request_id: str) -> str:
        """Create S3 key for log storage."""
        from datetime import datetime
        dt = datetime.fromtimestamp(timestamp)
        return f"logs/{dt.year:04d}/{dt.month:02d}/{dt.day:02d}/{timestamp}_{lambda_name}_{request_id}.json"


def log_lambda_event(
    logger,
    event_type: str,
    lambda_name: str,
    request_id: str,
    data: Dict[str, Any],
    success: bool = True,
    error_msg: Optional[str] = None
):
    """Log a Lambda event with structured data."""
    log_data = {
        "event_type": event_type,
        "lambda_name": lambda_name,
        "request_id": request_id,
        "success": success,
        **data
    }
    
    if error_msg:
        log_data["error_msg"] = error_msg
    
    if success:
        logger.info(f"Lambda event: {event_type}", **log_data)
    else:
        logger.error(f"Lambda event failed: {event_type}", **log_data)


def get_logger(name: str = None):
    """Get a configured logger instance."""
    if name is None:
        name = __name__
    return structlog.get_logger(name)


# Initialize logging on module import
if not structlog.is_configured():
    setup_logging() 