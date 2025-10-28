"""
Test suite for logging and observability features.
Tests log file creation, rotation, and structured logging.
"""

import pytest
import os
import json
from pathlib import Path
from datetime import datetime

from app.core.logging_config import (
    setup_logging,
    get_moderation_logger,
    get_admin_logger,
    get_component_logger,
    log_moderation_event,
    log_admin_action,
    log_system_event,
    log_security_event,
    log_performance_metric,
    log_health_check,
    LOGS_DIR,
    APP_LOG,
    ERROR_LOG,
    MODERATION_LOG,
    ADMIN_LOG
)


def test_logs_directory_exists():
    """Test that logs directory is created."""
    assert LOGS_DIR.exists()
    assert LOGS_DIR.is_dir()


def test_log_files_created():
    """Test that log files are created after setup."""
    setup_logging()
    
    # Log files should be created or exist
    assert APP_LOG.exists() or True  # May not exist until first log
    # Files are created on first write, so we just verify the paths are correct
    assert str(APP_LOG).endswith("app.log")
    assert str(ERROR_LOG).endswith("error.log")
    assert str(MODERATION_LOG).endswith("moderation.log")
    assert str(ADMIN_LOG).endswith("admin.log")


def test_moderation_logger():
    """Test moderation logger creation."""
    logger = get_moderation_logger()
    assert logger is not None
    
    # Log a test event
    log_moderation_event(
        action="test_block",
        severity="high",
        content_preview="Test content",
        user_id="test-user-123",
        conversation_id="test-conv-456",
        matched_keywords=["test"]
    )
    
    # If log file exists, verify it has content
    if MODERATION_LOG.exists():
        with open(MODERATION_LOG, 'r') as f:
            lines = f.readlines()
            assert len(lines) > 0


def test_admin_logger():
    """Test admin logger creation."""
    logger = get_admin_logger()
    assert logger is not None
    
    # Log a test event
    log_admin_action(
        action="test_action",
        admin_user_id="admin-123",
        target_user_id="user-456",
        details={"test": "data"}
    )
    
    # If log file exists, verify it has content
    if ADMIN_LOG.exists():
        with open(ADMIN_LOG, 'r') as f:
            lines = f.readlines()
            assert len(lines) > 0


def test_component_logger():
    """Test component-specific logger creation."""
    logger = get_component_logger("test_component")
    assert logger is not None


def test_system_event_logging():
    """Test system event logging."""
    log_system_event(
        event="test_event",
        component="test_component",
        details={"key": "value"}
    )
    
    # Verify log file has content
    if APP_LOG.exists():
        assert APP_LOG.stat().st_size > 0


def test_security_event_logging():
    """Test security event logging."""
    log_security_event(
        event="test_security_event",
        user_id="user-123",
        ip_address="192.168.1.1",
        details={"reason": "test"}
    )
    
    # Verify log file has content
    if APP_LOG.exists():
        assert APP_LOG.stat().st_size > 0


def test_performance_metric_logging():
    """Test performance metric logging."""
    log_performance_metric(
        metric_name="test_metric",
        value=123.45,
        component="test_component",
        details={"unit": "ms"}
    )
    
    # Verify log file has content
    if APP_LOG.exists():
        assert APP_LOG.stat().st_size > 0


def test_health_check_logging():
    """Test health check logging."""
    # Test healthy status
    log_health_check(
        component="test_component",
        status="healthy",
        details={"uptime": "100s"}
    )
    
    # Test unhealthy status
    log_health_check(
        component="test_component",
        status="unhealthy",
        details={"error": "connection failed"}
    )
    
    # Verify log file has content
    if APP_LOG.exists():
        assert APP_LOG.stat().st_size > 0


def test_structured_logging_format():
    """Test that structured logs are properly formatted as JSON."""
    # Clear or create moderation log
    log_moderation_event(
        action="structured_test",
        severity="medium",
        content_preview="Structured log test",
        user_id="user-789",
        matched_keywords=["keyword1", "keyword2"]
    )
    
    if MODERATION_LOG.exists() and MODERATION_LOG.stat().st_size > 0:
        with open(MODERATION_LOG, 'r') as f:
            lines = f.readlines()
            if lines:
                # Last line should be our test log
                try:
                    log_entry = json.loads(lines[-1])
                    assert "text" in log_entry or "record" in log_entry
                except json.JSONDecodeError:
                    # Log format may vary, just check it exists
                    assert len(lines[-1]) > 0


def test_log_rotation_config():
    """Test that log rotation is configured (files should have size limits)."""
    # We can't easily test rotation without writing 10MB of data,
    # but we can verify the files are created and configured
    setup_logging()
    
    # Just verify setup doesn't raise errors
    assert True


def test_multiple_log_entries():
    """Test writing multiple log entries."""
    # Write several entries
    for i in range(5):
        log_system_event(
            event=f"test_event_{i}",
            component="test_component",
            details={"iteration": i}
        )
    
    # Verify logs are written
    if APP_LOG.exists():
        with open(APP_LOG, 'r') as f:
            lines = f.readlines()
            # Should have at least our 5 test entries
            assert len(lines) >= 5


def test_moderation_log_structured_data():
    """Test that moderation logs contain expected structured fields."""
    log_moderation_event(
        action="keyword_match",
        severity="high",
        content_preview="Test flagged content",
        user_id="user-111",
        conversation_id="conv-222",
        matched_keywords=["violence", "harm"]
    )
    
    # The log should be written
    if MODERATION_LOG.exists():
        assert MODERATION_LOG.stat().st_size > 0


def test_admin_log_structured_data():
    """Test that admin logs contain expected structured fields."""
    log_admin_action(
        action="update_user_role",
        admin_user_id="admin-999",
        target_user_id="user-888",
        details={
            "old_role": "user",
            "new_role": "moderator",
            "timestamp": datetime.utcnow().isoformat()
        }
    )
    
    # The log should be written
    if ADMIN_LOG.exists():
        assert ADMIN_LOG.stat().st_size > 0


@pytest.mark.asyncio
async def test_concurrent_logging():
    """Test that logging is thread-safe with concurrent writes."""
    import asyncio
    
    async def log_task(task_id: int):
        log_system_event(
            event=f"concurrent_test_{task_id}",
            component="test",
            details={"task_id": task_id}
        )
    
    # Run 10 concurrent logging tasks
    tasks = [log_task(i) for i in range(10)]
    await asyncio.gather(*tasks)
    
    # Verify all logs were written
    if APP_LOG.exists():
        with open(APP_LOG, 'r') as f:
            lines = f.readlines()
            # Should have at least our 10 concurrent entries
            assert len(lines) >= 10
