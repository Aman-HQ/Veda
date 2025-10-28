"""
Test script for authentication endpoints.
This is a temporary test file for B04 validation.
"""
import asyncio
import httpx
import json
from typing import Dict, Any

BASE_URL = "http://localhost:8000"


async def test_auth_endpoints():
    """Test authentication endpoints."""
    print("=== B04 Authentication Endpoints Test ===\n")
    
    async with httpx.AsyncClient() as client:
        try:
            # Test 1: Health check
            print("1. Testing health check...")
            response = await client.get(f"{BASE_URL}/health")
            if response.status_code == 200:
                print("+ Health check passed")
                health_data = response.json()
                print(f"  Database status: {health_data.get('database', 'unknown')}")
            else:
                print(f"- Health check failed: {response.status_code}")
                return False
            
            # Test 2: User Registration
            print("\n2. Testing user registration...")
            register_data = {
                "email": "test@example.com",
                "password": "testpassword123",
                "name": "Test User"
            }
            
            response = await client.post(
                f"{BASE_URL}/api/auth/register",
                json=register_data
            )
            
            if response.status_code == 201:
                print("+ User registration successful")
                user_data = response.json()
                print(f"  User ID: {user_data.get('id')}")
                print(f"  Email: {user_data.get('email')}")
            elif response.status_code == 400:
                error_data = response.json()
                if "detail" in error_data and "already registered" in error_data["detail"].lower():
                    print("+ User already exists (expected for repeated tests)")
                else:
                    print(f"- User registration failed with unexpected error: {response.text}")
                    return False
            else:
                print(f"- User registration failed: {response.status_code}")
                print(f"  Error: {response.text}")
                return False
            
            # Test 3: User Login
            print("\n3. Testing user login...")
            login_data = {
                "email": "test@example.com",
                "password": "testpassword123"
            }
            
            response = await client.post(
                f"{BASE_URL}/api/auth/login",
                json=login_data
            )
            
            if response.status_code == 200:
                print("+ User login successful")
                token_data = response.json()
                access_token = token_data.get("access_token")
                refresh_token = token_data.get("refresh_token")
                print(f"  Token type: {token_data.get('token_type')}")
                print(f"  Access token: {access_token[:20]}...")
                print(f"  Refresh token: {refresh_token[:20]}...")
            else:
                print(f"- User login failed: {response.status_code}")
                print(f"  Error: {response.text}")
                return False
            
            # Test 4: Get current user info
            print("\n4. Testing get current user...")
            headers = {"Authorization": f"Bearer {access_token}"}
            
            response = await client.get(
                f"{BASE_URL}/api/auth/me",
                headers=headers
            )
            
            if response.status_code == 200:
                print("+ Get current user successful")
                user_data = response.json()
                print(f"  User: {user_data.get('name')} ({user_data.get('email')})")
                print(f"  Role: {user_data.get('role')}")
            else:
                print(f"- Get current user failed: {response.status_code}")
                print(f"  Error: {response.text}")
                return False
            
            # Test 5: Token refresh
            print("\n5. Testing token refresh...")
            refresh_data = {"refresh_token": refresh_token}
            
            response = await client.post(
                f"{BASE_URL}/api/auth/refresh",
                json=refresh_data
            )
            
            if response.status_code == 200:
                print("+ Token refresh successful")
                new_token_data = response.json()
                new_access_token = new_token_data.get("access_token")
                print(f"  New access token: {new_access_token[:20]}...")
            else:
                print(f"- Token refresh failed: {response.status_code}")
                print(f"  Error: {response.text}")
                return False
            
            # Test 6: Invalid credentials
            print("\n6. Testing invalid credentials...")
            invalid_login = {
                "email": "test@example.com",
                "password": "wrongpassword"
            }
            
            response = await client.post(
                f"{BASE_URL}/api/auth/login",
                json=invalid_login
            )
            
            if response.status_code == 401:
                print("+ Invalid credentials properly rejected")
            else:
                print(f"- Invalid credentials test failed: {response.status_code}")
                return False
            
            # Test 7: Protected endpoint without token
            print("\n7. Testing protected endpoint without token...")
            response = await client.get(f"{BASE_URL}/api/auth/me")
            
            if response.status_code == 401:
                print("+ Protected endpoint properly secured")
            else:
                print(f"- Protected endpoint security failed: {response.status_code}")
                return False
            
            print("\n[SUCCESS] All authentication tests passed!")
            return True
            
        except httpx.ConnectError:
            print("[ERROR] Could not connect to server. Make sure the backend is running on http://localhost:8000")
            return False
        except Exception as e:
            print(f"[ERROR] Test failed with exception: {e}")
            return False


def test_schema_validation():
    """Test that authentication schemas work correctly."""
    print("\n=== Schema Validation Test ===\n")
    
    try:
        from app.schemas.auth import UserCreate, LoginRequest, Token
        
        # Test UserCreate schema
        user_data = {
            "email": "test@example.com",
            "password": "testpassword123",
            "name": "Test User"
        }
        user_schema = UserCreate(**user_data)
        print("+ UserCreate schema validation works")
        
        # Test LoginRequest schema
        login_data = {
            "email": "test@example.com",
            "password": "testpassword123"
        }
        login_schema = LoginRequest(**login_data)
        print("+ LoginRequest schema validation works")
        
        # Test Token schema
        token_data = {
            "access_token": "fake_access_token",
            "refresh_token": "fake_refresh_token",
            "token_type": "bearer"
        }
        token_schema = Token(**token_data)
        print("+ Token schema validation works")
        
        print("\n[SUCCESS] All schema validations passed!")
        return True
        
    except Exception as e:
        print(f"[ERROR] Schema validation failed: {e}")
        return False


async def main():
    """Run all tests."""
    print("Starting B04 Authentication Tests...\n")
    
    # Test schemas first (doesn't require server)
    schema_success = test_schema_validation()
    
    # Test endpoints (requires server)
    endpoint_success = await test_auth_endpoints()
    
    if schema_success and endpoint_success:
        print("\n🎉 All B04 tests passed! Authentication implementation is working correctly.")
    else:
        print("\n💥 Some tests failed. Please check the implementation.")
        return False
    
    return True


if __name__ == "__main__":
    asyncio.run(main())
