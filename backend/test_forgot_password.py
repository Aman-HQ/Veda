"""
Quick test script for the forgot password endpoint.
Run this after starting the server to verify the endpoint works.
"""
import requests

BASE_URL = "http://localhost:8000"

def test_forgot_password():
    """Test the /forgot-password endpoint"""
    
    print("=" * 60)
    print("Testing /api/auth/forgot-password endpoint")
    print("=" * 60)
    
    # Test with a valid email format
    test_email = "test@example.com"
    
    print(f"\n1. Testing with email: {test_email}")
    response = requests.post(
        f"{BASE_URL}/api/auth/forgot-password",
        json={"email": test_email}
    )
    
    print(f"   Status Code: {response.status_code}")
    print(f"   Response: {response.json()}")
    
    if response.status_code == 200:
        print("   ✅ Endpoint is working!")
    else:
        print("   ❌ Unexpected status code")
    
    # Test with invalid email format
    print(f"\n2. Testing with invalid email format")
    response = requests.post(
        f"{BASE_URL}/api/auth/forgot-password",
        json={"email": "not-an-email"}
    )
    
    print(f"   Status Code: {response.status_code}")
    print(f"   Response: {response.json()}")
    
    if response.status_code == 422:
        print("   ✅ Validation working correctly!")
    else:
        print("   ❌ Validation not working as expected")
    
    print("\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        test_forgot_password()
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to server.")
        print("   Make sure the FastAPI server is running on http://localhost:8000")
    except Exception as e:
        print(f"❌ Error: {e}")
