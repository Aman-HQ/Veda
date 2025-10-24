"""
Content Moderation Service for Veda Healthcare Chatbot.
Implements keyword-based screening for safety and compliance.
"""

import json
import re
import os
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
from datetime import datetime
import logging

from app.core.config import ENABLE_MODERATION

logger = logging.getLogger(__name__)


class ModerationResult:
    """Result of content moderation analysis."""
    
    def __init__(
        self,
        is_safe: bool = True,
        severity: Optional[str] = None,
        matched_keywords: Optional[List[str]] = None,
        action: str = "allow",
        message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.is_safe = is_safe
        self.severity = severity
        self.matched_keywords = matched_keywords or []
        self.action = action  # "allow", "flag", "block"
        self.message = message
        self.metadata = metadata or {}
        self.timestamp = datetime.utcnow().isoformat()


class ModerationService:
    """
    Content moderation service with keyword-based filtering.
    Supports multiple severity levels and configurable actions.
    """
    
    def __init__(self, rules_file: Optional[str] = None):
        self.rules_file = rules_file or os.path.join(
            os.path.dirname(__file__), 
            "..", 
            "core", 
            "moderation_rules.json"
        )
        self.rules = self._load_rules()
        self.enabled = ENABLE_MODERATION
        
        # Compile regex patterns for better performance
        self._compiled_patterns = self._compile_patterns()
        
        # Statistics tracking
        self.stats = {
            "total_checks": 0,
            "blocked_messages": 0,
            "flagged_messages": 0,
            "high_severity": 0,
            "medium_severity": 0,
            "low_severity": 0,
            "medical_emergency": 0
        }
        
        logger.info(f"Moderation service initialized (enabled: {self.enabled})")
    
    def _load_rules(self) -> Dict[str, List[str]]:
        """Load moderation rules from JSON file."""
        
        try:
            with open(self.rules_file, 'r', encoding='utf-8') as f:
                rules = json.load(f)
            
            logger.info(f"Loaded moderation rules from {self.rules_file}")
            logger.info(f"Rule categories: {list(rules.keys())}")
            
            return rules
        except FileNotFoundError:
            logger.error(f"Moderation rules file not found: {self.rules_file}")
            return {"high": [], "medium": [], "low": [], "medical_emergency": []}
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in moderation rules file: {e}")
            return {"high": [], "medium": [], "low": [], "medical_emergency": []}
        except Exception as e:
            logger.error(f"Error loading moderation rules: {e}")
            return {"high": [], "medium": [], "low": [], "medical_emergency": []}
    
    def _compile_patterns(self) -> Dict[str, List[re.Pattern]]:
        """Compile regex patterns for efficient matching."""
        
        compiled = {}
        
        for severity, keywords in self.rules.items():
            patterns = []
            for keyword in keywords:
                # Create word boundary pattern for better matching
                # This prevents partial matches (e.g., "assault" in "massage")
                pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
                try:
                    compiled_pattern = re.compile(pattern, re.IGNORECASE)
                    patterns.append(compiled_pattern)
                except re.error as e:
                    logger.warning(f"Invalid regex pattern for '{keyword}': {e}")
            
            compiled[severity] = patterns
        
        return compiled
    
    def moderate_content(self, content: str, context: Optional[Dict] = None) -> ModerationResult:
        """
        Moderate content for safety and compliance.
        
        Args:
            content: Text content to moderate
            context: Additional context (user_id, conversation_id, etc.)
            
        Returns:
            ModerationResult with analysis and recommended action
        """
        
        if not self.enabled:
            return ModerationResult(is_safe=True, action="allow", message="Moderation disabled")
        
        if not content or not content.strip():
            return ModerationResult(is_safe=True, action="allow", message="Empty content")
        
        self.stats["total_checks"] += 1
        
        # Normalize content for analysis
        normalized_content = content.lower().strip()
        
        # Check each severity level
        for severity in ["high", "medium", "low", "medical_emergency"]:
            matched_keywords = self._check_severity_level(normalized_content, severity)
            
            if matched_keywords:
                result = self._create_result_for_severity(
                    severity, 
                    matched_keywords, 
                    content, 
                    context
                )
                
                # Log the moderation event
                self._log_moderation_event(result, content, context)
                
                # Update statistics
                self._update_stats(severity, result.action)
                
                return result
        
        # No matches found - content is safe
        return ModerationResult(
            is_safe=True,
            action="allow",
            message="Content passed moderation checks"
        )
    
    def _check_severity_level(self, content: str, severity: str) -> List[str]:
        """Check content against patterns for a specific severity level."""
        
        matched_keywords = []
        patterns = self._compiled_patterns.get(severity, [])
        
        for pattern in patterns:
            matches = pattern.findall(content)
            if matches:
                # Get the original keyword from the pattern
                keyword = pattern.pattern.replace(r'\b', '').replace('\\', '')
                matched_keywords.extend(matches)
        
        return matched_keywords
    
    def _create_result_for_severity(
        self, 
        severity: str, 
        matched_keywords: List[str], 
        content: str, 
        context: Optional[Dict]
    ) -> ModerationResult:
        """Create moderation result based on severity level."""
        
        if severity == "high":
            return ModerationResult(
                is_safe=False,
                severity=severity,
                matched_keywords=matched_keywords,
                action="block",
                message="Content blocked due to high-risk keywords",
                metadata={
                    "blocked_reason": "high_severity_keywords",
                    "matched_count": len(matched_keywords),
                    "context": context
                }
            )
        
        elif severity == "medical_emergency":
            return ModerationResult(
                is_safe=True,  # Not unsafe, but needs special handling
                severity=severity,
                matched_keywords=matched_keywords,
                action="flag",
                message="Medical emergency keywords detected - prioritize response",
                metadata={
                    "emergency_flag": True,
                    "matched_count": len(matched_keywords),
                    "context": context,
                    "recommended_action": "immediate_medical_attention"
                }
            )
        
        elif severity == "medium":
            return ModerationResult(
                is_safe=True,
                severity=severity,
                matched_keywords=matched_keywords,
                action="flag",
                message="Content flagged for review",
                metadata={
                    "flagged_reason": "medium_severity_keywords",
                    "matched_count": len(matched_keywords),
                    "context": context
                }
            )
        
        elif severity == "low":
            return ModerationResult(
                is_safe=True,
                severity=severity,
                matched_keywords=matched_keywords,
                action="allow",
                message="Content allowed with warning logged",
                metadata={
                    "warning_reason": "low_severity_keywords",
                    "matched_count": len(matched_keywords),
                    "context": context
                }
            )
        
        else:
            return ModerationResult(is_safe=True, action="allow")
    
    def _log_moderation_event(
        self, 
        result: ModerationResult, 
        content: str, 
        context: Optional[Dict]
    ):
        """Log moderation events for admin review."""
        
        log_entry = {
            "timestamp": result.timestamp,
            "severity": result.severity,
            "action": result.action,
            "matched_keywords": result.matched_keywords,
            "content_length": len(content),
            "content_preview": content[:100] + "..." if len(content) > 100 else content,
            "context": context or {},
            "metadata": result.metadata
        }
        
        # Use different log levels based on severity
        if result.severity == "high":
            logger.error(f"HIGH SEVERITY CONTENT BLOCKED: {log_entry}")
        elif result.severity == "medical_emergency":
            logger.warning(f"MEDICAL EMERGENCY DETECTED: {log_entry}")
        elif result.severity == "medium":
            logger.warning(f"MEDIUM SEVERITY CONTENT FLAGGED: {log_entry}")
        elif result.severity == "low":
            logger.info(f"LOW SEVERITY CONTENT WARNING: {log_entry}")
    
    def _update_stats(self, severity: str, action: str):
        """Update moderation statistics."""
        
        if action == "block":
            self.stats["blocked_messages"] += 1
        elif action == "flag":
            self.stats["flagged_messages"] += 1
        
        # Update severity-specific counters
        severity_key = f"{severity}_severity" if severity != "medical_emergency" else "medical_emergency"
        if severity_key in self.stats:
            self.stats[severity_key] += 1
    
    def moderate_conversation(self, messages: List[Dict[str, str]]) -> List[ModerationResult]:
        """
        Moderate an entire conversation thread.
        
        Args:
            messages: List of message dictionaries with 'content' and optional metadata
            
        Returns:
            List of ModerationResult objects for each message
        """
        
        results = []
        
        for i, message in enumerate(messages):
            content = message.get("content", "")
            context = {
                "message_index": i,
                "total_messages": len(messages),
                "user_id": message.get("user_id"),
                "conversation_id": message.get("conversation_id")
            }
            
            result = self.moderate_content(content, context)
            results.append(result)
        
        return results
    
    def get_safe_response_for_blocked_content(self, severity: str = "high") -> str:
        """
        Get a safe response message for blocked content.
        
        Args:
            severity: Severity level of the blocked content
            
        Returns:
            Safe response message
        """
        
        if severity == "high":
            return (
                "I'm not able to respond to that type of content. If you're experiencing "
                "thoughts of self-harm or are in crisis, please reach out to a mental health "
                "professional or crisis hotline immediately. For medical emergencies, call 911. "
                "I'm here to help with general health information and questions."
            )
        elif severity == "medical_emergency":
            return (
                "⚠️ **MEDICAL EMERGENCY DETECTED** ⚠️\n\n"
                "If you are experiencing a medical emergency, please:\n"
                "• Call 911 immediately\n"
                "• Go to the nearest emergency room\n"
                "• Contact your healthcare provider\n\n"
                "I cannot provide emergency medical care. Please seek immediate professional help."
            )
        else:
            return (
                "I understand you may be frustrated, but I'd like to keep our conversation "
                "respectful and focused on helping with your health questions. How can I "
                "assist you with medical information today?"
            )
    
    def add_emergency_resources_to_response(self, response: str) -> str:
        """Add emergency resources to responses when appropriate."""
        
        emergency_resources = (
            "\n\n🆘 **Emergency Resources:**\n"
            "• Emergency: 911\n"
            "• Suicide Prevention Lifeline: 988\n"
            "• Crisis Text Line: Text HOME to 741741\n"
            "• Poison Control: 1-800-222-1222"
        )
        
        return response + emergency_resources
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get moderation statistics."""
        
        return {
            "enabled": self.enabled,
            "rules_loaded": len(self.rules),
            "total_keywords": sum(len(keywords) for keywords in self.rules.values()),
            "stats": self.stats.copy(),
            "rules_file": self.rules_file
        }
    
    def reload_rules(self) -> bool:
        """Reload moderation rules from file."""
        
        try:
            old_rules_count = sum(len(keywords) for keywords in self.rules.values())
            self.rules = self._load_rules()
            self._compiled_patterns = self._compile_patterns()
            new_rules_count = sum(len(keywords) for keywords in self.rules.values())
            
            logger.info(f"Moderation rules reloaded: {old_rules_count} -> {new_rules_count} keywords")
            return True
        except Exception as e:
            logger.error(f"Failed to reload moderation rules: {e}")
            return False
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check on moderation service."""
        
        health = {
            "status": "healthy",
            "enabled": self.enabled,
            "rules_loaded": len(self.rules) > 0,
            "total_keywords": sum(len(keywords) for keywords in self.rules.values()),
            "compiled_patterns": len(self._compiled_patterns),
            "stats": self.stats
        }
        
        if not self.rules:
            health["status"] = "degraded"
            health["warning"] = "No moderation rules loaded"
        
        return health


# Global moderation service instance
moderation_service = ModerationService()


# Convenience functions for easy import
def moderate_content(content: str, context: Optional[Dict] = None) -> ModerationResult:
    """Moderate content using the global moderation service."""
    return moderation_service.moderate_content(content, context)


def is_content_safe(content: str) -> bool:
    """Quick check if content is safe."""
    result = moderation_service.moderate_content(content)
    return result.is_safe and result.action != "block"


def get_safe_response_for_blocked_content(severity: str = "high") -> str:
    """Get safe response for blocked content."""
    return moderation_service.get_safe_response_for_blocked_content(severity)
