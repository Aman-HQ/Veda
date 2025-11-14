"""
End-to-end test of moderation flow via API.
Tests the full pipeline: user sends message → moderation → storage → admin query.
"""

import requests
import json

BASE_URL = "http://localhost:8000"

# You'll need to set these tokens from a logged-in user
# Get them by logging in via the frontend or auth API
ACCESS_TOKEN = None  # Set this before running


def login():
    """Login and get access token."""
    global ACCESS_TOKEN
    
    print("\n" + "="*60)
    print("Login to get access token")
    print("="*60)
    
    # Try to login with test credentials
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={
            "email": "aman.23209@knit.ac.in",  # Update with your test user
            "password": "Test@123"  # Update with your test password
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        ACCESS_TOKEN = data.get("access_token")
        print(f"✓ Logged in successfully")
        print(f"  User: {data.get('user', {}).get('email')}")
        return True
    else:
        print(f"❌ Login failed: {response.status_code}")
        print(f"   {response.text}")
        return False


def create_conversation():
    """Create a test conversation."""
    print("\n" + "="*60)
    print("Creating test conversation")
    print("="*60)
    
    response = requests.post(
        f"{BASE_URL}/api/conversations/",
        json={"title": "Moderation Test Conversation"},
        headers={"Authorization": f"Bearer {ACCESS_TOKEN}"}
    )
    
    if response.status_code == 201:
        data = response.json()
        conv_id = data["id"]
        print(f"✓ Conversation created: {conv_id}")
        return conv_id
    else:
        print(f"❌ Failed to create conversation: {response.status_code}")
        print(f"   {response.text}")
        return None


def test_blocked_message(conversation_id):
    """Test HIGH severity message (should be blocked)."""
    print("\n" + "="*60)
    print("TEST 1: HIGH severity - blocked message")
    print("="*60)
    
    # Send message with HIGH severity keyword
    response = requests.post(
        f"{BASE_URL}/api/conversations/{conversation_id}/messages",
        json={
            "content": "I want to kill myself"
        },
        headers={"Authorization": f"Bearer {ACCESS_TOKEN}"}
    )
    
    print(f"Response status: {response.status_code}")
    print(f"Response body: {response.text[:500]}")
    
    # Should be blocked (400 error)
    if response.status_code == 400:
        data = response.json()
        print("✅ Message correctly blocked by moderation")
        print(f"   Detail: {data.get('detail')}")
        return True
    else:
        print("❌ Message was not blocked (expected 400)")
        return False


def test_flagged_message(conversation_id):
    """Test MEDIUM severity message (should be flagged but allowed)."""
    print("\n" + "="*60)
    print("TEST 2: MEDIUM severity - flagged message")
    print("="*60)
    
    # Send message with MEDIUM severity keyword
    response = requests.post(
        f"{BASE_URL}/api/conversations/{conversation_id}/messages",
        json={
            "content": "Where can I buy cocaine near me?"
        },
        headers={"Authorization": f"Bearer {ACCESS_TOKEN}"}
    )
    
    print(f"Response status: {response.status_code}")
    
    # Should succeed but be flagged
    if response.status_code == 201:
        data = response.json()
        message_id = data["id"]
        print(f"✅ Message created successfully: {message_id}")
        print(f"   Status: {data.get('status')}")
        print(f"   Metadata: {data.get('message_metadata')}")
        
        # Verify status is "flagged"
        if data.get("status") == "flagged":
            print("✅ Message correctly flagged")
            return True, message_id
        else:
            print(f"❌ Message status is '{data.get('status')}', expected 'flagged'")
            return False, message_id
    else:
        print(f"❌ Message creation failed: {response.text}")
        return False, None


def test_emergency_message(conversation_id):
    """Test MEDICAL_EMERGENCY severity message (should be flagged)."""
    print("\n" + "="*60)
    print("TEST 3: MEDICAL_EMERGENCY severity - flagged message")
    print("="*60)
    
    response = requests.post(
        f"{BASE_URL}/api/conversations/{conversation_id}/messages",
        json={
            "content": "I'm having severe chest pain and trouble breathing"
        },
        headers={"Authorization": f"Bearer {ACCESS_TOKEN}"}
    )
    
    print(f"Response status: {response.status_code}")
    
    if response.status_code == 201:
        data = response.json()
        message_id = data["id"]
        print(f"✅ Message created successfully: {message_id}")
        print(f"   Status: {data.get('status')}")
        
        if data.get("status") == "flagged":
            print("✅ Emergency message correctly flagged")
            return True, message_id
        else:
            print(f"❌ Message status is '{data.get('status')}', expected 'flagged'")
            return False, message_id
    else:
        print(f"❌ Message creation failed: {response.text}")
        return False, None


def test_normal_message(conversation_id):
    """Test normal message (should be sent)."""
    print("\n" + "="*60)
    print("TEST 4: Normal message - no moderation")
    print("="*60)
    
    response = requests.post(
        f"{BASE_URL}/api/conversations/{conversation_id}/messages",
        json={
            "content": "What are the symptoms of diabetes?"
        },
        headers={"Authorization": f"Bearer {ACCESS_TOKEN}"}
    )
    
    print(f"Response status: {response.status_code}")
    
    if response.status_code == 201:
        data = response.json()
        message_id = data["id"]
        print(f"✅ Message created successfully: {message_id}")
        print(f"   Status: {data.get('status')}")
        
        if data.get("status") == "sent":
            print("✅ Normal message correctly marked as 'sent'")
            return True, message_id
        else:
            print(f"❌ Message status is '{data.get('status')}', expected 'sent'")
            return False, message_id
    else:
        print(f"❌ Message creation failed: {response.text}")
        return False, None


def test_admin_moderation_query():
    """Test admin endpoint to query flagged/blocked messages."""
    print("\n" + "="*60)
    print("TEST 5: Admin moderation query")
    print("="*60)
    
    # Query flagged messages
    response = requests.get(
        f"{BASE_URL}/api/admin/moderation/flagged",
        headers={"Authorization": f"Bearer {ACCESS_TOKEN}"}
    )
    
    print(f"Response status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        items = data.get("items", [])
        print(f"✅ Query successful: found {len(items)} flagged messages")
        
        for item in items[:3]:  # Show first 3
            print(f"   • Message {item.get('id')}")
            print(f"     Content: {item.get('content', '')[:50]}...")
            print(f"     Status: {item.get('status')}")
            print(f"     Severity: {item.get('message_metadata', {}).get('moderation', {}).get('severity')}")
        
        return len(items) > 0
    else:
        print(f"❌ Query failed: {response.text}")
        return False


def cleanup_conversation(conversation_id):
    """Delete test conversation."""
    print("\n" + "="*60)
    print("Cleanup")
    print("="*60)
    
    response = input(f"Delete test conversation {conversation_id}? (y/N): ")
    
    if response.lower() == 'y':
        resp = requests.delete(
            f"{BASE_URL}/api/conversations/{conversation_id}",
            headers={"Authorization": f"Bearer {ACCESS_TOKEN}"}
        )
        
        if resp.status_code == 204:
            print("✓ Test conversation deleted")
        else:
            print(f"⚠️  Failed to delete conversation: {resp.status_code}")
    else:
        print(f"✓ Keeping test conversation: {conversation_id}")


def main():
    """Run end-to-end moderation tests."""
    print("\n" + "="*60)
    print("END-TO-END MODERATION API TEST")
    print("="*60)
    
    # Login
    if not login():
        print("\n❌ Cannot proceed without authentication")
        print("   Please update credentials in the script")
        return
    
    # Create test conversation
    conversation_id = create_conversation()
    if not conversation_id:
        print("\n❌ Cannot proceed without conversation")
        return
    
    try:
        # Run tests
        results = []
        
        # Test 1: Blocked message
        results.append(("Blocked message", test_blocked_message(conversation_id)))
        
        # Test 2: Flagged message (MEDIUM)
        success, msg_id = test_flagged_message(conversation_id)
        results.append(("Flagged message (MEDIUM)", success))
        
        # Test 3: Flagged message (EMERGENCY)
        success, msg_id = test_emergency_message(conversation_id)
        results.append(("Flagged message (EMERGENCY)", success))
        
        # Test 4: Normal message
        success, msg_id = test_normal_message(conversation_id)
        results.append(("Normal message", success))
        
        # Test 5: Admin query
        results.append(("Admin query", test_admin_moderation_query()))
        
        # Summary
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        
        passed = sum(1 for _, r in results if r)
        total = len(results)
        
        for name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status}: {name}")
        
        print(f"\nResults: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 ALL TESTS PASSED!")
        else:
            print("⚠️  Some tests failed")
        
    finally:
        # Cleanup
        cleanup_conversation(conversation_id)


if __name__ == "__main__":
    main()
