"""
B10 Unit Tests - Core utilities, auth, moderation
"""

import pytest
from datetime import datetime, timedelta
import bcrypt


class TestPasswordHashing:
    """Test password hashing and verification."""
    
    def test_hash_password(self):
        """Test password hashing."""
        from app.core.security import get_password_hash
        
        password = "testpassword123"
        hashed = get_password_hash(password)
        
        assert hashed != password
        assert len(hashed) > 0
        assert hashed.startswith("$2b$")
    
    def test_verify_password_correct(self):
        """Test password verification with correct password."""
        from app.core.security import get_password_hash, verify_password
        
        password = "testpassword123"
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed) is True
    
    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password."""
        from app.core.security import get_password_hash, verify_password
        
        password = "testpassword123"
        wrong_password = "wrongpassword"
        hashed = get_password_hash(password)
        
        assert verify_password(wrong_password, hashed) is False


class TestJWTTokens:
    """Test JWT token creation and validation."""
    
    def test_create_access_token(self):
        """Test access token creation."""
        from app.core.security import create_access_token
        
        data = {"sub": "test@example.com"}
        token = create_access_token(data)
        
        assert isinstance(token, str)
        assert len(token) > 0
        # JWT has 3 parts separated by dots
        assert token.count('.') == 2
    
    def test_create_access_token_with_expiry(self):
        """Test access token with custom expiry."""
        from app.core.security import create_access_token
        
        data = {"sub": "test@example.com"}
        expires_delta = timedelta(minutes=30)
        token = create_access_token(data, expires_delta=expires_delta)
        
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_decode_valid_token(self):
        """Test decoding valid JWT token."""
        from app.core.security import create_access_token, decode_token
        
        email = "test@example.com"
        token = create_access_token(data={"sub": email})
        
        payload = decode_token(token)
        assert payload is not None
        assert payload.get("sub") == email
    
    def test_decode_invalid_token(self):
        """Test decoding invalid JWT token."""
        from app.core.security import decode_token
        
        invalid_token = "invalid.token.here"
        payload = decode_token(invalid_token)
        
        assert payload is None
    
    def test_decode_expired_token(self):
        """Test decoding expired JWT token."""
        from app.core.security import create_access_token, decode_token
        
        # Create token that expires immediately
        token = create_access_token(
            data={"sub": "test@example.com"},
            expires_delta=timedelta(seconds=-1)
        )
        
        payload = decode_token(token)
        assert payload is None


class TestModeration:
    """Test content moderation."""
    
    def test_check_content_safe(self):
        """Test safe content passes moderation."""
        from app.services.moderation import moderate_content
        
        safe_text = "I have a headache. What should I do?"
        result = moderate_content(safe_text)
        
        assert result.is_safe is True
        assert result.severity is None
        assert len(result.matched_keywords) == 0
    
    def test_check_content_high_severity(self):
        """Test high severity content is blocked."""
        from app.services.moderation import moderate_content
        
        dangerous_text = "I want to kill myself"
        result = moderate_content(dangerous_text)
        
        assert result.is_safe is False
        assert result.severity == "high"
        assert len(result.matched_keywords) > 0
        assert result.action == "block"
    
    def test_check_content_medium_severity(self):
        """Test medium severity content is flagged but allowed."""
        from app.services.moderation import moderate_content
        
        flagged_text = "Can I take this drug without prescription?"
        result = moderate_content(flagged_text)
        
        # Medium severity allows but flags
        assert result.severity == "medium"
        assert len(result.matched_keywords) > 0
        assert result.action == "flag"
    
    def test_check_content_case_insensitive(self):
        """Test moderation is case-insensitive."""
        from app.services.moderation import moderate_content
        
        text1 = "SUICIDE"
        text2 = "suicide"
        text3 = "SuIcIdE"
        
        result1 = moderate_content(text1)
        result2 = moderate_content(text2)
        result3 = moderate_content(text3)
        
        assert result1.is_safe is False
        assert result2.is_safe is False
        assert result3.is_safe is False


class TestUtilities:
    """Test utility functions."""
    
    def test_sanitize_html(self):
        """Test HTML sanitization."""
        # This test assumes you have a sanitize function
        # Adjust based on your actual implementation
        pass
    
    def test_format_date(self):
        """Test date formatting."""
        # This test assumes you have a date formatting function
        # Adjust based on your actual implementation
        pass


class TestConfig:
    """Test configuration loading."""
    
    def test_config_loads(self):
        """Test that config module loads successfully."""
        from app.core import config
        
        assert hasattr(config, 'DATABASE_URL')
        assert hasattr(config, 'JWT_SECRET')
        assert hasattr(config, 'JWT_ALGORITHM')
    
    def test_database_url_format(self):
        """Test DATABASE_URL has correct format."""
        from app.core.config import DATABASE_URL
        
        assert isinstance(DATABASE_URL, str)
        # Should start with postgresql+asyncpg:// or sqlite+aiosqlite://
        assert DATABASE_URL.startswith(("postgresql+asyncpg://", "sqlite+aiosqlite://"))
