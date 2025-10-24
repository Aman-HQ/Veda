"""
Tests for B08 Moderation & Safety functionality.
Tests content moderation, keyword filtering, and safety responses.
"""

import pytest
import asyncio
import json
import tempfile
import os
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path

from app.services.moderation import (
    ModerationService, 
    ModerationResult, 
    moderate_content, 
    is_content_safe,
    get_safe_response_for_blocked_content
)
from app.services.llm_provider import LLMProvider
from app.core.logging_config import setup_logging


class TestModerationService:
    """Test the ModerationService class."""
    
    @pytest.fixture
    def temp_rules_file(self):
        """Create a temporary rules file for testing."""
        
        test_rules = {
            "high": ["suicide", "kill myself", "self harm"],
            "medium": ["drug", "prescription abuse", "weapon"],
            "low": ["stupid", "hate", "annoying"],
            "medical_emergency": ["chest pain", "heart attack", "can't breathe"]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_rules, f)
            temp_file = f.name
        
        yield temp_file
        
        # Cleanup
        os.unlink(temp_file)
    
    @pytest.fixture
    def moderation_service(self, temp_rules_file):
        """Create a ModerationService instance with test rules."""
        return ModerationService(rules_file=temp_rules_file)
    
    def test_load_rules_success(self, moderation_service):
        """Test successful loading of moderation rules."""
        
        assert len(moderation_service.rules) == 4
        assert "high" in moderation_service.rules
        assert "suicide" in moderation_service.rules["high"]
        assert "chest pain" in moderation_service.rules["medical_emergency"]
    
    def test_load_rules_file_not_found(self):
        """Test handling of missing rules file."""
        
        service = ModerationService(rules_file="nonexistent.json")
        assert service.rules == {"high": [], "medium": [], "low": [], "medical_emergency": []}
    
    def test_high_severity_blocking(self, moderation_service):
        """Test that high severity content is blocked."""
        
        result = moderation_service.moderate_content("I want to kill myself")
        
        assert not result.is_safe
        assert result.severity == "high"
        assert result.action == "block"
        assert "kill myself" in result.matched_keywords
        assert "high-risk keywords" in result.message
    
    def test_medical_emergency_flagging(self, moderation_service):
        """Test that medical emergency content is flagged appropriately."""
        
        result = moderation_service.moderate_content("I'm having severe chest pain")
        
        assert result.is_safe  # Not unsafe, but needs special handling
        assert result.severity == "medical_emergency"
        assert result.action == "flag"
        assert "chest pain" in result.matched_keywords
        assert result.metadata["emergency_flag"] is True
    
    def test_medium_severity_flagging(self, moderation_service):
        """Test that medium severity content is flagged."""
        
        result = moderation_service.moderate_content("I have a drug problem")
        
        assert result.is_safe
        assert result.severity == "medium"
        assert result.action == "flag"
        assert "drug" in result.matched_keywords
    
    def test_low_severity_warning(self, moderation_service):
        """Test that low severity content generates warnings."""
        
        result = moderation_service.moderate_content("This is so stupid")
        
        assert result.is_safe
        assert result.severity == "low"
        assert result.action == "allow"
        assert "stupid" in result.matched_keywords
    
    def test_safe_content(self, moderation_service):
        """Test that safe content passes moderation."""
        
        result = moderation_service.moderate_content("I have a headache, what should I do?")
        
        assert result.is_safe
        assert result.severity is None
        assert result.action == "allow"
        assert len(result.matched_keywords) == 0
    
    def test_empty_content(self, moderation_service):
        """Test handling of empty content."""
        
        result = moderation_service.moderate_content("")
        
        assert result.is_safe
        assert result.action == "allow"
        assert "Empty content" in result.message
    
    def test_case_insensitive_matching(self, moderation_service):
        """Test that keyword matching is case-insensitive."""
        
        result = moderation_service.moderate_content("I want to KILL MYSELF")
        
        assert not result.is_safe
        assert result.severity == "high"
        assert result.action == "block"
    
    def test_word_boundary_matching(self, moderation_service):
        """Test that word boundaries are respected in matching."""
        
        # "assault" should not match "massage" (partial word)
        result = moderation_service.moderate_content("I need a massage")
        
        assert result.is_safe
        assert result.action == "allow"
    
    def test_multiple_keywords_same_severity(self, moderation_service):
        """Test handling of multiple keywords in same severity level."""
        
        result = moderation_service.moderate_content("I hate this stupid situation")
        
        assert result.is_safe
        assert result.severity == "low"
        assert result.action == "allow"
        assert len(result.matched_keywords) >= 2
    
    def test_multiple_keywords_different_severity(self, moderation_service):
        """Test that highest severity wins when multiple levels match."""
        
        result = moderation_service.moderate_content("I hate this and want to kill myself")
        
        # Should prioritize "high" over "low"
        assert not result.is_safe
        assert result.severity == "high"
        assert result.action == "block"
    
    def test_moderation_disabled(self, temp_rules_file):
        """Test behavior when moderation is disabled."""
        
        with patch('app.services.moderation.ENABLE_MODERATION', False):
            service = ModerationService(rules_file=temp_rules_file)
            result = service.moderate_content("I want to kill myself")
            
            assert result.is_safe
            assert result.action == "allow"
            assert "Moderation disabled" in result.message
    
    def test_conversation_moderation(self, moderation_service):
        """Test moderation of entire conversation threads."""
        
        messages = [
            {"content": "Hello, how are you?"},
            {"content": "I'm feeling really stupid today"},
            {"content": "I want to kill myself"},
            {"content": "Just kidding, I'm fine"}
        ]
        
        results = moderation_service.moderate_conversation(messages)
        
        assert len(results) == 4
        assert results[0].is_safe and results[0].action == "allow"
        assert results[1].is_safe and results[1].severity == "low"
        assert not results[2].is_safe and results[2].severity == "high"
        assert results[3].is_safe and results[3].action == "allow"
    
    def test_statistics_tracking(self, moderation_service):
        """Test that moderation statistics are tracked correctly."""
        
        # Generate some moderation events
        moderation_service.moderate_content("I want to kill myself")  # blocked
        moderation_service.moderate_content("I have a drug problem")  # flagged
        moderation_service.moderate_content("This is stupid")  # warning
        moderation_service.moderate_content("I have chest pain")  # emergency
        
        stats = moderation_service.get_statistics()
        
        assert stats["stats"]["total_checks"] == 4
        assert stats["stats"]["blocked_messages"] == 1
        assert stats["stats"]["flagged_messages"] >= 2  # medium + emergency
        assert stats["stats"]["high_severity"] == 1
        assert stats["stats"]["medical_emergency"] == 1
    
    def test_safe_response_generation(self, moderation_service):
        """Test generation of safe responses for blocked content."""
        
        high_response = moderation_service.get_safe_response_for_blocked_content("high")
        emergency_response = moderation_service.get_safe_response_for_blocked_content("medical_emergency")
        
        assert "crisis hotline" in high_response
        assert "911" in emergency_response
        assert "MEDICAL EMERGENCY" in emergency_response
    
    def test_emergency_resources_addition(self, moderation_service):
        """Test addition of emergency resources to responses."""
        
        original_response = "You should see a doctor."
        enhanced_response = moderation_service.add_emergency_resources_to_response(original_response)
        
        assert original_response in enhanced_response
        assert "Emergency: 911" in enhanced_response
        assert "Suicide Prevention Lifeline: 988" in enhanced_response
    
    def test_health_check(self, moderation_service):
        """Test moderation service health check."""
        
        health = moderation_service.health_check()
        
        assert health["status"] == "healthy"
        assert health["enabled"] is True
        assert health["rules_loaded"] is True
        assert health["total_keywords"] > 0
    
    def test_rules_reload(self, moderation_service, temp_rules_file):
        """Test reloading of moderation rules."""
        
        # Modify the rules file
        new_rules = {
            "high": ["test_keyword"],
            "medium": [],
            "low": [],
            "medical_emergency": []
        }
        
        with open(temp_rules_file, 'w') as f:
            json.dump(new_rules, f)
        
        # Reload rules
        success = moderation_service.reload_rules()
        
        assert success is True
        assert "test_keyword" in moderation_service.rules["high"]


class TestModerationIntegration:
    """Test integration of moderation with other components."""
    
    @pytest.fixture
    def mock_llm_provider(self):
        """Create a mock LLM provider for testing."""
        provider = LLMProvider(use_dev_mode=True)
        return provider
    
    @pytest.mark.asyncio
    async def test_llm_pipeline_moderation_blocking(self, mock_llm_provider):
        """Test that LLM pipeline blocks high-risk content."""
        
        response = await mock_llm_provider.process_pipeline(
            text="I want to kill myself",
            user_id="test_user",
            conversation_id="test_conv"
        )
        
        assert "crisis hotline" in response
        assert "not able to respond" in response
    
    @pytest.mark.asyncio
    async def test_llm_pipeline_emergency_detection(self, mock_llm_provider):
        """Test that LLM pipeline detects medical emergencies."""
        
        response = await mock_llm_provider.process_pipeline(
            text="I'm having severe chest pain",
            user_id="test_user",
            conversation_id="test_conv"
        )
        
        assert "Emergency: 911" in response
        assert "Emergency Resources" in response
    
    @pytest.mark.asyncio
    async def test_llm_pipeline_safe_content(self, mock_llm_provider):
        """Test that LLM pipeline processes safe content normally."""
        
        response = await mock_llm_provider.process_pipeline(
            text="I have a headache, what should I do?",
            user_id="test_user",
            conversation_id="test_conv"
        )
        
        assert "Medical Disclaimer" in response
        assert len(response) > 50  # Should have substantial content
    
    @pytest.mark.asyncio
    async def test_streaming_moderation(self, mock_llm_provider):
        """Test that streaming responses are also moderated."""
        
        chunks = []
        async for chunk in mock_llm_provider.process_pipeline_stream(
            text="I want to kill myself",
            user_id="test_user",
            conversation_id="test_conv"
        ):
            chunks.append(chunk)
        
        full_response = "".join(chunks)
        assert "crisis hotline" in full_response
        assert "not able to" in full_response


class TestConvenienceFunctions:
    """Test the convenience functions for moderation."""
    
    def test_moderate_content_function(self):
        """Test the global moderate_content function."""
        
        result = moderate_content("I have a headache")
        
        assert isinstance(result, ModerationResult)
        assert result.is_safe
    
    def test_is_content_safe_function(self):
        """Test the is_content_safe convenience function."""
        
        assert is_content_safe("I have a headache") is True
        assert is_content_safe("I want to kill myself") is False
    
    def test_get_safe_response_function(self):
        """Test the get_safe_response_for_blocked_content function."""
        
        response = get_safe_response_for_blocked_content("high")
        
        assert "crisis hotline" in response
        assert "not able to respond" in response


class TestModerationLogging:
    """Test moderation logging functionality."""
    
    @pytest.fixture(autouse=True)
    def setup_logging(self):
        """Setup logging for tests."""
        setup_logging()
    
    @pytest.mark.asyncio
    async def test_moderation_event_logging(self, caplog):
        """Test that moderation events are logged properly."""
        
        with patch('app.services.moderation.logger') as mock_logger:
            service = ModerationService()
            service.moderate_content("I want to kill myself")
            
            # Check that error log was called for high severity
            mock_logger.error.assert_called()
            call_args = mock_logger.error.call_args[0][0]
            assert "HIGH SEVERITY CONTENT BLOCKED" in call_args
    
    @pytest.mark.asyncio
    async def test_emergency_event_logging(self, caplog):
        """Test that medical emergency events are logged properly."""
        
        with patch('app.services.moderation.logger') as mock_logger:
            service = ModerationService()
            service.moderate_content("I'm having a heart attack")
            
            # Check that warning log was called for emergency
            mock_logger.warning.assert_called()
            call_args = mock_logger.warning.call_args[0][0]
            assert "MEDICAL EMERGENCY DETECTED" in call_args


class TestModerationEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_malformed_rules_file(self):
        """Test handling of malformed JSON rules file."""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("{ invalid json }")
            temp_file = f.name
        
        try:
            service = ModerationService(rules_file=temp_file)
            # Should fall back to empty rules
            assert service.rules == {"high": [], "medium": [], "low": [], "medical_emergency": []}
        finally:
            os.unlink(temp_file)
    
    def test_very_long_content(self):
        """Test moderation of very long content."""
        
        service = ModerationService()
        long_content = "This is a normal message. " * 1000 + "I want to kill myself"
        
        result = service.moderate_content(long_content)
        
        assert not result.is_safe
        assert result.severity == "high"
        assert result.action == "block"
    
    def test_unicode_content(self):
        """Test moderation of Unicode content."""
        
        service = ModerationService()
        unicode_content = "I have a headache 🤕 and feel terrible 😢"
        
        result = service.moderate_content(unicode_content)
        
        assert result.is_safe
        assert result.action == "allow"
    
    def test_mixed_language_content(self):
        """Test moderation of mixed language content."""
        
        service = ModerationService()
        mixed_content = "Hello, मुझे सिरदर्द है। I have a headache."
        
        result = service.moderate_content(mixed_content)
        
        assert result.is_safe
        assert result.action == "allow"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
