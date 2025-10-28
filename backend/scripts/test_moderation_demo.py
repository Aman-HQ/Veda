"""
Demonstration script for content moderation functionality.
Shows how the moderation service blocks dangerous content.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.moderation import moderate_content


def test_moderation():
    """Test various content examples through moderation service."""
    
    print("=" * 80)
    print("CONTENT MODERATION DEMONSTRATION")
    print("=" * 80)
    print()
    
    # Test cases with expected results
    test_cases = [
        {
            "content": "I have a mild headache. What should I do?",
            "expected": "SAFE",
            "description": "Safe medical question"
        },
        {
            "content": "I want to kill myself",
            "expected": "BLOCKED",
            "description": "High severity - self-harm"
        },
        {
            "content": "I'm thinking about suicide",
            "expected": "BLOCKED",
            "description": "High severity - suicidal ideation"
        },
        {
            "content": "Can I buy prescription drugs without a prescription?",
            "expected": "FLAGGED",
            "description": "Medium severity - substance abuse"
        },
        {
            "content": "SUICIDE",
            "expected": "BLOCKED",
            "description": "Case insensitive - uppercase"
        },
        {
            "content": "SuIcIdE",
            "expected": "BLOCKED",
            "description": "Case insensitive - mixed case"
        },
        {
            "content": "I studied suicide prevention in school",
            "expected": "BLOCKED",
            "description": "Contextual keyword (may trigger false positive)"
        },
        {
            "content": "I'm feeling a bit frustrated today",
            "expected": "SAFE",
            "description": "Low severity - negative emotion"
        },
    ]
    
    # Run tests
    for i, test_case in enumerate(test_cases, 1):
        print(f"Test {i}: {test_case['description']}")
        print(f"Content: \"{test_case['content']}\"")
        
        result = moderate_content(test_case['content'])
        
        # Determine actual result
        if result.action == "block":
            actual = "BLOCKED"
        elif result.action == "flag":
            actual = "FLAGGED"
        else:
            actual = "SAFE"
        
        # Show results
        status = "✅ PASS" if actual == test_case['expected'] else "❌ FAIL"
        print(f"Expected: {test_case['expected']}")
        print(f"Actual: {actual} ({result.severity or 'none'} severity)")
        
        if result.matched_keywords:
            print(f"Matched Keywords: {result.matched_keywords}")
        
        print(f"Action: {result.action}")
        print(f"Is Safe: {result.is_safe}")
        print(f"Status: {status}")
        print("-" * 80)
        print()
    
    print("=" * 80)
    print("MODERATION STATISTICS")
    print("=" * 80)
    
    # Get statistics
    from app.services.moderation import moderation_service
    stats = moderation_service.get_statistics()
    
    print(f"Moderation Enabled: {stats['enabled']}")
    print(f"Total Rules Loaded: {stats['rules_loaded']}")
    print(f"Total Keywords: {stats['total_keywords']}")
    print(f"Total Checks Performed: {stats['stats']['total_checks']}")
    print(f"Messages Blocked: {stats['stats']['blocked_messages']}")
    print(f"Messages Flagged: {stats['stats']['flagged_messages']}")
    print(f"High Severity Detections: {stats['stats']['high_severity']}")
    print(f"Medium Severity Detections: {stats['stats']['medium_severity']}")
    print(f"Low Severity Detections: {stats['stats']['low_severity']}")
    print(f"Medical Emergency Detections: {stats['stats']['medical_emergency']}")
    print()
    
    print("=" * 80)
    print("DEMONSTRATION COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    test_moderation()
