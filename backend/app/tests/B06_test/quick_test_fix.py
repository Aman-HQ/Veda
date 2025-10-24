"""
Quick test for the conversation with messages endpoint fix.
"""
import asyncio
import httpx
import sys

async def test_fix():
    """Test the fixed endpoint."""
    print("Testing the conversation with messages endpoint fix...")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # 1. Login
            login_data = {
                "email": "test-crud@example.com",
                "password": "testpassword123"
            }
            
            login_resp = await client.post(
                "http://localhost:8000/api/auth/login",
                json=login_data
            )
            
            if login_resp.status_code != 200:
                print(f"❌ Login failed: {login_resp.status_code} - {login_resp.text}")
                return False
            
            token = login_resp.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            print("✅ Login successful")
            
            # 2. Create conversation
            conv_data = {"title": "Test Conversation for Fix"}
            conv_resp = await client.post(
                "http://localhost:8000/api/conversations/",
                json=conv_data,
                headers=headers
            )
            
            if conv_resp.status_code != 201:
                print(f"❌ Conversation creation failed: {conv_resp.status_code} - {conv_resp.text}")
                return False
            
            conv_id = conv_resp.json()["id"]
            print(f"✅ Conversation created: {conv_id}")
            
            # 3. Add a message
            msg_data = {
                "content": "Test message for the fix",
                "type": "text"
            }
            msg_resp = await client.post(
                f"http://localhost:8000/api/{conv_id}/messages",
                json=msg_data,
                headers=headers
            )
            
            if msg_resp.status_code != 201:
                print(f"❌ Message creation failed: {msg_resp.status_code} - {msg_resp.text}")
                return False
            
            print("✅ Message created")
            
            # 4. Test the problematic endpoint
            with_messages_resp = await client.get(
                f"http://localhost:8000/api/conversations/{conv_id}/with-messages?limit=10",
                headers=headers
            )
            
            # 5. Cleanup (do this before checking result)
            try:
                await client.delete(f"http://localhost:8000/api/conversations/{conv_id}", headers=headers)
                print("✅ Cleanup completed")
            except Exception:
                pass  # Best effort cleanup
            
            if with_messages_resp.status_code == 200:
                data = with_messages_resp.json()
                print("✅ Conversation with messages endpoint works!")
                print(f"   Conversation title: {data.get('title')}")
                print(f"   Messages count: {len(data.get('messages', []))}")
                if data.get("messages"):
                    print(f"   First message: {data['messages'][0].get('content', '')[:50]}...")
                
                return True
            else:
                print(f"❌ Conversation with messages failed: {with_messages_resp.status_code}")
                print(f"   Response: {with_messages_resp.text}")
                return False
                
        except httpx.ConnectError:
            print("❌ Could not connect to server. Make sure backend is running on http://localhost:8000")
            return False
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            return False

if __name__ == "__main__":
    result = asyncio.run(test_fix())
    if result:
        print("\n🎉 Fix verified! The conversation with messages endpoint is working correctly.")
        sys.exit(0)
    else:
        print("\n💥 Fix failed! The endpoint still has issues.")
        sys.exit(1)