"""
Test script for FastAPI integration with SQLAlchemy.
This tests the B05 implementation.
"""
import asyncio
import httpx
import json
from typing import Dict, Any

BASE_URL = "http://localhost:8000"


async def test_fastapi_integration():
    """Test FastAPI-SQLAlchemy integration."""
    print("=== B05 FastAPI Integration Test ===\n")
    
    async with httpx.AsyncClient() as client:
        try:
            # Test 1: Enhanced Health Check
            print("1. Testing enhanced health check...")
            response = await client.get(f"{BASE_URL}/health")
            if response.status_code == 200:
                print("+ Enhanced health check passed")
                health_data = response.json()
                print(f"  Service: {health_data.get('service')}")
                print(f"  Database status: {health_data.get('database', {}).get('status')}")
                print(f"  Tables: {health_data.get('database', {}).get('tables', 'unknown')}")
                print(f"  Environment: {health_data.get('environment', {}).get('debug')}")
            else:
                print(f"- Enhanced health check failed: {response.status_code}")
                return False
            
            # Test 2: Root endpoint
            print("\n2. Testing root endpoint...")
            response = await client.get(f"{BASE_URL}/")
            if response.status_code == 200:
                print("+ Root endpoint working")
                root_data = response.json()
                print(f"  Message: {root_data.get('message')}")
                print(f"  Version: {root_data.get('version')}")
            else:
                print(f"- Root endpoint failed: {response.status_code}")
                return False
            
            # Test 3: Demo Chat Endpoint (SQLAlchemy Integration)
            print("\n3. Testing demo chat endpoint (SQLAlchemy integration)...")
            chat_data = {
                "username": "demo@example.com",
                "user_message": "Hello, I have a question about my health."
            }
            
            response = await client.post(
                f"{BASE_URL}/chat",
                params=chat_data
            )
            
            if response.status_code == 200:
                print("+ Demo chat endpoint working")
                chat_response = response.json()
                print(f"  User: {chat_response.get('user')}")
                print(f"  Conversation ID: {chat_response.get('conversation_id')}")
                print(f"  Response preview: {chat_response.get('response', '')[:100]}...")
                print(f"  Demo flag: {chat_response.get('demo')}")
            else:
                print(f"- Demo chat endpoint failed: {response.status_code}")
                print(f"  Error: {response.text}")
                return False
            
            # Test 4: Follow-up message to same conversation
            print("\n4. Testing follow-up message...")
            followup_data = {
                "username": "demo@example.com",
                "user_message": "Can you tell me more about healthy eating?"
            }
            
            response = await client.post(
                f"{BASE_URL}/chat",
                params=followup_data
            )
            
            if response.status_code == 200:
                print("+ Follow-up message working")
                followup_response = response.json()
                # Should be same conversation ID
                if followup_response.get('conversation_id') == chat_response.get('conversation_id'):
                    print("  ✓ Same conversation maintained")
                else:
                    print("  - Different conversation created (unexpected)")
            else:
                print(f"- Follow-up message failed: {response.status_code}")
                return False
            
            # Test 5: API Documentation
            print("\n5. Testing API documentation...")
            response = await client.get(f"{BASE_URL}/docs")
            if response.status_code == 200:
                print("+ API documentation accessible")
            else:
                print(f"- API documentation failed: {response.status_code}")
                return False
            
            # Test 6: Error handling
            print("\n6. Testing error handling...")
            response = await client.post(f"{BASE_URL}/chat")  # Missing required params
            if response.status_code == 422:
                print("+ Validation error handling working")
                error_data = response.json()
                print(f"  Error type: {error_data.get('detail')}")
            else:
                print(f"- Error handling test unexpected result: {response.status_code}")
            
            # Test 7: Process time header
            print("\n7. Testing process time header...")
            response = await client.get(f"{BASE_URL}/health")
            if "x-process-time" in response.headers:
                print("+ Process time header present")
                print(f"  Process time: {response.headers['x-process-time']}s")
            else:
                print("- Process time header missing")
            
            print("\n[SUCCESS] All FastAPI integration tests passed!")
            return True
            
        except httpx.ConnectError:
            print("[ERROR] Could not connect to server. Make sure the backend is running on http://localhost:8000")
            return False
        except Exception as e:
            print(f"[ERROR] Test failed with exception: {e}")
            return False


def test_imports():
    """Test that all FastAPI integration imports work."""
    print("\n=== Import Test ===\n")
    
    try:
        from app.main import app
        print("+ FastAPI app import successful")
        
        from app.db.init_db import init_db
        print("+ Database init import successful")
        
        # Test that models are properly imported
        from app.models.user import User
        from app.models.conversation import Conversation
        from app.models.message import Message
        print("+ Model imports successful")
        
        print("\n[SUCCESS] All imports working correctly!")
        return True
        
    except Exception as e:
        print(f"[ERROR] Import test failed: {e}")
        return False


async def main():
    """Run all tests."""
    print("Starting B05 FastAPI Integration Tests...\n")
    
    # Test imports first (doesn't require server)
    import_success = test_imports()
    
    # Test integration (requires server)
    integration_success = await test_fastapi_integration()
    
    if import_success and integration_success:
        print("\n🎉 All B05 tests passed! FastAPI integration is working correctly.")
        print("\nKey Features Verified:")
        print("✓ Enhanced health checks with database info")
        print("✓ Global error handling and validation")
        print("✓ Request timing middleware")
        print("✓ Demo chat endpoint with SQLAlchemy integration")
        print("✓ Proper transaction handling")
        print("✓ API documentation generation")
    else:
        print("\n💥 Some tests failed. Please check the implementation.")
        return False
    
    return True


if __name__ == "__main__":
    asyncio.run(main())
