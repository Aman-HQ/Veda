import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.services.moderation import moderate_content

# Test cases from the user's report
test_messages = [
    "I want to commit suicide",
    "suicide",
    "kill",
    "die", 
    "chest pain",
    "I want to kill someone",
    "Where can I buy cocaine?"
]

print("=" * 60)
print("MODERATION SERVICE TEST")
print("=" * 60)

for msg in test_messages:
    result = moderate_content(msg)
    print(f"\nMessage: '{msg}'")
    print(f"  ├─ Is Safe: {result.is_safe}")
    print(f"  ├─ Severity: {result.severity}")
    print(f"  ├─ Action: {result.action}")
    print(f"  ├─ Matched Keywords: {result.matched_keywords}")
    print(f"  └─ Message: {result.message}")
