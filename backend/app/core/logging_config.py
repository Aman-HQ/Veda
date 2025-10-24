"""
Logging configuration for Veda Healthcare Chatbot.
Sets up structured logging with loguru and separate log files.
"""

import os
import sys
from pathlib import Path
from loguru import logger
from app.core.config import DEBUG

# Create logs directory
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)

# Log file paths
APP_LOG = LOGS_DIR / "app.log"
ERROR_LOG = LOGS_DIR / "error.log"
MODERATION_LOG = LOGS_DIR / "moderation.log"
ADMIN_LOG = LOGS_DIR / "admin.log"


def setup_logging():
    """
    Configure structured logging with loguru.
    Sets up separate log files for different types of events.
    """
    
    # Remove default logger
    logger.remove()
    
    # Console logging (for development)
    if DEBUG:
        logger.add(
            sys.stdout,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            level="DEBUG",
            colorize=True
        )
    else:
        logger.add(
            sys.stdout,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            level="INFO",
            colorize=False
        )
    
    # Main application log
    logger.add(
        APP_LOG,
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {extra} | {message}",
        level="INFO",
        rotation="10 MB",
        retention="7 days",
        compression="zip",
        serialize=False,
        enqueue=True,  # Thread-safe logging
        backtrace=True,
        diagnose=True
    )
    
    # Error log (errors and exceptions only)
    logger.add(
        ERROR_LOG,
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {extra} | {message}",
        level="ERROR",
        rotation="5 MB",
        retention="14 days",
        compression="zip",
        serialize=False,
        enqueue=True,
        backtrace=True,
        diagnose=True
    )
    
    # Moderation log (content moderation events)
    logger.add(
        MODERATION_LOG,
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {extra} | {message}",
        level="INFO",
        rotation="5 MB",
        retention="30 days",  # Keep moderation logs longer for compliance
        compression="zip",
        serialize=True,  # JSON format for structured data
        enqueue=True,
        filter=lambda record: "moderation" in record["extra"]
    )
    
    # Admin log (admin actions and system events)
    logger.add(
        ADMIN_LOG,
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {extra} | {message}",
        level="INFO",
        rotation="5 MB",
        retention="30 days",
        compression="zip",
        serialize=True,
        enqueue=True,
        filter=lambda record: "admin" in record["extra"]
    )
    
    logger.info("Logging system initialized", extra={"component": "logging"})


def get_moderation_logger():
    """Get logger for moderation events."""
    return logger.bind(moderation=True)


def get_admin_logger():
    """Get logger for admin events."""
    return logger.bind(admin=True)


def get_component_logger(component: str):
    """Get logger for a specific component."""
    return logger.bind(component=component)


def log_request(method: str, path: str, user_id: str = None, duration: float = None):
    """Log HTTP request with structured data."""
    logger.info(
        f"{method} {path}",
        extra={
            "component": "http",
            "method": method,
            "path": path,
            "user_id": user_id,
            "duration_ms": duration * 1000 if duration else None
        }
    )


def log_moderation_event(
    action: str,
    severity: str,
    content_preview: str,
    user_id: str = None,
    conversation_id: str = None,
    matched_keywords: list = None
):
    """Log moderation event with structured data."""
    moderation_logger = get_moderation_logger()
    
    moderation_logger.info(
        f"Moderation {action}: {severity} severity",
        extra={
            "action": action,
            "severity": severity,
            "content_preview": content_preview,
            "user_id": user_id,
            "conversation_id": conversation_id,
            "matched_keywords": matched_keywords or [],
            "event_type": "content_moderation"
        }
    )


def log_admin_action(
    action: str,
    admin_user_id: str,
    target_user_id: str = None,
    details: dict = None
):
    """Log admin action with structured data."""
    admin_logger = get_admin_logger()
    
    admin_logger.info(
        f"Admin action: {action}",
        extra={
            "action": action,
            "admin_user_id": admin_user_id,
            "target_user_id": target_user_id,
            "details": details or {},
            "event_type": "admin_action"
        }
    )


def log_system_event(event: str, component: str, details: dict = None):
    """Log system event with structured data."""
    logger.info(
        f"System event: {event}",
        extra={
            "component": component,
            "event": event,
            "details": details or {},
            "event_type": "system"
        }
    )


def log_security_event(event: str, user_id: str = None, ip_address: str = None, details: dict = None):
    """Log security-related event."""
    logger.warning(
        f"Security event: {event}",
        extra={
            "component": "security",
            "event": event,
            "user_id": user_id,
            "ip_address": ip_address,
            "details": details or {},
            "event_type": "security"
        }
    )


def log_performance_metric(metric_name: str, value: float, component: str, details: dict = None):
    """Log performance metric."""
    logger.info(
        f"Performance metric: {metric_name} = {value}",
        extra={
            "component": component,
            "metric_name": metric_name,
            "metric_value": value,
            "details": details or {},
            "event_type": "performance"
        }
    )


def log_health_check(component: str, status: str, details: dict = None):
    """Log health check result."""
    level = "INFO" if status == "healthy" else "WARNING"
    
    logger.log(
        level,
        f"Health check: {component} is {status}",
        extra={
            "component": component,
            "health_status": status,
            "details": details or {},
            "event_type": "health_check"
        }
    )


# Exception handler for uncaught exceptions
def handle_exception(exc_type, exc_value, exc_traceback):
    """Handle uncaught exceptions with structured logging."""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    logger.error(
        "Uncaught exception",
        extra={
            "component": "system",
            "exception_type": exc_type.__name__,
            "exception_value": str(exc_value),
            "event_type": "uncaught_exception"
        }
    )


# Set up exception handler
sys.excepthook = handle_exception


# Initialize logging when module is imported
if __name__ != "__main__":
    setup_logging()
